"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:50
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base
from app.platform.db.mixins import TimestampMixin
from app.platform.id_generator.snowflake import generate_snowflake_id


class MsgNotification(Base, TimestampMixin):
    __tablename__ = "msg_notification"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, nullable=False, default=generate_snowflake_id, comment="主键"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="内容")
    content_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="内容格式")
    category: Mapped[str] = mapped_column(String(32), nullable=False, comment="分类")
    severity: Mapped[str] = mapped_column(String(32), nullable=False, comment="等级")
    target_scope: Mapped[str] = mapped_column(String(32), nullable=False, comment="目标范围")
    target_account_types: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="目标账户类型列表"
    )
    target_account_ids: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="目标账户ID列表"
    )
    target_dept_ids: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="目标部门ID列表"
    )
    target_role_ids: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="目标角色ID列表"
    )
    sender_account_type: Mapped[str | None] = mapped_column(String(32), comment="发送者账户类型")
    sender_account_id: Mapped[str | None] = mapped_column(String(64), comment="发送者账户ID")
    source_type: Mapped[str | None] = mapped_column(String(64), comment="来源模块")
    source_id: Mapped[str | None] = mapped_column(String(64), comment="来源业务ID")
    status: Mapped[str] = mapped_column(String(32), nullable=False, comment="状态")
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="发布时间")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="撤回时间")
    extra: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="扩展信息"
    )


class MsgNotificationRead(Base):
    __tablename__ = "msg_notification_read"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, nullable=False, default=generate_snowflake_id, comment="主键"
    )
    notification_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="通知ID")
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="账户类型")
    account_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="账户ID")
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now, comment="阅读时间"
    )

    __table_args__ = (
        UniqueConstraint(
            "notification_id", "account_type", "account_id", name="uq_msg_notification_read_account"
        ),
    )
