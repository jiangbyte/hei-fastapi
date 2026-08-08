""" Author: Charlie

创建 sys_weak_password 弱密码库表。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d2e3f4a5b6c7"
down_revision: str | Sequence[str] | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sys_weak_password",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("password", sa.String(length=255), nullable=False, comment="弱密码值"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_weak_password")),
    )
    op.create_index(
        "idx_sys_weak_password_password",
        "sys_weak_password",
        ["password"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_sys_weak_password_password", table_name="sys_weak_password")
    op.drop_table("sys_weak_password")
