from typing import Optional, List
from modules.sys.role.params import PermissionItem
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
from core.pojo.datetime_mixin import DateTimeValidatorMixin


class UserVO(DateTimeValidatorMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    username: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    motto: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    email: Optional[str] = None
    github: Optional[str] = None
    phone: Optional[str] = None
    org_id: Optional[str] = None
    position_id: Optional[str] = None
    group_id: Optional[str] = None
    org_names: Optional[List[str]] = None
    group_names: Optional[List[str]] = None
    position_name: Optional[str] = None
    status: Optional[str] = None
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    login_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    role_ids: Optional[List[str]] = None


class UserPageParam(BaseModel):
    current: int = 1
    size: int = 10
    keyword: Optional[str] = None
    status: Optional[str] = None


class GrantRoleParam(BaseModel):
    user_id: str
    role_ids: List[str]


class GrantUserPermissionParam(BaseModel):
    user_id: str
    permissions: Optional[List[PermissionItem]] = None


class UpdateProfileParam(BaseModel):
    username: Optional[str] = None
    nickname: Optional[str] = None
    motto: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    email: Optional[str] = None
    github: Optional[str] = None
    phone: Optional[str] = None


class UpdateAvatarParam(BaseModel):
    avatar: str


class UpdatePasswordParam(BaseModel):
    current_password: str
    new_password: str
