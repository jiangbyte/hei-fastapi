from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
from core.pojo import PageBounds, BaseExportParam
from core.pojo.datetime_mixin import DateTimeValidatorMixin


class ClientUserVO(DateTimeValidatorMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    account: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    motto: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    email: Optional[str] = None
    github: Optional[str] = None
    status: Optional[str] = None
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    login_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_name: Optional[str] = None


class ClientUserPageParam(PageBounds):
    keyword: Optional[str] = None
    status: Optional[str] = None


class UpdateProfileParam(BaseModel):
    nickname: Optional[str] = None
    motto: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    email: Optional[str] = None
    github: Optional[str] = None


class UpdateAvatarParam(BaseModel):
    avatar: str


class UpdatePasswordParam(BaseModel):
    current_password: str
    new_password: str


class ClientUserExportParam(BaseExportParam):
    pass


class ClientUserImportParam(BaseModel):
    data: List[ClientUserVO]
