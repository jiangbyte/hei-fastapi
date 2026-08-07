""" Author: Charlie

由 HEI 代码生成器生成。
Author: jiangbyte
"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base
from app.platform.db.mixins import TimestampMixin
from app.platform.id_generator.snowflake import generate_snowflake_id


class MsgFeedback(Base, TimestampMixin):
    __tablename__ = "msg_feedback"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, nullable=False, default=generate_snowflake_id, comment="主键"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="反馈内容")
    category: Mapped[str] = mapped_column(String(64), nullable=False, comment="反馈分类")
    contact: Mapped[str | None] = mapped_column(String(255), comment="联系方式")
    attach_urls: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="附件URL列表"
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, comment="状态")
    reply: Mapped[str | None] = mapped_column(Text, comment="管理员回复")
    replied_by: Mapped[str | None] = mapped_column(String(64), comment="回复人ID")
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="回复时间")
    submitter_account_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="提交者账户类型"
    )
    submitter_account_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="提交者账户ID"
    )
