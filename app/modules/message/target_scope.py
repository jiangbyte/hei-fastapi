""" Author: Charlie

消息目标范围与目标列表的一致性校验。
"""

from typing import Any

from app.modules.message.enums import TargetScope


def validate_message_targets(
    *,
    target_scope: str,
    target_account_types: list[str],
    target_account_ids: list[str],
    target_dept_ids: list[str],
    target_role_ids: list[str],
) -> None:
    scope = str(target_scope or "").upper()
    allowed = {s.value for s in TargetScope}
    if scope not in allowed:
        raise ValueError("目标范围仅支持全部 / 按账户类型 / 指定用户")
    if not target_account_types:
        raise ValueError("必须选择目标账户类型")
    if scope == TargetScope.SPECIFIC.value and not target_account_ids:
        raise ValueError("指定用户时必须选择目标用户")
    _ = target_dept_ids, target_role_ids  # 未实现 DEPARTMENT/ROLE 匹配


def has_enabled_publish_location(publish_locations: dict[str, Any] | None) -> bool:
    if not publish_locations:
        return False
    return any(bool(v) for v in publish_locations.values())
