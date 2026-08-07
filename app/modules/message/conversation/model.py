"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:54
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base
from app.platform.db.mixins import TimestampMixin
from app.platform.id_generator.snowflake import generate_snowflake_id


class MsgConversation(Base, TimestampMixin):
    __tablename__ = "msg_conversation"
    __table_args__ = (
        Index("ix_msg_conv_last_message_at", "last_message_at"),
        Index("ix_msg_conv_group_status", "group_id", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, nullable=False, default=generate_snowflake_id, comment="主键"
    )
    conversation_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="会话类型 DIRECT/GROUP"
    )
    title: Mapped[str | None] = mapped_column(String(255), comment="会话标题")
    avatar: Mapped[str | None] = mapped_column(String(500), comment="会话头像")
    group_id: Mapped[str | None] = mapped_column(String(64), comment="关联群ID")
    owner_account_type: Mapped[str | None] = mapped_column(String(32), comment="创建者账户类型")
    owner_account_id: Mapped[str | None] = mapped_column(String(64), comment="创建者账户ID")
    status: Mapped[str] = mapped_column(String(32), nullable=False, comment="状态")
    last_message_id: Mapped[str | None] = mapped_column(String(64), comment="最新消息ID")
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="最新消息时间"
    )
    extra: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="扩展信息"
    )


class MsgConversationMember(Base, TimestampMixin):
    __tablename__ = "msg_conversation_member"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id", "account_type", "account_id", name="uq_conversation_member"
        ),
        Index("ix_msg_cmember_account_left", "account_type", "account_id", "left_at"),
        Index("ix_msg_cmember_conv_left", "conversation_id", "left_at"),
    )

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, nullable=False, default=generate_snowflake_id, comment="主键"
    )
    conversation_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="会话ID")
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="账户类型")
    account_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="账户ID")
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default="MEMBER", comment="角色 OWNER/MEMBER"
    )
    unread_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="未读消息数"
    )
    last_read_message_id: Mapped[str | None] = mapped_column(String(64), comment="最后已读消息ID")
    last_read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="最后已读时间"
    )
    last_delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="最后投递时间"
    )
    is_muted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否免打扰"
    )
    is_pinned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否置顶"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="加入时间"
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="离开时间")
    extra: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="扩展信息"
    )
