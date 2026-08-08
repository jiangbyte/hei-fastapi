""" Author: Charlie

删除个人工作台表、菜单资源与权限绑定。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "l5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "k4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RESOURCE_IDS = ("200002", "202301", "202302", "202303", "202304")
_PERM_REL_IDS = ("202311", "202312", "202313", "202314")


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM sys_iam_relation
            WHERE id = ANY(:ids)
               OR (
                    relation_type IN ('RESOURCE_PERMISSION', 'ROLE_RESOURCE', 'ACCOUNT_RESOURCE')
                    AND (
                        (subject_type = 'RESOURCE' AND subject_id = ANY(:resource_ids))
                        OR (target_type = 'RESOURCE' AND target_id = ANY(:resource_ids))
                    )
               )
               OR target_key LIKE 'workbench:%'
            """
        ),
        {
            "ids": list(_PERM_REL_IDS),
            "resource_ids": list(_RESOURCE_IDS),
        },
    )
    conn.execute(
        sa.text("DELETE FROM sys_resource WHERE id = ANY(:ids)"),
        {"ids": list(_RESOURCE_IDS)},
    )
    op.drop_table("sys_workbench_shortcut")


def downgrade() -> None:
    op.create_table(
        "sys_workbench_shortcut",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("account_id", sa.String(length=64), nullable=False, comment="所属账号ID"),
        sa.Column("resource_id", sa.String(length=64), nullable=False, comment="菜单资源ID"),
        sa.Column("sort", sa.Integer(), nullable=False, comment="排序"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_workbench_shortcut")),
        sa.UniqueConstraint(
            "account_id",
            "resource_id",
            name="uq_sys_workbench_shortcut_account_resource",
        ),
    )
    op.create_index(
        "idx_sys_workbench_shortcut_account_sort",
        "sys_workbench_shortcut",
        ["account_id", "sort"],
        unique=False,
    )
