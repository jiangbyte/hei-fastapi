""" Author: Charlie

去掉 sys_file.storage_config_id 历史列，解析存储仅依赖 storage_provider。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "h1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "g0a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    # 兜底：若 provider 空而旧 id 已是 provider 值，先回填
    conn.execute(
        sa.text(
            """
            UPDATE sys_file
            SET storage_provider = storage_config_id
            WHERE (storage_provider IS NULL OR storage_provider = '')
              AND storage_config_id IN ('local', 'minio', 'oss', 's3')
            """
        )
    )
    op.drop_column("sys_file", "storage_config_id")


def downgrade() -> None:
    op.add_column(
        "sys_file",
        sa.Column(
            "storage_config_id",
            sa.String(length=64),
            nullable=False,
            server_default="",
            comment="存储配置 ID",
        ),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE sys_file
            SET storage_config_id = storage_provider
            WHERE storage_provider IS NOT NULL AND storage_provider <> ''
            """
        )
    )
    op.alter_column("sys_file", "storage_config_id", server_default=None)
