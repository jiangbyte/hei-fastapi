""" Author: Charlie """

from app.core.security.permission_registry import (
    ensure_registered_permission_key,
    ensure_registered_permission_keys,
)


async def ensure_registered_permission(permission_key: str) -> None:
    await ensure_registered_permission_key(permission_key)


async def ensure_registered_permissions(permission_keys: list[str]) -> None:
    await ensure_registered_permission_keys(permission_keys)
