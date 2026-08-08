""" Author: Charlie

新增个人工作台快捷入口表。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "38e3d922ce9b"
down_revision: str | Sequence[str] | None = "f6a7b8c9d0e1_drop_im_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index(
        "idx_sys_workbench_shortcut_account_sort",
        table_name="sys_workbench_shortcut",
    )
    op.drop_table("sys_workbench_shortcut")
