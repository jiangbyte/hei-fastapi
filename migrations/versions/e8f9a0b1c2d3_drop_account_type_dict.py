""" Author: Charlie

移除已由前端常量 / 后端枚举接管的 ACCOUNT_TYPE 字典。
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "e8f9a0b1c2d3"
down_revision: str | Sequence[str] | None = "d7e8f9a0b1c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 6, 29, tzinfo=UTC)


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM sys_dict
            WHERE code IN (
                'ACCOUNT_TYPE',
                'ACCOUNT_TYPE_ADMIN',
                'ACCOUNT_TYPE_PORTAL',
                'ACCOUNT_TYPE_APP'
            )
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT 1 FROM sys_dict WHERE code = 'ACCOUNT_TYPE' LIMIT 1")
    ).scalar()
    if exists:
        return
    conn.execute(
        sa.text(
            """
            INSERT INTO sys_dict (
                id, code, label, value, color, category, parent_id, status, sort,
                created_at, created_by, updated_at, updated_by
            ) VALUES
            (
                '100007', 'ACCOUNT_TYPE', '账号类型', 'ACCOUNT_TYPE',
                '#2080f0', 'SYS', NULL, 'ENABLED', 0,
                :now, NULL, :now, NULL
            ),
            (
                '100008', 'ACCOUNT_TYPE_ADMIN', '管理员', 'ADMIN',
                '#722ed1', 'SYS', '100007', 'ENABLED', 1,
                :now, NULL, :now, NULL
            ),
            (
                '100009', 'ACCOUNT_TYPE_PORTAL', '门户用户', 'PORTAL',
                '#18a058', 'SYS', '100007', 'ENABLED', 2,
                :now, NULL, :now, NULL
            )
            """
        ),
        {"now": _NOW},
    )
