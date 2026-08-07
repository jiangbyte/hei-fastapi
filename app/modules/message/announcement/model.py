"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:51
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base
from app.platform.db.mixins import TimestampMixin
from app.platform.id_generator.snowflake import generate_snowflake_id


class MsgAnnouncement(Base, TimestampMixin):
    __tablename__ = "msg_announcement"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, nullable=False, default=generate_snowflake_id, comment="主键"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="内容")
    content_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="内容格式")
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
    publish_locations: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="发布位置列表"
    )
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="是否置顶")
    pinned_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="置顶截止时间"
    )
    sender_account_type: Mapped[str | None] = mapped_column(String(32), comment="发布者账户类型")
    sender_account_id: Mapped[str | None] = mapped_column(String(64), comment="发布者账户ID")
    status: Mapped[str] = mapped_column(String(32), nullable=False, comment="状态")
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="发布时间")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="撤回时间")
    expire_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="过期时间")
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, comment="查看次数")
    extra: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="扩展信息"
    )


class MsgAnnouncementRead(Base, TimestampMixin):
    __tablename__ = "msg_announcement_read"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, nullable=False, default=generate_snowflake_id, comment="主键"
    )
    announcement_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="公告ID")
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="账户类型")
    account_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="账户ID")
