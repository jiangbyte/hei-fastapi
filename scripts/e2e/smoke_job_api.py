"""Login to admin API and smoke-test job endpoints against copied hei_boot DB."""

from __future__ import annotations

import base64
import json
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def _get_json(url: str) -> dict:
    with urlopen(Request(url), timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, payload: dict, cookie: str | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if cookie:
        headers["Cookie"] = cookie
    req = Request(url, data=data, headers=headers, method="POST")
    with urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        set_cookie = resp.headers.get("Set-Cookie")
        return {"body": json.loads(body), "set_cookie": set_cookie}


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


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    account = sys.argv[2] if len(sys.argv) > 2 else "superadmin"
    password = sys.argv[3] if len(sys.argv) > 3 else "Admin@123456"

    captcha = _get_json(f"{base}/api/v1/admin/captcha?format=svg")["data"]
    pwd_key = _get_json(f"{base}/api/v1/admin/password-key")["data"]
    encrypted = _encrypt_password(pwd_key["public_key"], password)

    login_resp = _post_json(
        f"{base}/api/v1/admin/login",
        {
            "account": account,
            "password": encrypted,
            "password_key_id": pwd_key["key_id"],
            "captcha_id": captcha["captcha_id"],
            "captcha_value": captcha.get("captcha_value") or "skip",
            "identity_type": "ACCOUNT",
            "login_mode": "PASSWORD",
        },
    )
    # captcha_value in dev might need real value - try reading from svg endpoint issue
    body = login_resp["body"]
    if body.get("code") != 0:
        print("LOGIN_FAILED:", json.dumps(body, ensure_ascii=False))
        return 1

    cookie = login_resp.get("set_cookie") or ""
    if not cookie:
        token = body.get("data", {}).get("token")
        cookie = f"Authorization={token}" if token else ""

    jobs = _get_json_with_cookie(f"{base}/api/v1/admin/sys/jobs/page?current=1&size=5", cookie)
    logs = _get_json_with_cookie(f"{base}/api/v1/admin/sys/job-logs/page?current=1&size=5", cookie)

    print("jobs.page code:", jobs.get("code"))
    records = (jobs.get("data") or {}).get("records") or []
    if records:
        first = records[0]
        print("first job keys:", sorted(first.keys()))
        print("first job handler:", first.get("handler"))
        print("first job trigger_type:", first.get("trigger_type"))

    print("job-logs.page code:", logs.get("code"))
    log_records = (logs.get("data") or {}).get("records") or []
    if log_records:
        print("first log keys:", sorted(log_records[0].keys()))

    return 0


def _get_json_with_cookie(url: str, cookie: str) -> dict:
    headers = {"Cookie": cookie} if cookie else {}
    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
