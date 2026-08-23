""" Author: Charlie

运行时 JSON 逐接口对比：hei-boot vs hei-fastapi。

对 Boot OpenAPI 中的 GET 接口（跳过副作用/上传/OAuth 等），用相同 token、路径、query
分别请求两栈，对比 HTTP status、业务 code 与归一化后的 data JSON。

用法::

    python scripts/e2e/boot_fastapi_runtime_diff.py \\
        --boot http://127.0.0.1:8000 \\
        --fastapi http://127.0.0.1:8100 \\
        --redis redis://:123456@127.0.0.1:6379/3 \\
        --out scripts/e2e/reports/boot_fastapi_runtime_diff.json
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from redis import Redis

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.e2e.assert_util import parse_loose, truncate  # noqa: E402
from scripts.e2e.client import do_raw, get_json  # noqa: E402
from scripts.e2e.boot_contract_full_diff import fetch_boot_openapi  # noqa: E402
from scripts.e2e.contract import iter_operations  # noqa: E402
from scripts.e2e.contract_sweep import _enrich_get_query, _skip_contract  # noqa: E402
from scripts.e2e.sweep import materialize_path, pick_token  # noqa: E402
from app.core.security.password import hash_password  # noqa: E402

IGNORE_JSON_KEYS = frozenset(
    {
        "trans_map",
        "transMap",
        "latest_login_time",
        "last_login_time",
    }
)

BOOT_PAGE_EXTRA = frozenset(
    {
        "count_id",
        "max_limit",
        "optimize_count_sql",
        "optimize_join_of_count_sql",
        "orders",
        "search_count",
    }
)

# 扫接口过程中会写入或随时间变化的 GET，默认跳过以免误报。
DYNAMIC_PATH_SUBSTRINGS = (
    "/sys/audit/",
    "/auth/sessions/",
    "/workspace/overview",
    "/permission-registry",
)

DYNAMIC_EXACT_PATHS = frozenset(
    {
        "/",
        "/api/v1/admin/me",
        "/api/v1/portal/me",
    }
)

# 预签名 URL 的 query 每次请求不同，对比时只保留 path。
PRESIGN_URL_KEYS = frozenset({"url", "avatar", "cover_url", "icon_url", "submitter_avatar"})


def classify_dynamic_path(path: str) -> str | None:
    """若路径在扫接口时必然波动，返回跳过原因。"""
    normalized = path if path.startswith("/") else f"/{path}"
    if normalized in DYNAMIC_EXACT_PATHS:
        return f"dynamic:{normalized}"
    for sub in DYNAMIC_PATH_SUBSTRINGS:
        if sub in normalized:
            return f"dynamic:{sub}"
    return None


def normalize_storage_url(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        q = url.find("?")
        return url[:q] if q >= 0 else url
    return url


def audit_table_snapshot(db_url: str) -> dict[str, Any]:
    """只读查询审计表行数与最大 id（用于 sweep 前后对照）。"""
    sync_url = re.sub(r"postgresql\+asyncpg://", "postgresql://", db_url)
    sync_url = re.sub(r"postgresql\+psycopg://", "postgresql://", sync_url)
    from sqlalchemy import create_engine, text

    engine = create_engine(sync_url)
    with engine.connect() as conn:
        audit = conn.execute(
            text(
                "SELECT COUNT(*)::bigint AS cnt, MAX(id) AS max_id "
                "FROM sys_operation_audit_log"
            )
        ).mappings().one()
        outbox = conn.execute(
            text("SELECT COUNT(*)::bigint AS cnt FROM sys_operation_audit_outbox")
        ).mappings().one()
    return {
        "sys_operation_audit_log": {
            "count": int(audit["cnt"]),
            "max_id": audit["max_id"],
        },
        "sys_operation_audit_outbox": {"count": int(outbox["cnt"])},
    }


def load_default_db_url() -> str | None:
    env_path = _ROOT / ".env"
    if not env_path.is_file():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DB__URL="):
            return line.split("=", 1)[1].strip()
    return None


def to_snake(name: str) -> str:
    if not name or "_" in name:
        return name
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _encrypt_password(public_key_b64: str, password: str) -> str:
    der = base64.b64decode(public_key_b64)
    public_key = serialization.load_der_public_key(der)
    ciphertext = public_key.encrypt(
        password.encode("utf-8"),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.b64encode(ciphertext).decode("ascii")


def login(
    rdb: Redis,
    base: str,
    prefix: str,
    account: str,
    password: str = "123456",
) -> str:
    cap = get_json(f"{base}{prefix}/captcha")
    captcha_id = (cap.get("data") or {}).get("captcha_id")
    if not captcha_id:
        raise RuntimeError(f"captcha missing: {cap}")
    rdb.setex(f"captcha:{captcha_id}", 300, hash_password("test"))
    pk = get_json(f"{base}{prefix}/password-key")
    data = pk.get("data") or {}
    key_id = data.get("key_id")
    public_key = data.get("public_key")
    if not key_id or not public_key:
        raise RuntimeError(f"password-key missing: {pk}")
    encrypted = _encrypt_password(public_key, password)
    status, raw, ar = do_raw(
        "POST",
        f"{base}{prefix}/login",
        "",
        json.dumps(
            {
                "account": account,
                "password": encrypted,
                "identity_type": "ACCOUNT",
                "remember_me": False,
                "password_key_id": key_id,
                "captcha_id": captcha_id,
                "captcha_value": "test",
            }
        ),
    )
    if status >= 400 or ar.code not in (0, 200):
        raise RuntimeError(
            f"login failed status={status} code={ar.code} "
            f"body={truncate(raw.decode('utf-8', 'replace'), 240)}"
        )
    token = (ar.data or {}).get("token") if isinstance(ar.data, dict) else None
    if not token:
        raise RuntimeError("login ok but no token")
    return str(token)


def normalize_json(value: Any, key: str | None = None) -> Any:
    """递归归一化：snake_case 键、剔除展示字段与 MP 分页扩展。"""
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            sk = to_snake(str(k))
            if sk in IGNORE_JSON_KEYS or sk in BOOT_PAGE_EXTRA:
                continue
            if v is None:
                continue
            out[sk] = normalize_json(v, sk)
        return out
    if isinstance(value, list):
        return [normalize_json(item) for item in value]
    if isinstance(value, str) and key in PRESIGN_URL_KEYS:
        return normalize_storage_url(value)
    if isinstance(value, float) and value == int(value):
        return int(value)
    return value


def deep_diff(boot: Any, fast: Any, path: str = "") -> list[str]:
    """返回人类可读差异路径列表。"""
    diffs: list[str] = []
    if type(boot) != type(fast):
        diffs.append(f"{path}: type boot={type(boot).__name__} fast={type(fast).__name__}")
        return diffs
    if isinstance(boot, dict):
        boot_keys = set(boot.keys())
        fast_keys = set(fast.keys())
        for k in sorted(boot_keys - fast_keys):
            diffs.append(f"{path}.{k}: missing in fastapi")
        for k in sorted(fast_keys - boot_keys):
            diffs.append(f"{path}.{k}: extra in fastapi")
        for k in sorted(boot_keys & fast_keys):
            child = f"{path}.{k}" if path else k
            diffs.extend(deep_diff(boot[k], fast[k], child))
        return diffs
    if isinstance(boot, list):
        if len(boot) != len(fast):
            diffs.append(f"{path}: list len boot={len(boot)} fast={len(fast)}")
        for i, (a, b) in enumerate(zip(boot, fast, strict=False)):
            diffs.extend(deep_diff(a, b, f"{path}[{i}]"))
        return diffs
    if boot != fast:
        diffs.append(f"{path}: boot={truncate(json.dumps(boot, ensure_ascii=False), 80)} "
                     f"fast={truncate(json.dumps(fast, ensure_ascii=False), 80)}")
    return diffs


@dataclass
class RuntimeDiff:
    method: str
    path: str
    url: str
    skip_reason: str | None = None
    boot_status: int | None = None
    fast_status: int | None = None
    boot_code: int | None = None
    fast_code: int | None = None
    status_mismatch: bool = False
    code_mismatch: bool = False
    data_diffs: list[str] = field(default_factory=list)
    error: str | None = None


def compare_get(
    boot_root: str,
    fast_root: str,
    admin_tok_boot: str,
    portal_tok_boot: str,
    admin_tok_fast: str,
    portal_tok_fast: str,
    method: str,
    path: str,
    op: dict[str, Any],
) -> RuntimeDiff:
    path_m = materialize_path(path)
    tok_boot = pick_token(path_m, admin_tok_boot, portal_tok_boot)
    tok_fast = pick_token(path_m, admin_tok_fast, portal_tok_fast)
    q = _enrich_get_query(path_m, op)
    rel = path_m + (f"?{q}" if q else "")
    url_boot = boot_root + rel
    url_fast = fast_root + rel
    rd = RuntimeDiff(method=method, path=path, url=rel)

    try:
        st_b, raw_b, ar_b = do_raw(method, url_boot, tok_boot, "")
        st_f, raw_f, ar_f = do_raw(method, url_fast, tok_fast, "")
        rd.boot_status, rd.fast_status = st_b, st_f
        rd.boot_code, rd.fast_code = ar_b.code, ar_f.code
        rd.status_mismatch = st_b != st_f
        rd.code_mismatch = ar_b.code != ar_f.code

        norm_b = normalize_json(ar_b.data)
        norm_f = normalize_json(ar_f.data)
        if path.endswith("/sys/config/list"):
            if isinstance(norm_b, list):
                norm_b = sorted(norm_b, key=lambda r: r.get("config_key", ""))
            if isinstance(norm_f, list):
                norm_f = sorted(norm_f, key=lambda r: r.get("config_key", ""))
        rd.data_diffs = deep_diff(norm_b, norm_f, "data")
    except Exception as exc:  # noqa: BLE001
        rd.error = str(exc)
    return rd


def path_matches_module(path: str, module: str) -> bool:
    if not module:
        return True
    token = module.strip().lower().replace("_", "-")
    return token in path.lower()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Runtime JSON diff boot vs fastapi")
    parser.add_argument("--boot", default="http://127.0.0.1:8000")
    parser.add_argument("--fastapi", default="http://127.0.0.1:8100")
    parser.add_argument("--module", default="", help="filter paths containing token (e.g. sys/audit)")
    parser.add_argument("--redis", default="redis://:123456@127.0.0.1:6379/3", help="fastapi redis")
    parser.add_argument("--redis-boot", default="redis://:123456@127.0.0.1:6379/0", help="boot redis")
    parser.add_argument("--admin-account", default="superadmin")
    parser.add_argument("--portal-account", default="user")
    parser.add_argument("--password", default="123456")
    parser.add_argument("--out", default="scripts/e2e/reports/boot_fastapi_runtime_diff.json")
    parser.add_argument(
        "--skip-dynamic",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="跳过审计/会话/me 等动态 GET（默认开启）",
    )
    parser.add_argument(
        "--audit-snapshot-db",
        default=None,
        help="只读 PostgreSQL URL，记录 sweep 前后审计表快照（默认读 .env DB__URL）",
    )
    args = parser.parse_args(argv)

    if os.environ.get("E2E_DISABLE_RATE_LIMIT") != "1":
        print(
            "NOTE: e2e client sends X-E2E-Disable-Rate-Limit:1; "
            "or start hei-fastapi with E2E_DISABLE_RATE_LIMIT=1",
            file=sys.stderr,
        )

    boot_root = args.boot.rstrip("/")
    fast_root = args.fastapi.rstrip("/")
    boot_api = boot_root + "/api"
    fast_api = fast_root + "/api"

    rdb_fast = Redis.from_url(args.redis, decode_responses=False)
    rdb_boot = Redis.from_url(args.redis_boot, decode_responses=False)
    rdb_fast.ping()
    rdb_boot.ping()

    audit_snapshots: dict[str, Any] = {}
    snapshot_db = args.audit_snapshot_db or load_default_db_url()
    if snapshot_db:
        try:
            audit_snapshots["before_sweep"] = audit_table_snapshot(snapshot_db)
            print("Audit snapshot (before sweep):", audit_snapshots["before_sweep"])
        except Exception as exc:  # noqa: BLE001
            audit_snapshots["before_sweep_error"] = str(exc)
            print("Audit snapshot failed:", exc)

    print("Logging in boot...")
    admin_boot = login(rdb_boot, boot_api, "/v1/admin", args.admin_account, args.password)
    portal_boot = login(rdb_boot, boot_api, "/v1/portal", args.portal_account, args.password)
    print("Logging in fastapi...")
    admin_fast = login(rdb_fast, fast_api, "/v1/admin", args.admin_account, args.password)
    portal_fast = login(rdb_fast, fast_api, "/v1/portal", args.portal_account, args.password)

    openapi = fetch_boot_openapi(args.boot)
    ops = iter_operations(openapi)

    results: list[RuntimeDiff] = []
    skipped = 0
    dynamic_skipped = 0
    compared = 0
    mismatches = 0

    for item in ops:
        method = item["method"]
        path = item["path"]
        op = item["operation"]
        if method != "GET":
            continue
        skip = _skip_contract(method, path)
        if skip:
            results.append(RuntimeDiff(method=method, path=path, url=path, skip_reason=skip))
            skipped += 1
            continue
        if "easyTrans" in path:
            results.append(RuntimeDiff(method=method, path=path, url=path, skip_reason="easyTrans"))
            skipped += 1
            continue
        if not path_matches_module(path, args.module):
            skipped += 1
            continue
        if args.skip_dynamic:
            dyn = classify_dynamic_path(path)
            if dyn:
                results.append(
                    RuntimeDiff(method=method, path=path, url=path, skip_reason=dyn)
                )
                skipped += 1
                dynamic_skipped += 1
                continue

        rd = compare_get(
            boot_root,
            fast_root,
            admin_boot,
            portal_boot,
            admin_fast,
            portal_fast,
            method,
            path,
            op,
        )
        results.append(rd)
        compared += 1
        bad = (
            rd.error
            or rd.status_mismatch
            or rd.code_mismatch
            or rd.data_diffs
        )
        if bad:
            mismatches += 1
            print(
                "DIFF",
                method,
                path,
                rd.error or f"status={rd.status_mismatch} code={rd.code_mismatch} "
                f"data={len(rd.data_diffs)}",
            )
        else:
            print("OK", method, path)

    if snapshot_db and "before_sweep" in audit_snapshots:
        try:
            audit_snapshots["after_sweep"] = audit_table_snapshot(snapshot_db)
            before = audit_snapshots["before_sweep"]["sys_operation_audit_log"]["count"]
            after = audit_snapshots["after_sweep"]["sys_operation_audit_log"]["count"]
            audit_snapshots["audit_log_delta"] = after - before
            print("Audit snapshot (after sweep):", audit_snapshots["after_sweep"])
            print("Audit log delta:", audit_snapshots["audit_log_delta"])
        except Exception as exc:  # noqa: BLE001
            audit_snapshots["after_sweep_error"] = str(exc)

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "boot_base": boot_root,
        "fastapi_base": fast_root,
        "skip_dynamic": args.skip_dynamic,
        "module_filter": args.module or None,
        "audit_snapshots": audit_snapshots,
        "summary": {
            "ops_in_openapi": len(ops),
            "get_compared": compared,
            "get_skipped": skipped,
            "dynamic_skipped": dynamic_skipped,
            "mismatch_count": mismatches,
            "match_count": compared - mismatches,
        },
        "mismatches": [
            {
                "method": r.method,
                "path": r.path,
                "url": r.url,
                "boot_status": r.boot_status,
                "fast_status": r.fast_status,
                "boot_code": r.boot_code,
                "fast_code": r.fast_code,
                "status_mismatch": r.status_mismatch,
                "code_mismatch": r.code_mismatch,
                "data_diffs": r.data_diffs[:50],
                "data_diff_count": len(r.data_diffs),
                "error": r.error,
            }
            for r in results
            if r.skip_reason is None
            and (
                r.error
                or r.status_mismatch
                or r.code_mismatch
                or r.data_diffs
            )
        ],
        "skipped": [
            {"method": r.method, "path": r.path, "reason": r.skip_reason}
            for r in results
            if r.skip_reason
        ],
    }

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = _ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== RUNTIME JSON DIFF ===")
    print(f"Compared GET: {compared}, skipped: {skipped}")
    print(f"Match: {report['summary']['match_count']}, mismatch: {mismatches}")
    print(f"Report: {out_path}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
