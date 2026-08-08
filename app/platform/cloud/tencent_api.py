""" Author: Charlie

腾讯云 API 3.0（TC3-HMAC-SHA256）JSON 调用。
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime

from app.platform.http.client import get_http_client


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _sha256_hex(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def tencent_api_post(
    *,
    service: str,
    host: str,
    action: str,
    version: str,
    region: str,
    secret_id: str,
    secret_key: str,
    payload: dict,
) -> dict:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    timestamp = str(int(datetime.now(UTC).timestamp()))
    date = datetime.fromtimestamp(int(timestamp), tz=UTC).strftime("%Y-%m-%d")

    canonical_headers = f"content-type:application/json; charset=utf-8\nhost:{host}\n"
    signed_headers = "content-type;host"
    canonical_request = (
        "POST\n/\n\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{_sha256_hex(body)}"
    )
    credential_scope = f"{date}/{service}/tc3_request"
    string_to_sign = (
        "TC3-HMAC-SHA256\n"
        f"{timestamp}\n"
        f"{credential_scope}\n"
        f"{_sha256_hex(canonical_request)}"
    )
    secret_date = _hmac_sha256(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = _hmac_sha256(secret_date, service)
    secret_signing = _hmac_sha256(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    authorization = (
        "TC3-HMAC-SHA256 "
        f"Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json; charset=utf-8",
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Timestamp": timestamp,
        "X-TC-Version": version,
        "X-TC-Region": region,
    }
    client = get_http_client()
    resp = await client.post(f"https://{host}", content=body, headers=headers)
    data = resp.json()
    if resp.status_code >= 400:
        raise RuntimeError(f"Tencent API HTTP {resp.status_code}: {data}")
    response = data.get("Response") if isinstance(data, dict) else None
    if isinstance(response, dict) and response.get("Error"):
        err = response["Error"]
        raise RuntimeError(f"Tencent API error: {err.get('Code')} {err.get('Message')}")
    return response if isinstance(response, dict) else (data if isinstance(data, dict) else {})
