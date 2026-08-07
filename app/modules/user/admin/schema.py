""" Author: Charlie """

from datetime import datetime

from pydantic import Field

from app.core.schema.base import ApiSchema
from app.core.schema.common_schema import IdNameResponse
from app.core.schema.wire import WireBool
from app.core.security.transport import PasswordKeyMixin


class AdminProfileResponse(ApiSchema):
    """管理端账户扩展资料响应模型。"""

    account_id: str
    name: str | None = None
    nickname: str | None = None
    avatar: str | None = None
    signature: str | None = None
    phone: str | None = None
    email: str | None = None
    phone_login_enabled: WireBool = False
    email_login_enabled: WireBool = False
    remark: str | None = None
    created_at: datetime | None = Field(default=None, examples=["2026-06-17T12:00:00Z"])
    updated_at: datetime | None = Field(default=None, examples=["2026-06-17T12:00:00Z"])


class AdminProfileUpsertPayload(ApiSchema):
    """管理端账户资料写入载荷。"""

    account_id: str
    name: str | None = None
    nickname: str | None = None
    avatar: str | None = None
    signature: str | None = None
    phone: str | None = None
    email: str | None = None
    remark: str | None = None


class AdminUserCenterProfileUpdateRequest(ApiSchema):
    """当前管理员个人资料更新请求。"""

    name: str | None = Field(default=None, max_length=64)
    nickname: str | None = Field(default=None, max_length=64)
    avatar: str | None = None
    signature: str | None = None
    remark: str | None = None


class AdminUserCenterPasswordUpdateRequest(PasswordKeyMixin):
    """当前管理员修改密码请求。"""

    old_password: str = Field(min_length=1, max_length=512)
    new_password: str = Field(min_length=1, max_length=512)


class AdminUserCenterPhoneUpdateRequest(PasswordKeyMixin):
    """当前管理员手机号绑定更新请求。"""

    password: str = Field(min_length=1, max_length=512)
    phone: str | None = Field(default=None, max_length=32)
    phone_login_enabled: WireBool = False


class AdminUserCenterEmailUpdateRequest(PasswordKeyMixin):
    """当前管理员邮箱绑定更新请求。"""

    password: str = Field(min_length=1, max_length=512)
    email: str | None = Field(default=None, max_length=128)
    email_login_enabled: WireBool = False


class AdminUserCenterOrgInfoResponse(ApiSchema):
    """当前管理员组织信息回显。"""

    role_id_names: list[IdNameResponse] = Field(default_factory=list)
    dept_id_names: list[IdNameResponse] = Field(default_factory=list)
    group_id_names: list[IdNameResponse] = Field(default_factory=list)


class AdminUserCenterAvatarUpdateResponse(ApiSchema):
    """当前管理员头像更新响应。"""

    avatar: str
    file_id: str
    object_name: str
    url: str
