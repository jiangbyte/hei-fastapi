from typing import Optional
import datetime

from sqlalchemy import Date, DateTime, Integer, Text
from sqlalchemy.dialects.mysql import VARCHAR, LONGTEXT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class ClientUser(Base):
    __tablename__ = 'client_user'
    __table_args__ = {'comment': 'C端用户'}

    id: Mapped[str] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), primary_key=True, comment='主键')
    account: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='账号')
    password: Mapped[Optional[str]] = mapped_column(VARCHAR(255, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='密码')
    nickname: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='昵称')
    avatar: Mapped[Optional[str]] = mapped_column(LONGTEXT(collation='utf8mb4_general_ci'), comment='头像')
    motto: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='座右铭')
    gender: Mapped[Optional[str]] = mapped_column(VARCHAR(8, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='性别')
    birthday: Mapped[Optional[datetime.date]] = mapped_column(Date, comment='生日')
    email: Mapped[Optional[str]] = mapped_column(VARCHAR(64, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='电子邮箱')
    github: Mapped[Optional[str]] = mapped_column(VARCHAR(64, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='GitHub')
    phone: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='手机号')
    org_id: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='所属组织ID')
    position_id: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='所属职位ID')
    group_id: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='所属用户组ID')
    status: Mapped[Optional[str]] = mapped_column(VARCHAR(16, charset='utf8mb4', collation='utf8mb4_general_ci'), default="ACTIVE", comment='状态')
    last_login_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='最后登录时间')
    last_login_ip: Mapped[Optional[str]] = mapped_column(VARCHAR(64, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='最后登录IP')
    login_count: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment='登录次数')
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='创建时间')
    created_by: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='创建用户')
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, comment='更新时间')
    updated_by: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='更新用户')
