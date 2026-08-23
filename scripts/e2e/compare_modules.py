#!/usr/bin/env python3
"""Module-by-module boot vs fastapi response shape comparison."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from typing import Any

import bcrypt
import redis
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

BOOT = "http://127.0.0.1:8000"
FASTAPI = "http://127.0.0.1:8100"

MODULE_ENDPOINTS: dict[str, list[tuple[str, str]]] = {
    "auth": [
        ("GET", "/api/v1/admin/public/auth-options"),
        ("GET", "/api/v1/portal/public/auth-options"),
        ("GET", "/api/v1/public/site-footer"),
    ],
    "workspace": [
        ("GET", "/api/v1/admin/workspace/overview"),
        ("GET", "/api/v1/admin/workspace/shortcuts"),
    ],
    "profile": [
        ("GET", "/api/v1/admin/me"),
        ("GET", "/api/v1/portal/me"),
        ("GET", "/api/v1/admin/profile/org-info"),
    ],
    "identity": [
        ("GET", "/api/v1/admin/profile/identity/status"),
        ("GET", "/api/v1/portal/profile/identity/status"),
    ],
    "iam/account": [
        ("GET", "/api/v1/admin/sys/accounts/page?current=1&size=2"),
        ("GET", "/api/v1/admin/sys/accounts/detail?id=1"),
    ],
    "iam/role": [("GET", "/api/v1/admin/sys/roles/page?current=1&size=2")],
    "iam/dept": [
        ("GET", "/api/v1/admin/sys/depts/page?current=1&size=2"),
        ("GET", "/api/v1/admin/sys/depts/tree"),
    ],
    "iam/group": [("GET", "/api/v1/admin/sys/groups/page?current=1&size=2")],
    "iam/position": [("GET", "/api/v1/admin/sys/positions/page?current=1&size=2")],
    "iam/resource": [
        ("GET", "/api/v1/admin/sys/resources/tree"),
        ("GET", "/api/v1/admin/sys/resources/current"),
        ("GET", "/api/v1/portal/sys/resources/current"),
    ],
    "iam/client": [
        ("GET", "/api/v1/admin/sys/client-modules/page?current=1&size=2"),
        ("GET", "/api/v1/admin/sys/client-resources/tree"),
    ],
    "iam/relation": [("GET", "/api/v1/admin/permission-registry")],
    "sys/audit": [
        ("GET", "/api/v1/admin/sys/audit/page?current=1&size=2"),
        ("GET", "/api/v1/admin/sys/audit/my-page?current=1&size=2"),
    ],
    "sys/banner": [
        ("GET", "/api/v1/admin/sys/banners/page?current=1&size=2"),
        ("GET", "/api/v1/portal/sys/banners/list"),
    ],
    "sys/codegen": [
        ("GET", "/api/v1/admin/sys/codegen/page?current=1&size=2"),
        ("GET", "/api/v1/admin/sys/codegen/tables"),
    ],
    "sys/config": [
        ("GET", "/api/v1/admin/sys/config/page?current=1&size=2"),
        ("GET", "/api/v1/admin/sys/config/list"),
    ],
    "sys/dict": [
        ("GET", "/api/v1/admin/sys/dicts/page?current=1&size=2"),
        ("GET", "/api/v1/portal/sys/dicts/tree"),
    ],
    "sys/feedback": [("GET", "/api/v1/admin/sys/feedbacks/page?current=1&size=2")],
    "sys/file": [("GET", "/api/v1/admin/sys/file/page?current=1&size=2")],
    "sys/job": [
        ("GET", "/api/v1/admin/sys/jobs/page?current=1&size=2"),
        ("GET", "/api/v1/admin/sys/job-logs/page?current=1&size=2"),
    ],
    "sys/notice": [
        ("GET", "/api/v1/admin/sys/notices/page?current=1&size=2"),
        ("GET", "/api/v1/admin/sys/notices/my-page?current=1&size=2"),
    ],
    "sys/weak_password": [("GET", "/api/v1/admin/sys/weak-password/page?current=1&size=2")],
    "biz/activity": [("GET", "/api/v1/admin/biz/cg-test-activity/page?current=1&size=2")],
    "biz/catalog": [("GET", "/api/v1/admin/biz/cg-test-catalog/page?current=1&size=2")],
    "biz/order": [("GET", "/api/v1/admin/biz/cg-test-order/page?current=1&size=2")],
    "biz/knowledge": [("GET", "/api/v1/admin/biz/cg-test-knowledge-category/page?current=1&size=2")],
}

SKIP_KEYS = {
    "created_at",
    "updated_at",
    "bound_at",
    "verified_at",
    "last_login_at",
    "token",
    "password_hash",
    "trans_map",
    "children",
}

PORTAL_ONLY_PREFIXES = (
    "/api/v1/portal/",
)

E2E_HEADERS = {"Accept": "application/json", "X-E2E-Disable-Rate-Limit": "1"}


def should_skip_key(key: str) -> bool:
    if key in SKIP_KEYS:
        return True
    return key.endswith("_name") or key.endswith("_names")


def http_json(method: str, url: str, token: str = "", body: dict | None = None) -> tuple[int, Any]:
    headers = dict(E2E_HEADERS)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def plant_captcha(base: str, redis_db: int) -> str:
    _, cap = http_json("GET", f"{base}/api/v1/admin/captcha")
    cap_id = ((cap or {}).get("data") or {}).get("captcha_id", "")
    if not cap_id:
        raise RuntimeError(f"captcha id missing from {base}")
    rdb = redis.Redis(host="127.0.0.1", port=6379, password="123456", db=redis_db, decode_responses=True)
    hashed = bcrypt.hashpw(b"test", bcrypt.gensalt()).decode()
    rdb.set(f"captcha:{cap_id}", hashed, ex=300)
    return cap_id


def encrypt_password(pub_b64: str, password: str) -> str:
    der = base64.b64decode(pub_b64)
    pub = serialization.load_der_public_key(der)
    enc = pub.encrypt(
        password.encode(),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return base64.b64encode(enc).decode()


def login(base: str, redis_db: int) -> str:
    cap_id = plant_captcha(base, redis_db)
    _, pk = http_json("GET", f"{base}/api/v1/admin/password-key")
    key_id = (pk or {}).get("data", {}).get("key_id", "")
    pub = (pk or {}).get("data", {}).get("public_key", "")
    enc_pwd = encrypt_password(pub, "123456")
    _, resp = http_json(
        "POST",
        f"{base}/api/v1/admin/login",
        body={
            "account": "superadmin",
            "password": enc_pwd,
            "password_key_id": key_id,
            "captcha_id": cap_id,
            "captcha_value": "test",
            "remember_me": True,
            "login_mode": "PASSWORD",
        },
    )
    tok = ((resp or {}).get("data") or {}).get("token", "")
    if not tok:
        raise RuntimeError(f"login failed on {base}: {resp}")
    return tok


def keys_of(obj: Any) -> set[str]:
    return set(obj.keys()) if isinstance(obj, dict) else set()


def wire_kind(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "number"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "false"}:
            return "wire_bool"
        if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
            return "wire_number"
        return "str"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return type(value).__name__


def types_compatible(a: Any, b: Any) -> bool:
    if type(a) is type(b):
        return True
    ka, kb = wire_kind(a), wire_kind(b)
    if ka == kb:
        return True
    if ka == "null" or kb == "null":
        return a is None and b is None
    numeric = {"wire_number", "number", "str"}
    if ka in numeric and kb in numeric:
        return True
    boolish = {"wire_bool", "bool", "str"}
    if ka in boolish and kb in boolish:
        return True
    return False


def pick_matching_records(boot_records: list[Any], fast_records: list[Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    fast_by_id = {r.get("id"): r for r in fast_records if isinstance(r, dict) and r.get("id")}
    stable = [r for r in boot_records if isinstance(r, dict) and r.get("action") not in {"login", "logout"}]
    candidates = stable or [r for r in boot_records if isinstance(r, dict)]
    for br in candidates:
        rid = br.get("id")
        if rid and rid in fast_by_id:
            return br, fast_by_id[rid]
    if candidates and fast_records and isinstance(fast_records[0], dict):
        return candidates[0], fast_records[0]
    return None, None


def shape_diff(a: Any, b: Any, prefix: str = "") -> list[str]:
    diffs: list[str] = []
    if not types_compatible(a, b):
        return [f"{prefix}: type {wire_kind(a)} vs {wire_kind(b)}"]
    if isinstance(a, dict):
        only_a = sorted(k for k in keys_of(a) - keys_of(b) if not should_skip_key(k))
        only_b = sorted(k for k in keys_of(b) - keys_of(a) if not should_skip_key(k))
        if only_a:
            diffs.append(f"{prefix} only_boot={only_a[:10]}")
        if only_b:
            diffs.append(f"{prefix} only_fastapi={only_b[:10]}")
        for k in sorted(keys_of(a) & keys_of(b)):
            if should_skip_key(k):
                continue
            diffs.extend(shape_diff(a[k], b[k], f"{prefix}.{k}" if prefix else k)[:2])
    elif isinstance(a, list) and isinstance(b, list) and a and b:
        if isinstance(a[0], dict) and isinstance(b[0], dict):
            br, fr = pick_matching_records(a, b)
            if br and fr:
                diffs.extend(shape_diff(br, fr, f"{prefix}[id={br.get('id')}]")[:6])
            else:
                diffs.extend(shape_diff(a[0], b[0], f"{prefix}[0]")[:3])
    return diffs[:8]


def compare_endpoint(
    method: str,
    path: str,
    boot_tok: str,
    fast_tok: str,
    boot_base: str,
    fast_base: str,
) -> list[str]:
    if any(path.startswith(p) for p in PORTAL_ONLY_PREFIXES):
        return []
    bs, br = http_json(method, boot_base + path, boot_tok)
    fs, fr = http_json(method, fast_base + path, fast_tok)
    if bs != fs:
        return [f"{path}: HTTP {bs} vs {fs}"]
    if not isinstance(br, dict) or not isinstance(fr, dict):
        return []
    if str(br.get("code")) != str(fr.get("code")):
        return [f"{path}: code {br.get('code')} vs {fr.get('code')}"]
    bd, fd = br.get("data"), fr.get("data")
    if isinstance(bd, dict) and isinstance(fd, dict) and "records" in bd and "records" in fd:
        if bd.get("records") and fd.get("records"):
            br0, fr0 = pick_matching_records(bd["records"], fd["records"])
            if br0 and fr0:
                return shape_diff(br0, fr0, f"{path}.record")
            return shape_diff(bd["records"][0], fd["records"][0], f"{path}.record")
        if bool(bd.get("records")) != bool(fd.get("records")):
            return [f"{path}: records empty mismatch"]
        return []
    if isinstance(bd, dict) and isinstance(fd, dict):
        return shape_diff(bd, fd, path)
    if type(bd) is not type(fd):
        return [f"{path}: data type {type(bd).__name__} vs {type(fd).__name__}"]
    return []


def module_matches_filter(mod: str, module_filter: str) -> bool:
    if not module_filter:
        return True
    return mod == module_filter or mod.startswith(module_filter.rstrip("/") + "/")


def main() -> int:
    parser = argparse.ArgumentParser(description="Boot vs FastAPI module response shape compare")
    parser.add_argument("--module", default="", help="compare single module (e.g. sys/audit)")
    parser.add_argument("--boot", default=BOOT)
    parser.add_argument("--fastapi", default=FASTAPI)
    parser.add_argument("--boot-redis-db", type=int, default=0)
    parser.add_argument("--fastapi-redis-db", type=int, default=3)
    parser.add_argument("--out", default="scripts/e2e/reports/module-compare.json")
    args = parser.parse_args()

    boot_base = args.boot.rstrip("/")
    fast_base = args.fastapi.rstrip("/")

    boot_tok = login(boot_base, args.boot_redis_db)
    fast_tok = login(fast_base, args.fastapi_redis_db)
    print("login OK (boot + fastapi)\n")

    report: dict[str, Any] = {"modules": {}, "summary": {}}
    ok_count = 0
    selected = {
        mod: endpoints
        for mod, endpoints in MODULE_ENDPOINTS.items()
        if module_matches_filter(mod, args.module)
    }
    for mod, endpoints in selected.items():
        diffs: list[str] = []
        for method, path in endpoints:
            diffs.extend(compare_endpoint(method, path, boot_tok, fast_tok, boot_base, fast_base))
        status = "aligned" if not diffs else "diff"
        if status == "aligned":
            ok_count += 1
        report["modules"][mod] = {"status": status, "diffs": diffs}
        mark = "OK" if not diffs else "DIFF"
        print(f"[{mark}] {mod}")
        for d in diffs[:5]:
            print(f"  - {d}")

    total = len(selected)
    report["summary"] = {
        "aligned": ok_count,
        "total": total,
        "diff": total - ok_count,
        "module_filter": args.module or None,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n=== SUMMARY aligned={ok_count}/{total} ===")
    print(f"report: {args.out}")
    return 0 if ok_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
