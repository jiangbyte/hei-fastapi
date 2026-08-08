""" Author: Charlie

新增客户端 / 客户端模块 / 客户端资源并列树表。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "o8c9d0e1f2a3"
down_revision: str | Sequence[str] | None = "n7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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
    op.create_table(
        "sys_client_module",
        sa.Column("id", sa.String(length=64), primary_key=True, comment="主键"),
        sa.Column("client_id", sa.String(length=64), nullable=False, comment="所属客户端ID"),
        sa.Column("name", sa.String(length=64), nullable=False, comment="模块名称"),
        sa.Column("code", sa.String(length=64), nullable=False, comment="模块编码"),
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
        sa.UniqueConstraint("client_id", "code", name="uq_sys_client_module_client_id_code"),
    )
    op.create_index("ix_sys_client_module_client_id", "sys_client_module", ["client_id"])
    op.create_table(
        "sys_client_resource",
        sa.Column("id", sa.String(length=64), primary_key=True, comment="主键"),
        sa.Column("parent_id", sa.String(length=64), comment="父资源ID"),
        sa.Column("code", sa.String(length=64), nullable=False, comment="资源编码"),
        sa.Column("name", sa.String(length=64), nullable=False, comment="资源名称"),
        sa.Column("resource_type", sa.String(length=32), nullable=False, comment="资源类型"),
        sa.Column("module_id", sa.String(length=64), comment="所属客户端模块ID"),
        sa.Column("path", sa.String(length=255), comment="路由路径"),
        sa.Column("component", sa.String(length=255), comment="前端组件"),
        sa.Column("redirect", sa.String(length=255), comment="重定向地址"),
        sa.Column("icon", sa.String(length=255), comment="图标"),
        sa.Column("color", sa.String(length=32), comment="颜色"),
        sa.Column("href", sa.String(length=255), comment="外链地址"),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="99", comment="排序"),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("true"), comment="是否可见"),
        sa.Column("is_cache", sa.Boolean(), nullable=False, server_default=sa.text("false"), comment="是否缓存"),
        sa.Column("is_affix", sa.Boolean(), nullable=False, server_default=sa.text("false"), comment="是否固定标签"),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="ENABLED",
            comment="状态",
        ),
        sa.Column("description", sa.Text(), comment="描述"),
        sa.Column("layout", sa.String(length=255), comment="布局类型"),
        sa.Column("extra", sa.JSON(), nullable=False, server_default=sa.text("'{}'"), comment="扩展信息"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("created_by", sa.String(length=64), comment="创建人"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, comment="更新时间"),
        sa.Column("updated_by", sa.String(length=64), comment="更新人"),
        sa.UniqueConstraint("module_id", "code", name="uq_sys_client_resource_module_id_code"),
    )
    op.create_index("ix_sys_client_resource_module_id", "sys_client_resource", ["module_id"])
    op.create_index("ix_sys_client_resource_parent_id", "sys_client_resource", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_sys_client_resource_parent_id", table_name="sys_client_resource")
    op.drop_index("ix_sys_client_resource_module_id", table_name="sys_client_resource")
    op.drop_table("sys_client_resource")
    op.drop_index("ix_sys_client_module_client_id", table_name="sys_client_module")
    op.drop_table("sys_client_module")
    op.drop_table("sys_client")
