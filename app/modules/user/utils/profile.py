""" Author: Charlie

用户资料批量查询与审计字段名 enrichment。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.exceptions.business import BusinessError
from app.modules.user.admin.model import AdminUserProfile
from app.modules.user.admin.repository import AdminUserProfileRepository
from app.modules.user.portal.model import PortalUserProfile
from app.modules.user.portal.repository import PortalUserProfileRepository


def as_account_type(account_type: AccountType | str) -> AccountType:
    if isinstance(account_type, AccountType):
        return account_type
    try:
        return AccountType(str(account_type))
    except ValueError as exc:
        raise BusinessError(f"Unsupported account type: {account_type}") from exc


def pick_profile_repo(db: AsyncSession, account_type: AccountType | str):
    account_type = as_account_type(account_type)
    if account_type == AccountType.ADMIN:
        return AdminUserProfileRepository(db)
    if account_type == AccountType.PORTAL:
        return PortalUserProfileRepository(db)
    raise BusinessError(f"Unsupported account type: {account_type}")


def pick_profile_model(account_type: AccountType | str):
    account_type = as_account_type(account_type)
    if account_type == AccountType.ADMIN:
        return AdminUserProfile
    if account_type == AccountType.PORTAL:
        return PortalUserProfile
    raise BusinessError(f"Unsupported account type: {account_type}")


async def get_profile(
    db: AsyncSession, account_type: AccountType | str, account_id: str
) -> object | None:
    repo = pick_profile_repo(db, account_type)
    return await repo.get_by_account_id(account_id)


async def get_profiles_batch(
    db: AsyncSession,
    account_type: AccountType | str,
    account_ids: list[str],
) -> dict[str, object]:
    if not account_ids:
        return {}
    repo = pick_profile_repo(db, account_type)
    profiles = await repo.list_by_account_ids(list(dict.fromkeys(account_ids)))
    return {p.account_id: p for p in profiles}


def _profile_display_name(profile: object) -> str | None:
    name = getattr(profile, "name", None) or getattr(profile, "nickname", None)
    return str(name) if name else None


async def enrich_audit_names(
    db: AsyncSession,
    schemas: list[Any],
    *,
    account_type: AccountType | str = AccountType.ADMIN,
    created_by_attr: str = "created_by",
    updated_by_attr: str = "updated_by",
    created_name_attr: str = "created_name",
    updated_name_attr: str = "updated_name",
) -> list[Any]:
    """从 admin/portal profile 填充 schema 对象的 created_name / updated_name。"""
    if not schemas:
        return schemas
    all_ids: set[str] = set()
    for schema in schemas:
        created_by = getattr(schema, created_by_attr, None)
        updated_by = getattr(schema, updated_by_attr, None)
        if created_by:
            all_ids.add(str(created_by))
        if updated_by:
            all_ids.add(str(updated_by))
    if not all_ids:
        return schemas
    profiles = await get_profiles_batch(db, account_type, list(all_ids))
    for schema in schemas:
        created_by = getattr(schema, created_by_attr, None)
        updated_by = getattr(schema, updated_by_attr, None)
        if created_by and str(created_by) in profiles:
            setattr(schema, created_name_attr, _profile_display_name(profiles[str(created_by)]))
        if updated_by and str(updated_by) in profiles:
            setattr(schema, updated_name_attr, _profile_display_name(profiles[str(updated_by)]))
    return schemas


async def enrich_audit_name(
    db: AsyncSession,
    schema: Any,
    *,
    account_type: AccountType | str = AccountType.ADMIN,
) -> Any:
    await enrich_audit_names(db, [schema], account_type=account_type)
    return schema
