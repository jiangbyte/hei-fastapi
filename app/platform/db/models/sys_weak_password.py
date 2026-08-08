""" Author: Charlie

弱密码库表模型 — ORM 定义在 platform 层供密码策略查询。
"""
from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base
from app.platform.db.mixins import TimestampMixin
from app.platform.id_generator.snowflake import generate_snowflake_id


class SysWeakPassword(Base, TimestampMixin):
    """弱密码库，存储禁止使用的明文密码值。"""

    __tablename__ = "sys_weak_password"
    __table_args__ = (Index("idx_sys_weak_password_password", "password", unique=True),)

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=generate_snowflake_id,
        comment="主键",
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="弱密码值")
