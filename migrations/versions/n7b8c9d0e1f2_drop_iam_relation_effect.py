""" Author: Charlie

删除未使用的 sys_iam_relation.effect 列。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "n7b8c9d0e1f2"
down_revision: str | Sequence[str] | None = "m6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("sys_iam_relation", "effect")


def downgrade() -> None:
    op.add_column(
        "sys_iam_relation",
        sa.Column(
            "effect",
            sa.String(length=32),
            nullable=False,
            server_default="ALLOW",
            comment="授权效果",
        ),
    )
    op.alter_column("sys_iam_relation", "effect", server_default=None)
