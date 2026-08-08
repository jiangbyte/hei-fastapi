""" Author: Charlie

从 ACCOUNT_TYPE / RESOURCE_MODULE_CLIENT 字典移除 APP（APP 仅属展示渠道 BANNER_DISPLAY_SCOPE）。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a8c1d2e3f4b5"
down_revision: str | Sequence[str] | None = "38e3d922ce9b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM sys_dict WHERE code IN ('ACCOUNT_TYPE_APP', 'RESOURCE_MODULE_CLIENT_APP')")
    )
    bind.execute(
        sa.text("UPDATE sys_dict SET label = '管理员' WHERE code = 'ACCOUNT_TYPE_ADMIN'")
    )
    bind.execute(
        sa.text("UPDATE sys_dict SET label = '门户用户' WHERE code = 'ACCOUNT_TYPE_PORTAL'")
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("UPDATE sys_dict SET label = '管理端' WHERE code = 'ACCOUNT_TYPE_ADMIN'")
    )
    bind.execute(
        sa.text("UPDATE sys_dict SET label = '门户端' WHERE code = 'ACCOUNT_TYPE_PORTAL'")
    )
    # 仅在缺失时回插，避免与现有主键冲突
    bind.execute(
        sa.text(
            """
            INSERT INTO sys_dict (
                id, code, label, value, color, category, parent_id, status, sort,
                created_at, created_by, updated_at, updated_by
            )
            SELECT
                'acct_type_app_restore', 'ACCOUNT_TYPE_APP', '移动端', 'APP', '#f0a020',
                'SYS', parent.id, 'ENABLED', 3, NOW(), NULL, NOW(), NULL
            FROM sys_dict AS parent
            WHERE parent.code = 'ACCOUNT_TYPE'
              AND NOT EXISTS (SELECT 1 FROM sys_dict WHERE code = 'ACCOUNT_TYPE_APP')
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO sys_dict (
                id, code, label, value, color, category, parent_id, status, sort,
                created_at, created_by, updated_at, updated_by
            )
            SELECT
                'res_mod_client_app_restore', 'RESOURCE_MODULE_CLIENT_APP', '移动端', 'APP',
                '#f0a020', 'SYS', parent.id, 'ENABLED', 3, NOW(), NULL, NOW(), NULL
            FROM sys_dict AS parent
            WHERE parent.code = 'RESOURCE_MODULE_CLIENT'
              AND NOT EXISTS (SELECT 1 FROM sys_dict WHERE code = 'RESOURCE_MODULE_CLIENT_APP')
            """
        )
    )
