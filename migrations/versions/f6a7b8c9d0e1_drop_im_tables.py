""" Author: Charlie

删除 IM/聊天相关表，仅保留通知、公告、反馈。
"""
from collections.abc import Sequence

from alembic import op

revision: str = "f6a7b8c9d0e1_drop_im_tables"
down_revision: str | Sequence[str] | None = "e5f6a7b8c9d0_webauthn"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_IM_TABLES = (
    "msg_message_read",
    "msg_message_attachment",
    "msg_message",
    "msg_conversation_member",
    "msg_conversation",
    "msg_friend_request",
    "msg_friend",
    "msg_group_join_request",
    "msg_group_member",
    "msg_group",
    "msg_offline_message_queue",
    "msg_terminal",
)


def upgrade() -> None:
    for table in _IM_TABLES:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')


def downgrade() -> None:
    # IM 表结构不再恢复；如需回滚请从历史 revision / 备份还原。
    pass
