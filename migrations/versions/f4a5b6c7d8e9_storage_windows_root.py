""" Author: Charlie

sys_storage_config 增加 windows_root（本地 Windows 存储路径）。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f4a5b6c7d8e9"
down_revision: str | Sequence[str] | None = "e3f4a5b6c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sys_storage_config",
        sa.Column("windows_root", sa.String(length=500), nullable=True, comment="WINDOWS 本地存储根目录"),
    )


def downgrade() -> None:
    op.drop_column("sys_storage_config", "windows_root")
