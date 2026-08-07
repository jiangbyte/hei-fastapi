""" Author: Charlie

签名公共文件访问 URL（HMAC-SHA256）。
"""
from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import quote, urlencode, urljoin

from app.core.config.settings import settings


def _signing_secret() -> bytes:
    key = (settings.app.config_crypto_key or "").strip()
    if not key:
        # 本地/开发环境无加密密钥时的确定性回退——仍优于完全开放。
        key = f"{settings.app.name}:file-signing"
    return key.encode("utf-8")


def sign_object_access(object_name: str, *, expires_at: int | None = None, ttl_seconds: int = 3600) -> tuple[int, str]:
    """返回 (expires_unix, hex_signature)。"""
    expires = expires_at if expires_at is not None else int(time.time()) + max(60, ttl_seconds)
    message = f"{object_name.strip('/')}:{expires}".encode("utf-8")
    sig = hmac.new(_signing_secret(), message, hashlib.sha256).hexdigest()
    return expires, sig


def verify_object_access(object_name: str, expires: int | str | None, signature: str | None) -> bool:
    if not signature or expires is None or expires == "":
        return False
    try:
        exp = int(expires)
    except (TypeError, ValueError):
        return False
    if exp < int(time.time()):
        return False
    expected_exp, expected_sig = sign_object_access(object_name, expires_at=exp)
    if expected_exp != exp:
        return False
    return hmac.compare_digest(expected_sig, signature.strip().lower())


def build_signed_file_query(object_name: str, *, ttl_seconds: int = 3600) -> str:
    expires, sig = sign_object_access(object_name, ttl_seconds=ttl_seconds)
    quoted = quote(object_name.strip("/"), safe="/")
    return urlencode({"object_name": quoted, "expires": str(expires), "sig": sig})
