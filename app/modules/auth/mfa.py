""" Author: Charlie

管理端 TOTP MFA 辅助工具与 challenge 存储。
"""
from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import pyotp
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.core.exceptions.business import AuthenticationError, BusinessError
from app.core.security.password import hash_password, verify_password
from app.modules.iam.account.model import SysAccount
from app.platform.cache.redis import get_redis
from app.platform.config.crypto import decrypt_secret, encrypt_secret

_CHALLENGE_PREFIX = "auth:mfa_challenge:"
_PENDING_SETUP_PREFIX = "auth:mfa_setup:"


@dataclass(slots=True)
class MfaChallenge:
    account_id: str
    account_type: str
    remember_me: bool
    client_ip: str | None
    user_agent: str | None
    device_label: str | None
    login_account: str


def _challenge_key(challenge_id: str) -> str:
    return f"{_CHALLENGE_PREFIX}{challenge_id}"


def _setup_key(account_id: str) -> str:
    return f"{_PENDING_SETUP_PREFIX}{account_id}"


def _redis():
    redis = get_redis()
    if redis is None:
        raise BusinessError("Redis is required for MFA")
    return redis


async def create_mfa_challenge(
    *,
    account: SysAccount,
    login_account: str,
    remember_me: bool,
    client_ip: str | None,
    user_agent: str | None,
    device_label: str | None,
) -> str:
    challenge_id = uuid4().hex
    payload = {
        "account_id": account.id,
        "account_type": account.account_type,
        "remember_me": remember_me,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "device_label": device_label,
        "login_account": login_account,
    }
    redis = _redis()
    await redis.set(
        _challenge_key(challenge_id),
        json.dumps(payload),
        ex=settings.auth.mfa_challenge_ttl_seconds,
    )
    return challenge_id


async def consume_mfa_challenge(challenge_id: str) -> MfaChallenge:
    redis = _redis()
    raw = None
    if hasattr(redis, "getdel"):
        raw = await redis.getdel(_challenge_key(challenge_id))
    else:
        raw = await redis.get(_challenge_key(challenge_id))
        if raw is not None:
            await redis.delete(_challenge_key(challenge_id))
    if not raw:
        raise AuthenticationError("MFA challenge expired or invalid")
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode()
    data = json.loads(raw)
    return MfaChallenge(
        account_id=str(data["account_id"]),
        account_type=str(data["account_type"]),
        remember_me=bool(data.get("remember_me", True)),
        client_ip=data.get("client_ip"),
        user_agent=data.get("user_agent"),
        device_label=data.get("device_label"),
        login_account=str(data.get("login_account") or ""),
    )


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_otpauth_uri(*, secret: str, account_label: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=account_label, issuer_name=settings.auth.mfa_issuer)


def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(code.strip(), valid_window=1))


def generate_backup_codes(count: int = 8) -> list[str]:
    return [secrets.token_hex(4) for _ in range(count)]


def hash_backup_codes(codes: list[str]) -> str:
    return json.dumps([hash_password(code) for code in codes])


def consume_backup_code(stored_json: str | None, code: str) -> str | None:
    """验证码匹配时返回更新后的 hash JSON，否则返回 None。"""
    if not stored_json:
        return None
    hashes: list[str] = json.loads(stored_json)
    remaining: list[str] = []
    matched = False
    for item in hashes:
        if not matched and verify_password(code.strip(), item):
            matched = True
            continue
        remaining.append(item)
    if not matched:
        return None
    return json.dumps(remaining)


async def store_pending_setup(account_id: str, secret: str) -> None:
    redis = _redis()
    await redis.set(
        _setup_key(account_id),
        encrypt_secret(secret),
        ex=settings.auth.mfa_challenge_ttl_seconds,
    )


async def load_pending_setup(account_id: str) -> str:
    redis = _redis()
    raw = await redis.get(_setup_key(account_id))
    if not raw:
        raise BusinessError("MFA setup expired; start again")
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode()
    secret = decrypt_secret(str(raw))
    if not secret:
        raise BusinessError("MFA setup secret unavailable")
    return secret


async def clear_pending_setup(account_id: str) -> None:
    redis = _redis()
    await redis.delete(_setup_key(account_id))


def decrypt_account_mfa_secret(account: SysAccount) -> str:
    if not account.mfa_secret_encrypted:
        raise AuthenticationError("MFA is not configured")
    secret = decrypt_secret(account.mfa_secret_encrypted)
    if not secret:
        raise AuthenticationError("MFA secret unavailable")
    return secret


async def enable_mfa_on_account(
    db: AsyncSession,
    account: SysAccount,
    *,
    secret: str,
    backup_codes: list[str],
) -> None:
    account.mfa_enabled = True
    account.mfa_secret_encrypted = encrypt_secret(secret)
    account.mfa_enabled_at = datetime.now(UTC)
    account.mfa_backup_codes_hash = hash_backup_codes(backup_codes)
    await db.flush()


async def disable_mfa_on_account(db: AsyncSession, account: SysAccount) -> None:
    account.mfa_enabled = False
    account.mfa_secret_encrypted = None
    account.mfa_enabled_at = None
    account.mfa_backup_codes_hash = None
    account.webauthn_credentials_json = None
    await db.flush()
