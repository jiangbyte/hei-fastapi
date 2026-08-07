""" Author: Charlie

MsgMessage - 聊天消息，不可变（仅可撤回）。
"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base
from app.platform.id_generator.snowflake import generate_snowflake_id


class MsgMessage(Base):
    """聊天消息，不可编辑，仅可撤回 (is_revoked)。
    不继承 TimestampMixin — 仅需 created_at（无 updated）。"""

    __tablename__ = "msg_message"
    __table_args__ = (
        Index("ix_msg_msg_conv_created", "conversation_id", "created_at"),
        Index("ix_msg_msg_parent", "parent_id"),
        Index("ix_msg_msg_sender", "sender_account_type", "sender_account_id"),
        UniqueConstraint(
            "sender_account_type",
            "sender_account_id",
            "client_msg_id",
            name="uq_msg_sender_client_msg_id",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_snowflake_id)
    conversation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    client_msg_id: Mapped[str | None] = mapped_column(String(64))
    msg_type: Mapped[str] = mapped_column(String(32), default="TEXT", nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(64))
    sender_type: Mapped[str] = mapped_column(String(32), default="USER", nullable=False)
    sender_account_type: Mapped[str | None] = mapped_column(String(32))
    sender_account_id: Mapped[str | None] = mapped_column(String(64))
    sender_name: Mapped[str | None] = mapped_column(String(128))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(32), default="TEXT", nullable=False)
    reply_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MsgMessageRead(Base):
    """按账户、会话、终端的游标式已读追踪。"""

    __tablename__ = "msg_message_read"
    __table_args__ = (
        Index("ix_msg_mread_account", "account_type", "account_id"),
        # 游标 UniqueConstraint：每个 conversation+account+terminal 一条
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_snowflake_id)
    conversation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    last_read_message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    last_read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    terminal_id: Mapped[str | None] = mapped_column(String(64))


class MsgMessageAttachment(Base):
    """消息附件，关联 sys_file 存储原始文件。"""

    __tablename__ = "msg_message_attachment"
    __table_args__ = (Index("ix_msg_mattach_message", "message_id", "sort"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_snowflake_id)
    message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    file_id: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128))
    size: Mapped[int | None] = mapped_column(Integer)
    attachment_type: Mapped[str] = mapped_column(String(32), default="FILE", nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024))
    duration: Mapped[int | None] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extra: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
