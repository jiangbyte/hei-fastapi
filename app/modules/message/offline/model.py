""" Author: Charlie

离线消息队列，IM 重连 (WS/TCP) 时投递。
"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base
from app.platform.id_generator.snowflake import generate_snowflake_id


class MsgOfflineQueue(Base):
    __tablename__ = "msg_offline_message_queue"
    __table_args__ = (
        Index(
            "ix_msg_offline_target_status",
            "target_account_type",
            "target_account_id",
            "status",
            "created_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_snowflake_id)
    message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    conversation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    event_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
