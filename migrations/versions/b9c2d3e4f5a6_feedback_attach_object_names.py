""" Author: Charlie

msg_feedback.attach_urls → attach_object_names。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b9c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "a8c1d2e3f4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "msg_feedback",
        "attach_urls",
        new_column_name="attach_object_names",
        existing_type=sa.JSON(),
        existing_nullable=False,
        comment="附件 object_name 列表",
    )


def downgrade() -> None:
    op.alter_column(
        "msg_feedback",
        "attach_object_names",
        new_column_name="attach_urls",
        existing_type=sa.JSON(),
        existing_nullable=False,
        comment="附件URL列表",
    )
