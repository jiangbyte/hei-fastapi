""" Author: Charlie

hei-gin 风格双库 API e2e：Redis 植入验证码 → 登录 → hard + OpenAPI 契约扫 + CRUD。

Usage::

    python -m scripts.e2e --base http://127.0.0.1:18080 --redis redis://:123456@127.0.0.1:6379/15 --out scripts/e2e/report-mysql.json
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from redis import Redis

# Allow `python -m scripts.e2e` from repo root.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.core.security.password import hash_password  # noqa: E402

from .assert_util import CaseBucket, CaseResult, truncate  # noqa: E402
from .client import do_raw, get_json  # noqa: E402
from .contract_sweep import run_contract_sweep  # noqa: E402
from .crud import run_crud_cases  # noqa: E402
from .hard import hard_checks  # noqa: E402
from .sweep import is_sql_suspect, pick_token  # noqa: E402


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


def login(rdb: Redis, base: str, prefix: str, account: str, password: str = "123456") -> str:
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
        raise RuntimeError(f"login failed status={status} code={ar.code} body={truncate(raw.decode('utf-8','replace'), 240)}")
    token = (ar.data or {}).get("token") if isinstance(ar.data, dict) else None
    if not token:
        raise RuntimeError("login ok but no token")
    return str(token)


def run_hard(
    base: str,
    admin_tok: str,
    portal_tok: str,
    results: list[dict[str, Any]],
) -> tuple[int, int]:
    hard_pass = 0
    hard_fail = 0
    for hc in hard_checks():
        tok = pick_token(hc.path, admin_tok, portal_tok)
        url = base + hc.path
        entry: dict[str, Any] = {
            "method": hc.method,
            "path": hc.path,
            "url": url,
            "hard_check": hc.name,
        }
        try:
            status, raw, ar = do_raw(hc.method, url, tok, hc.body)
            body = truncate(raw.decode("utf-8", "replace"), 400)
            entry.update(
                {
                    "status": status,
                    "biz_code": ar.code,
                    "body": body,
                    "is_5xx": status >= 500 or ar.code >= 500,
                    "sql_suspect": is_sql_suspect(body),
                }
            )
            ok = not entry["is_5xx"] and not entry["sql_suspect"] and 200 <= status < 500
            # hard checks expect success business for dialect probes
            if hc.name.startswith("health_") or hc.name in {"admin_me", "dashboard_overview"}:
                ok = ok and ar.code in (0, 200) and status == 200
            elif status == 200 and ar.code in (0, 200):
                ok = ok and True
            elif status in (401, 403) and not entry["sql_suspect"]:
                # permission miss is not dialect failure for optional portal paths without data
                ok = True
            entry["hard_ok"] = ok
            if ok:
                hard_pass += 1
                print("HARD PASS", hc.name)
            else:
                hard_fail += 1
                print("HARD FAIL", hc.name, status, ar.code, body[:120])
        except Exception as exc:  # noqa: BLE001
            entry["error"] = str(exc)
            entry["hard_ok"] = False
            entry["is_5xx"] = True
            hard_fail += 1
            print("HARD FAIL", hc.name, exc)
        results.append(entry)
    return hard_pass, hard_fail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="hei-fastapi dialect e2e (hei-gin style)")
    parser.add_argument("--base", default="http://127.0.0.1:18080")
    parser.add_argument("--redis", default="redis://:123456@127.0.0.1:6379/15")
    parser.add_argument("--out", default="scripts/e2e/report.json")
    args = parser.parse_args(argv)

    rdb = Redis.from_url(args.redis, decode_responses=False)
    try:
        rdb.ping()
    except Exception as exc:  # noqa: BLE001
        print("redis:", exc)
        return 1

    admin_ok = False
    portal_ok = False
    admin_tok = ""
    portal_tok = ""
    try:
        admin_tok = login(rdb, args.base, "/api/v1/admin", "superadmin")
        admin_ok = True
        print("admin login OK, token_len=", len(admin_tok))
    except Exception as exc:  # noqa: BLE001
        print("admin login FAILED:", exc)
    try:
        portal_tok = login(rdb, args.base, "/api/v1/portal", "user")
        portal_ok = True
        print("portal login OK, token_len=", len(portal_tok))
    except Exception as exc:  # noqa: BLE001
        print("portal login FAILED:", exc)

    results: list[dict[str, Any]] = []
    out_bucket = CaseBucket()
    in_bucket = CaseBucket()
    crud_bucket = CaseBucket()
    skipped: list[CaseResult] = []

    hard_pass, hard_fail = run_hard(args.base, admin_tok, portal_tok, results)

    if admin_ok:
        print("--- CRUD ---")
        run_crud_cases(args.base, admin_tok, crud_bucket)

    contract_stats: dict[str, int] = {}
    print("--- CONTRACT (in/out) ---")
    try:
        contract_stats = run_contract_sweep(
            args.base,
            admin_tok,
            portal_tok,
            out_bucket,
            in_bucket,
            skipped,
            results,
        )
        print(
            "contract:",
            f"ops={contract_stats.get('ops_total')} "
            f"out={contract_stats.get('out_pass')}/{contract_stats.get('out_pass', 0) + contract_stats.get('out_fail', 0)} "
            f"in={contract_stats.get('in_pass')}/{contract_stats.get('in_pass', 0) + contract_stats.get('in_fail', 0)} "
            f"skipped={contract_stats.get('skipped')}",
        )
    except Exception as exc:  # noqa: BLE001
        print("contract FAILED:", exc)
        contract_stats = {"error": 1}  # type: ignore[dict-item]

    fail_5xx_list = [r for r in results if r.get("is_5xx")]
    hard_fails = [r for r in results if r.get("hard_check") and r.get("hard_ok") is False]
    sql_suspects = [r for r in results if r.get("sql_suspect")]
    schema_fails = [r for r in results if r.get("schema_error")]

    report = {
        "base_url": args.base,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "admin_login_ok": admin_ok,
        "portal_login_ok": portal_ok,
        "contract": contract_stats,
        "out_cases": out_bucket.to_dict(),
        "in_cases": in_bucket.to_dict(),
        "crud_cases": crud_bucket.to_dict(),
        "skipped": [s.to_dict() for s in skipped],
        "total": len(results),
        "fail_5xx": len(fail_5xx_list),
        "hard_pass": hard_pass,
        "hard_fail": hard_fail,
        "results": results,
        "fail_5xx_list": fail_5xx_list,
        "hard_fails": hard_fails,
        "sql_suspects": sql_suspects,
        "schema_fails": schema_fails,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"\n=== SUMMARY ===\nadmin={admin_ok} portal={portal_ok} "
        f"out={out_bucket.pass_}/{out_bucket.total} in={in_bucket.pass_}/{in_bucket.total} "
        f"crud={crud_bucket.pass_}/{crud_bucket.total} "
        f"skipped={len(skipped)} hard={hard_pass}/{hard_pass + hard_fail} "
        f"fail5xx={len(fail_5xx_list)} sql_suspect={len(sql_suspects)} schema={len(schema_fails)}\n"
        f"out={out_path}"
    )
    fail = (
        not admin_ok
        or not portal_ok
        or hard_fail > 0
        or len(fail_5xx_list) > 0
        or len(sql_suspects) > 0
        or len(crud_bucket.fail) > 0
        or len(out_bucket.fail) > 0
        or len(in_bucket.fail) > 0
        or bool(contract_stats.get("error"))
    )
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
