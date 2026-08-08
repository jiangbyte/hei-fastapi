""" Author: Charlie

msg_feedback 增加 title；存量用 content 截断回填。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c1d2e3f4a5b6"
down_revision: str | Sequence[str] | None = "b9c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "msg_feedback",
        sa.Column("title", sa.String(length=255), nullable=True, comment="反馈标题"),
    )
    op.execute(
        sa.text(
            """
            UPDATE msg_feedback
            SET title = LEFT(COALESCE(NULLIF(BTRIM(content), ''), '未命名反馈'), 255)
            WHERE title IS NULL
            """
        )
    )
    op.alter_column("msg_feedback", "title", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    op.drop_column("msg_feedback", "title")
