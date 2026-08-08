""" Author: Charlie

恢复丢失的 ACCOUNT_STATUS 字典根节点，并修正通知严重级别 CRITICAL 挂载。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "c6d7e8f9a0b1"
down_revision: str | Sequence[str] | None = "b5c6d7e8f9a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 6, 29, tzinfo=UTC)


def upgrade() -> None:
    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT 1 FROM sys_dict WHERE code = 'ACCOUNT_STATUS' LIMIT 1")
    ).scalar()
    if not exists:
        conn.execute(
            sa.text(
                """
                INSERT INTO sys_dict (
                    id, code, label, value, color, category, parent_id, status, sort,
                    created_at, created_by, updated_at, updated_by
                ) VALUES (
                    '100010', 'ACCOUNT_STATUS', '账号状态', 'ACCOUNT_STATUS',
                    '#2080f0', 'SYS', NULL, 'ENABLED', 0,
                    :now, NULL, :now, NULL
                )
                """
            ),
            {"now": _NOW},
        )

    # 子项若仍指向旧父级 id，统一挂回 100010
    conn.execute(
        sa.text(
            """
            UPDATE sys_dict
            SET parent_id = '100010'
            WHERE code IN (
                'ACCOUNT_STATUS_ENABLED',
                'ACCOUNT_STATUS_DISABLED',
                'ACCOUNT_STATUS_CANCELLED'
            )
              AND (parent_id IS DISTINCT FROM '100010')
            """
        )
    )

    # 种子误把 CRITICAL 挂到不存在的 100122
    conn.execute(
        sa.text(
            """
            UPDATE sys_dict
            SET parent_id = '100095',
                value = 'CRITICAL',
                sort = 5
            WHERE code = 'NOTIFICATION_SEVERITY_CRITICAL'
            """
        )
    )


def downgrade() -> None:
    # 数据修复，不回滚删除根节点
    pass
