""" Author: Charlie

ORM 通用混入：为模型提供审计时间戳与数据范围部门归属字段。

TimestampMixin 的审计人由 audit 钩子自动注入，OwnerDeptMixin 供数据范围过滤复用。
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """审计时间戳混入：创建/更新时间与创建/更新人。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="创建人")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )
    updated_by: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="更新人")


class OwnerDeptMixin:
    """可选部门归属字段，用于 DEPT / DEPT_AND_CHILD / CUSTOM 数据范围。"""

    owner_dept_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="所属部门ID（数据范围）",
    )
