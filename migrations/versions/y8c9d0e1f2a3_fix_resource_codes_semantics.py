""" Author: Charlie

校正管理端资源编码语义，使 code 与目录/菜单职责一致。
不改 path/component，不改 RESOURCE_PERMISSION.target_key（如 message:notice:*）。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "y8c9d0e1f2a3"
down_revision: str | Sequence[str] | None = "x7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 9, tzinfo=UTC)

# id -> new_code
_UP_CODES: dict[str, str] = {
    "200006": "org",  # 组织权限
    "200003": "ops",  # 系统运维
    "200019": "content",  # 内容运营
    "200005": "content-banner",  # 展示图
    "202200": "content-notice",  # 通知消息
    "202220": "content-feedback",  # 反馈管理
    "202230": "content-manage",  # 隐藏的旧嵌套目录
    "202001": "devtools",  # 开发工具
}

_DOWN_CODES: dict[str, str] = {
    "200006": "iam",
    "200003": "sys",
    "200019": "message",
    "200005": "sys-banner",
    "202200": "message-notice",
    "202220": "message-feedback",
    "202230": "message-manage",
    "202001": "system-test",
}


def _apply_codes(conn, mapping: dict[str, str]) -> None:
    for rid, code in mapping.items():
        conflict = conn.execute(
            sa.text(
                """
                SELECT id FROM sys_resource
                WHERE module_id = '210001' AND code = :code AND id <> :id
                LIMIT 1
                """
            ),
            {"code": code, "id": rid},
        ).scalar()
        if conflict:
            raise RuntimeError(f"code conflict: {code} already used by {conflict}")
        conn.execute(
            sa.text(
                """
                UPDATE sys_resource
                SET code = :code, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": rid, "code": code, "now": _NOW},
        )


def upgrade() -> None:
    _apply_codes(op.get_bind(), _UP_CODES)


def downgrade() -> None:
    _apply_codes(op.get_bind(), _DOWN_CODES)
