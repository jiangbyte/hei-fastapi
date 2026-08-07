""" Author: Charlie

密码管理辅助工具 — 强度校验、历史记录、
复用检查与过期检测。

供 ``AuthService`` 与 ``AccountService`` 执行密码策略。
"""
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.core.security.password import hash_password, verify_password
from app.core.security.password_policy import validate_password_strength
from app.modules.iam.account.password_history import SysAccountPasswordHistory
from app.platform.id_generator.snowflake import generate_snowflake_id


def _parse_dt(value) -> datetime | None:
    """安全地将 datetime 或 None 解析为 UTC 时区的 datetime。"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    return None


async def validate_and_record_password(
    db: AsyncSession,
    account_id: str,
    plain_password: str,
    *,
    changed_by: str | None = None,
    change_reason: str | None = None,
) -> None:
    """校验密码强度、检查历史复用并记录。

    强度或复用违规时抛出 ``BusinessError``。
    """
    # 1. 强度校验
    validate_password_strength(plain_password)

    # 2. 历史复用校验
    await _check_password_reuse(db, account_id, plain_password)

    # 3. 记录到历史表
    db.add(
        SysAccountPasswordHistory(
            id=generate_snowflake_id(),
            account_id=account_id,
            password_hash=hash_password(plain_password),
            changed_by=changed_by or account_id,
            change_reason=change_reason or "unknown",
        )
    )


async def _check_password_reuse(db: AsyncSession, account_id: str, new_password: str) -> None:
    """检查新密码是否与最近历史记录中的任一密码相同。"""
    count = settings.password_policy.history_check_count
    if count <= 0:
        return

    stmt = (
        select(SysAccountPasswordHistory.password_hash)
        .where(SysAccountPasswordHistory.account_id == account_id)
        .order_by(SysAccountPasswordHistory.created_at.desc())
        .limit(count)
    )
    rows = (await db.execute(stmt)).scalars().all()

    for old_hash in rows:
        if verify_password(new_password, old_hash):
            from app.core.exceptions.business import BusinessError

            raise BusinessError(f"新密码不能与最近 {count} 次使用过的密码相同")


async def get_password_age_days(db: AsyncSession, account_id: str) -> float | None:
    """返回距上次改密的天数，未知时返回 ``None``。"""
    stmt = (
        select(SysAccountPasswordHistory.created_at)
        .where(SysAccountPasswordHistory.account_id == account_id)
        .order_by(SysAccountPasswordHistory.created_at.desc())
        .limit(1)
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        return None
    dt = _parse_dt(row)
    if dt is None:
        return None
    return (datetime.now(UTC) - dt).total_seconds() / 86400


async def is_password_expired(db: AsyncSession, account_id: str) -> bool:
    """检查账户密码是否已超过配置的过期期限。"""
    expire_days = settings.password_policy.expire_days
    if expire_days <= 0:
        return False
    age_days = await get_password_age_days(db, account_id)
    if age_days is None:
        return False
    return age_days >= expire_days
