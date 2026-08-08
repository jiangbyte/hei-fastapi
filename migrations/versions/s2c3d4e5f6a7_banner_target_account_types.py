""" Author: Charlie

展示图：display_scope 改为目标账户类型列表 target_account_types（对齐消息管理）。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "s2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "r1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.add_column(
            "sys_banner",
            sa.Column(
                "target_account_types",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
                comment="目标账户类型列表（AccountType：ADMIN/PORTAL）",
            ),
        )
    else:
        op.add_column(
            "sys_banner",
            sa.Column(
                "target_account_types",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
                comment="目标账户类型列表（AccountType：ADMIN/PORTAL）",
            ),
        )

    # PORTAL/APP -> ["PORTAL"]；ADMIN -> ["ADMIN"]；其它默认 PORTAL
    if dialect == "postgresql":
        bind.execute(
            sa.text(
                """
                UPDATE sys_banner
                SET target_account_types = CASE
                    WHEN display_scope = 'ADMIN' THEN '["ADMIN"]'::jsonb
                    ELSE '["PORTAL"]'::jsonb
                END
                """
            )
        )
    else:
        bind.execute(
            sa.text(
                """
                UPDATE sys_banner
                SET target_account_types = CASE
                    WHEN display_scope = 'ADMIN' THEN '["ADMIN"]'
                    ELSE '["PORTAL"]'
                END
                """
            )
        )

    op.drop_index("ix_sys_banner_scope_position_status_sort", table_name="sys_banner")
    op.drop_column("sys_banner", "display_scope")
    op.create_index(
        "ix_sys_banner_position_status_sort",
        "sys_banner",
        ["position", "status", "sort"],
    )
    op.alter_column("sys_banner", "target_account_types", server_default=None)

    # 清理展示渠道字典（账户类型改走前端 ACCOUNT_TYPE 常量）
    bind.execute(
        sa.text(
            """
            DELETE FROM sys_dict
            WHERE code = 'BANNER_DISPLAY_SCOPE'
               OR code LIKE 'BANNER_DISPLAY_SCOPE_%'
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.add_column(
        "sys_banner",
        sa.Column(
            "display_scope",
            sa.String(length=32),
            nullable=False,
            server_default="PORTAL",
            comment="显示端：展示图显示端",
        ),
    )

    if dialect == "postgresql":
        bind.execute(
            sa.text(
                """
                UPDATE sys_banner
                SET display_scope = CASE
                    WHEN target_account_types ? 'ADMIN'
                         AND NOT (target_account_types ? 'PORTAL')
                    THEN 'ADMIN'
                    ELSE 'PORTAL'
                END
                """
            )
        )
    else:
        bind.execute(
            sa.text(
                """
                UPDATE sys_banner
                SET display_scope = CASE
                    WHEN CAST(target_account_types AS TEXT) LIKE '%"ADMIN"%'
                         AND CAST(target_account_types AS TEXT) NOT LIKE '%"PORTAL"%'
                    THEN 'ADMIN'
                    ELSE 'PORTAL'
                END
                """
            )
        )

    op.drop_index("ix_sys_banner_position_status_sort", table_name="sys_banner")
    op.drop_column("sys_banner", "target_account_types")
    op.create_index(
        "ix_sys_banner_scope_position_status_sort",
        "sys_banner",
        ["display_scope", "position", "status", "sort"],
    )
    op.alter_column("sys_banner", "display_scope", server_default=None)
