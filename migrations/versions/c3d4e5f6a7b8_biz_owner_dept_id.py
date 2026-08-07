""" Author: Charlie

为现有 biz 主表（若存在）添加 owner_dept_id。
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8_biz_owner_dept"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7_audit_outbox"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "cg_test_activity",
    "cg_test_catalog",
    "cg_test_order",
    "cg_test_knowledge_category",
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    for table in _TABLES:
        if table not in existing:
            continue
        columns = {col["name"] for col in inspector.get_columns(table)}
        if "owner_dept_id" in columns:
            continue
        op.add_column(
            table,
            sa.Column(
                "owner_dept_id",
                sa.String(length=64),
                nullable=True,
                comment="所属部门ID（数据范围）",
            ),
        )
        op.create_index(f"ix_{table}_owner_dept_id", table, ["owner_dept_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    for table in _TABLES:
        if table not in existing:
            continue
        columns = {col["name"] for col in inspector.get_columns(table)}
        if "owner_dept_id" not in columns:
            continue
        op.drop_index(f"ix_{table}_owner_dept_id", table_name=table)
        op.drop_column(table, "owner_dept_id")
