"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:48
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base
from app.platform.db.mixins import TimestampMixin
from app.platform.id_generator.snowflake import generate_snowflake_id


class MsgTerminal(Base, TimestampMixin):
    __tablename__ = "msg_terminal"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, nullable=False, default=generate_snowflake_id, comment="主键"
    )
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="账户类型")
    account_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="账户ID")
    device_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="设备类型")
    device_name: Mapped[str | None] = mapped_column(String(128), comment="设备名称")
    device_id: Mapped[str | None] = mapped_column(String(255), comment="设备唯一标识")
    push_token: Mapped[str | None] = mapped_column(String(500), comment="推送Token")
    push_provider: Mapped[str | None] = mapped_column(String(32), comment="推送渠道")
    app_version: Mapped[str | None] = mapped_column(String(32), comment="App版本号")
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="是否在线")
    last_online_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="最后在线时间"
    )
    last_login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="最后登录时间"
    )
    extra: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, comment="扩展信息"
    )
