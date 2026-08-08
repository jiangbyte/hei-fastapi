""" Author: Charlie

sys_iam_relation 增加 account_type 并回填。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d7e8f9a0b1c2"
down_revision: str | Sequence[str] | None = "c6d7e8f9a0b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sys_iam_relation",
        sa.Column("account_type", sa.String(length=32), nullable=True, comment="账户类型"),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE sys_iam_relation r
            SET account_type = a.account_type
            FROM sys_account a
            WHERE r.subject_type = 'ACCOUNT' AND r.subject_id = a.id
              AND r.account_type IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE sys_iam_relation r
            SET account_type = a.account_type
            FROM sys_account a
            WHERE r.target_type = 'ACCOUNT' AND r.target_id = a.id
              AND r.account_type IS NULL
            """
        )
    )
    conn.execute(
        sa.text("UPDATE sys_iam_relation SET account_type = 'ADMIN' WHERE account_type IS NULL")
    )
    remaining = conn.execute(
        sa.text("SELECT COUNT(*) FROM sys_iam_relation WHERE account_type IS NULL")
    ).scalar()
    if remaining:
        raise RuntimeError(f"sys_iam_relation.account_type still null: {remaining}")
    op.alter_column("sys_iam_relation", "account_type", nullable=False)
    op.drop_constraint(
        "uq_sys_iam_relation_subject_relation_target",
        "sys_iam_relation",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_sys_iam_relation_subject_relation_target",
        "sys_iam_relation",
        [
            "subject_type",
            "subject_id",
            "relation_type",
            "target_type",
            "target_id",
            "target_key",
            "account_type",
        ],
    )
    op.create_index(
        "ix_sys_iam_relation_account_type_relation",
        "sys_iam_relation",
        ["account_type", "relation_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_sys_iam_relation_account_type_relation", table_name="sys_iam_relation")
    op.drop_constraint(
        "uq_sys_iam_relation_subject_relation_target",
        "sys_iam_relation",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_sys_iam_relation_subject_relation_target",
        "sys_iam_relation",
        [
            "subject_type",
            "subject_id",
            "relation_type",
            "target_type",
            "target_id",
            "target_key",
        ],
    )
    op.drop_column("sys_iam_relation", "account_type")
