""" Author: Charlie

IM 双通道：离线队列、client_msg_id、热点索引。
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6_im_dual_channel"
down_revision: str | Sequence[str] | None = "f76f51e0ec54"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 重建离线队列（不再兼容旧格式双读）
    op.execute("DROP TABLE IF EXISTS msg_offline_message_queue")
    op.create_table(
        "msg_offline_message_queue",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=False),
        sa.Column("target_account_type", sa.String(length=32), nullable=False),
        sa.Column("target_account_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("event_payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_msg_offline_target_status",
        "msg_offline_message_queue",
        ["target_account_type", "target_account_id", "status", "created_at"],
        unique=False,
    )

    op.add_column("msg_message", sa.Column("client_msg_id", sa.String(length=64), nullable=True))
    op.create_unique_constraint(
        "uq_msg_sender_client_msg_id",
        "msg_message",
        ["sender_account_type", "sender_account_id", "client_msg_id"],
    )

    op.create_index("ix_msg_conv_last_message_at", "msg_conversation", ["last_message_at"], unique=False)
    op.create_index("ix_msg_conv_group_status", "msg_conversation", ["group_id", "status"], unique=False)
    op.create_index(
        "ix_msg_cmember_account_left",
        "msg_conversation_member",
        ["account_type", "account_id", "left_at"],
        unique=False,
    )
    op.create_index(
        "ix_msg_cmember_conv_left",
        "msg_conversation_member",
        ["conversation_id", "left_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_msg_cmember_conv_left", table_name="msg_conversation_member")
    op.drop_index("ix_msg_cmember_account_left", table_name="msg_conversation_member")
    op.drop_index("ix_msg_conv_group_status", table_name="msg_conversation")
    op.drop_index("ix_msg_conv_last_message_at", table_name="msg_conversation")
    op.drop_constraint("uq_msg_sender_client_msg_id", "msg_message", type_="unique")
    op.drop_column("msg_message", "client_msg_id")
    op.drop_index("ix_msg_offline_target_status", table_name="msg_offline_message_queue")
    op.drop_table("msg_offline_message_queue")
