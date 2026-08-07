"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:52
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base
from app.platform.db.mixins import TimestampMixin
from app.platform.id_generator.snowflake import generate_snowflake_id


class MsgGroup(Base, TimestampMixin):
    __tablename__ = "msg_group"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, nullable=False, default=generate_snowflake_id, comment="主键"
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="群名称")
    avatar: Mapped[str | None] = mapped_column(String(500), comment="群头像")
    description: Mapped[str | None] = mapped_column(Text, comment="群简介")
    owner_account_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="群主账户类型"
    )
    owner_account_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="群主账户ID")
    status: Mapped[str] = mapped_column(String(32), nullable=False, comment="状态")
    join_mode: Mapped[str] = mapped_column(String(32), nullable=False, comment="入群方式")
    max_members: Mapped[int] = mapped_column(Integer, nullable=False, comment="最大成员数")
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, comment="当前成员数")
    extra: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="扩展信息"
    )


class MsgGroupMember(Base):
    __tablename__ = "msg_group_member"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, nullable=False, default=generate_snowflake_id, comment="主键"
    )
    group_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="群ID")
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="账户类型")
    account_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="账户ID")
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="MEMBER", comment="角色")
    nickname: Mapped[str | None] = mapped_column(String(64), comment="群内昵称")
    is_muted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否免打扰"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="加入时间"
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="离开时间")
    extra: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="扩展信息"
    )


class MsgGroupJoinRequest(Base, TimestampMixin):
    __tablename__ = "msg_group_join_request"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, nullable=False, default=generate_snowflake_id, comment="主键"
    )
    group_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="群ID")
    applicant_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="申请人账户类型"
    )
    applicant_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="申请人账户ID")
    message: Mapped[str | None] = mapped_column(Text, comment="申请附言")
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING", comment="状态"
    )
    handled_by_type: Mapped[str | None] = mapped_column(String(32), comment="处理人账户类型")
    handled_by_id: Mapped[str | None] = mapped_column(String(64), comment="处理人账户ID")
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="处理时间")
