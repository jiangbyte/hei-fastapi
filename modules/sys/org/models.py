from typing import Optional
import datetime

from sqlalchemy import DateTime, Index, Integer, Text
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class SysOrg(Base):
    __tablename__ = 'sys_org'
    __table_args__ = (
        Index('uk_code', 'code', unique=True),
        {'comment': '组织'}
    )

    id: Mapped[str] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), primary_key=True, comment='主键')
    code: Mapped[str] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), nullable=False, comment='组织编码')
    name: Mapped[str] = mapped_column(VARCHAR(64, charset='utf8mb4', collation='utf8mb4_general_ci'), nullable=False, comment='组织名称')
    category: Mapped[str] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), nullable=False, comment='组织类别')
    parent_id: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='父组织ID')
    description: Mapped[Optional[str]] = mapped_column(VARCHAR(500, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='组织描述')
    status: Mapped[Optional[str]] = mapped_column(VARCHAR(16, charset='utf8mb4', collation='utf8mb4_general_ci'), default="ENABLED", comment='状态')
    sort_code: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment='排序')
    extra: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_general_ci'), comment='扩展信息')
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    created_by: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='创建用户')
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    updated_by: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='更新用户')
