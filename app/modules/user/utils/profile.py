""" Author: Charlie

用户资料批量查询与审计字段名 enrichment。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType, account_types_with_profile
from app.core.exceptions.business import BusinessError
from app.modules.user.admin.model import ProfileUserAdmin
from app.modules.user.admin.repository import ProfileUserAdminRepository
from app.modules.user.portal.model import ProfileUserPortal
from app.modules.user.portal.repository import ProfileUserPortalRepository


def as_account_type(account_type: AccountType | str) -> AccountType:
    """将账户类型归一化为 AccountType 枚举，非法值抛 BusinessError。"""
    if isinstance(account_type, AccountType):
        return account_type
    try:
        return AccountType(str(account_type))
    except ValueError as exc:
        raise BusinessError(f"Unsupported account type: {account_type}") from exc


def pick_profile_repo(db: AsyncSession, account_type: AccountType | str):
    """按账户类型返回对应的资料仓储实例。"""
    account_type = as_account_type(account_type)
    match account_type:
        case AccountType.ADMIN:
            return ProfileUserAdminRepository(db)
        case AccountType.PORTAL:
            return ProfileUserPortalRepository(db)
        case _:
            raise BusinessError(f"Unsupported account type for profile: {account_type}")


def pick_profile_model(account_type: AccountType | str):
    """按账户类型返回对应的资料模型类。"""
    account_type = as_account_type(account_type)
    match account_type:
        case AccountType.ADMIN:
            return ProfileUserAdmin
        case AccountType.PORTAL:
            return ProfileUserPortal
        case _:
            raise BusinessError(f"Unsupported account type for profile: {account_type}")


async def get_profile(
    db: AsyncSession, account_type: AccountType | str, account_id: str
) -> object | None:
    """按账户类型与 ID 查询资料记录，不存在时返回 None。"""
    repo = pick_profile_repo(db, account_type)
    return await repo.get_by_account_id(account_id)


async def get_profiles_batch(
    db: AsyncSession,
    account_type: AccountType | str,
    account_ids: list[str],
) -> dict[str, object]:
    """批量查询资料记录，返回以 account_id 为键的字典。"""
    if not account_ids:
        return {}
    repo = pick_profile_repo(db, account_type)
    profiles = await repo.list_by_account_ids(list(dict.fromkeys(account_ids)))
    return {p.account_id: p for p in profiles}


def _profile_display_name(profile: object) -> str | None:
    """提取资料展示名（优先姓名，其次昵称）。"""
    name = getattr(profile, "name", None) or getattr(profile, "nickname", None)
    return str(name) if name else None


async def enrich_audit_names(
    db: AsyncSession,
    schemas: list[Any],
    *,
    account_type: AccountType | str | None = None,
    created_by_attr: str = "created_by",
    updated_by_attr: str = "updated_by",
    created_name_attr: str = "created_name",
    updated_name_attr: str = "updated_name",
) -> list[Any]:
    """从各端 profile 填充 schema 的 created_name / updated_name。

    若未指定 account_type，则在具备资料表的端上合并查找（ADMIN + PORTAL）。
    """
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

    profiles: dict[str, object] = {}
    if account_type is None:
        for client in account_types_with_profile():
            profiles.update(await get_profiles_batch(db, client, list(all_ids)))
    else:
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
    account_type: AccountType | str | None = None,
) -> Any:
    """为单条 schema 补充 created_name / updated_name。"""
    await enrich_audit_names(db, [schema], account_type=account_type)
    return schema
