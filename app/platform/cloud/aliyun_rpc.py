""" Author: Charlie

阿里云 RPC 风格 OpenAPI 签名（GET query）。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import uuid
from datetime import UTC, datetime
from urllib.parse import quote, urlencode

from app.platform.http.client import get_http_client


def _percent_encode(value: str) -> str:
    return quote(str(value), safe="~")


def sign_rpc_params(params: dict[str, str], access_key_secret: str) -> str:
    sorted_query = "&".join(
        f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted(params.items())
    )
    string_to_sign = f"GET&%2F&{_percent_encode(sorted_query)}"
    digest = hmac.new(
        (access_key_secret + "&").encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


async def aliyun_rpc_get(
    *,
    endpoint: str,
    access_key_id: str,
    access_key_secret: str,
    action: str,
    version: str,
    business_params: dict[str, str],
) -> dict:
    params = {
        "Format": "JSON",
        "Version": version,
        "AccessKeyId": access_key_id,
        "SignatureMethod": "HMAC-SHA1",
        "Timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "SignatureVersion": "1.0",
        "SignatureNonce": uuid.uuid4().hex,
        "Action": action,
        **business_params,
    }
    params["Signature"] = sign_rpc_params(params, access_key_secret)
    url = f"https://{endpoint}/?{urlencode(params)}"
    client = get_http_client()
    resp = await client.get(url)
    data = resp.json()
    if resp.status_code >= 400:
        raise RuntimeError(f"Aliyun RPC HTTP {resp.status_code}: {data}")
    if isinstance(data, dict):
        code = data.get("Code")
        if code is not None and str(code).upper() not in {"OK", "200"}:
            raise RuntimeError(f"Aliyun RPC error: {code} {data.get('Message')}")
    return data if isinstance(data, dict) else {"raw": data}
