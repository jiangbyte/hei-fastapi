from typing import Optional, List
import datetime

from sqlalchemy import Date, DateTime, Index, Integer, Text
from sqlalchemy.dialects.mysql import VARCHAR, LONGTEXT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class SysUser(Base):
    __tablename__ = 'sys_user'
    __table_args__ = (
        Index('idx_username', 'username'),
        {'comment': '用户'}
    )

    id: Mapped[str] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), primary_key=True, comment='主键')
    username: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), comment='用户名')
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


class RelUserRole(Base):
    __tablename__ = 'rel_user_role'
    __table_args__ = (
        Index('uk_user_role', 'user_id', 'role_id', unique=True),
        Index('idx_role_id', 'role_id'),
        {'comment': '用户-角色关联'}
    )

    id: Mapped[str] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), primary_key=True, comment='主键')
    user_id: Mapped[str] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), nullable=False, comment='用户ID')
    role_id: Mapped[str] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), nullable=False, comment='角色ID')

class RelUserPermission(Base):
    __tablename__ = 'rel_user_permission'
    __table_args__ = (
        Index('uk_user_permission', 'user_id', 'permission_code', unique=True),
        Index('idx_permission_code', 'permission_code'),
        {'comment': '用户-权限直关联'}
    )

    id: Mapped[str] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), primary_key=True, comment='主键')
    user_id: Mapped[str] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), nullable=False, comment='用户ID')
    permission_code: Mapped[str] = mapped_column(VARCHAR(255, charset='utf8mb4', collation='utf8mb4_general_ci'), nullable=False, comment='权限编码')
    scope: Mapped[Optional[str]] = mapped_column(VARCHAR(32, charset='utf8mb4', collation='utf8mb4_general_ci'), default="ALL", comment='数据范围：ALL-全部，SELF-本人，ORG-本组织，ORG_AND_BELOW-本组织及以下，CUSTOM_ORG-自定义组织，GROUP-本用户组，GROUP_AND_BELOW-本用户组及以下，CUSTOM_GROUP-自定义用户组')
    custom_scope_group_ids: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_general_ci'), comment='自定义用户组ID列表(JSON数组)，scope=CUSTOM_GROUP时生效')
    custom_scope_org_ids: Mapped[Optional[str]] = mapped_column(Text(collation='utf8mb4_general_ci'), comment='自定义组织ID列表(JSON数组)，scope=CUSTOM_ORG时生效')

