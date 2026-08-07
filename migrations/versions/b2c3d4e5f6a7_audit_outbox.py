""" Author: Charlie

新增持久化操作审计 outbox 表。
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7_audit_outbox"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6_im_dual_channel"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sys_operation_audit_outbox",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_sys_operation_audit_outbox_status_created",
        "sys_operation_audit_outbox",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sys_operation_audit_outbox_status_created", table_name="sys_operation_audit_outbox")
    op.drop_table("sys_operation_audit_outbox")
