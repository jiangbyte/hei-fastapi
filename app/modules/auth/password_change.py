""" Author: Charlie

自助改密验证：OLD_PASSWORD / EMAIL_CODE / PHONE_CODE。
"""

from __future__ import annotations

import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.config.settings import settings
from app.core.exceptions.business import BusinessError
from app.core.security.password import verify_password
from app.modules.iam.account.model import SysAccount
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.enums import AccountIdentityType
from app.platform.cache.keys import change_password_otp_key
from app.platform.cache.redis import get_redis
from app.platform.config.reader import config_reader
from app.platform.email.sender import send_templated_mail
from app.platform.sms.sender import send_templated_sms


def change_verify_method() -> str:
    return (config_reader.get("PASSWORD_CHANGE_VERIFY_METHOD") or "OLD_PASSWORD").strip().upper()


async def send_change_password_code(
    db: AsyncSession,
    *,
    account: SysAccount,
    account_type: AccountType,
) -> None:
    method = change_verify_method()
    if method not in {"EMAIL_CODE", "PHONE_CODE"}:
        raise BusinessError("Current password change method does not use verification code")
    identity_type = (
        AccountIdentityType.EMAIL if method == "EMAIL_CODE" else AccountIdentityType.PHONE
    )
    identities = await AccountRepository(db).list_identities_by_account_ids([account.id])
    target = next(
        (item.identifier for item in identities if item.identity_type == identity_type.value),
        None,
    )
    if not target:
        raise BusinessError("Account has no bound contact for verification")
    code = f"{secrets.randbelow(1_000_000):06d}"
    redis = get_redis()
    if redis is None:
        raise BusinessError("Redis is required for password change verification")
    channel = "EMAIL" if method == "EMAIL_CODE" else "PHONE"
    ttl = settings.auth.password_reset_token_ttl_seconds
    await redis.setex(
        change_password_otp_key(account_type.value, channel, account.id),
        ttl,
        code,
    )
    variables = {
        "app_name": settings.app.name,
        "code": code,
        "expire_minutes": max(1, ttl // 60),
    }
    if channel == "EMAIL":
        await send_templated_mail("CHANGE_PASSWORD_CODE", target, variables)
    else:
        await send_templated_sms("CHANGE_PASSWORD_CODE", target, variables)


async def verify_change_password(
    db: AsyncSession,
    *,
    account: SysAccount,
    account_type: AccountType,
    old_password: str | None,
    otp_code: str | None,
) -> None:
    method = change_verify_method()
    if method == "OLD_PASSWORD":
        if not old_password or not verify_password(old_password, account.password_hash):
            raise BusinessError("Old password is incorrect")
        return
    if method in {"EMAIL_CODE", "PHONE_CODE"}:
        code = (otp_code or "").strip()
        if not code:
            raise BusinessError("Verification code is required")
        redis = get_redis()
        if redis is None:
            raise BusinessError("Redis is required for password change verification")
        channel = "EMAIL" if method == "EMAIL_CODE" else "PHONE"
        key = change_password_otp_key(account_type.value, channel, account.id)
        raw = await redis.get(key)
        stored = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if not stored or stored != code:
            raise BusinessError("Invalid or expired verification code")
        await redis.delete(key)
        return
    raise BusinessError(f"Unsupported password change verify method: {method}")
