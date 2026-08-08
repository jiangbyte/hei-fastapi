""" Author: Charlie

account_type 下沉到 sys_client_module，删除 sys_client。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "p9d0e1f2a3b4"
down_revision: str | Sequence[str] | None = "o8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sys_client_module",
        sa.Column(
            "account_type",
            sa.String(length=32),
            nullable=False,
            server_default="ADMIN",
            comment="账户体系",
        ),
    )
    op.execute(
        """
        UPDATE sys_client_module AS m
        SET account_type = c.account_type
        FROM sys_client AS c
        WHERE m.client_id = c.id
        """
    )
    # Global unique(code): rename duplicates as code-<account_type>
    op.execute(
        """
        UPDATE sys_client_module AS m
        SET code = m.code || '-' || lower(m.account_type)
        WHERE (
            SELECT COUNT(*) FROM sys_client_module AS m2 WHERE m2.code = m.code
        ) > 1
        """
    )
    op.drop_constraint("uq_sys_client_module_client_id_code", "sys_client_module", type_="unique")
    op.drop_index("ix_sys_client_module_client_id", table_name="sys_client_module")
    op.drop_column("sys_client_module", "client_id")
    op.create_unique_constraint("uq_sys_client_module_code", "sys_client_module", ["code"])
    op.create_index("ix_sys_client_module_account_type", "sys_client_module", ["account_type"])
    op.alter_column("sys_client_module", "account_type", server_default=None)
    op.drop_table("sys_client")


def downgrade() -> None:
    op.create_table(
        "sys_client",
        sa.Column("id", sa.String(length=64), primary_key=True, comment="主键"),
        sa.Column("name", sa.String(length=64), nullable=False, comment="客户端名称"),
        sa.Column("code", sa.String(length=64), nullable=False, comment="客户端编码"),
        sa.Column(
            "account_type",
            sa.String(length=32),
            nullable=False,
            server_default="ADMIN",
            comment="账户体系",
        ),
        sa.Column("icon", sa.String(length=255), comment="图标"),
        sa.Column("color", sa.String(length=32), comment="颜色"),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="99", comment="排序"),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="ENABLED",
            comment="状态",
        ),
        sa.Column("description", sa.Text(), comment="描述"),
        sa.Column("extra", sa.JSON(), nullable=False, server_default=sa.text("'{}'"), comment="扩展信息"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("created_by", sa.String(length=64), comment="创建人"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
        sa.Column("updated_by", sa.String(length=64), comment="更新人"),
        sa.UniqueConstraint("code", name="uq_sys_client_code"),
    )
    op.drop_index("ix_sys_client_module_account_type", table_name="sys_client_module")
    op.drop_constraint("uq_sys_client_module_code", "sys_client_module", type_="unique")
    op.add_column(
        "sys_client_module",
        sa.Column("client_id", sa.String(length=64), nullable=True, comment="所属客户端ID"),
    )
    # Downgrade cannot fully restore client rows; leave client_id nullable for emergency only.
    op.create_index("ix_sys_client_module_client_id", "sys_client_module", ["client_id"])
    op.create_unique_constraint(
        "uq_sys_client_module_client_id_code",
        "sys_client_module",
        ["client_id", "code"],
    )
    op.drop_column("sys_client_module", "account_type")
