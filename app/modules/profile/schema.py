""" Author: Charlie

账户资料公共响应模型：管理端与门户端的「我的信息」响应。
"""

from datetime import datetime

from pydantic import Field

from app.core.config.enums import AccountType
from app.core.schema.base import ApiSchema
from app.core.schema.common_schema import IdNameResponse
from app.core.schema.wire import WireBool
from app.modules.profile.admin.schema import ProfileUserAdminResponse
from app.modules.profile.identity.schema import IdentityStatusResponse
from app.modules.profile.portal.schema import ProfileUserPortalResponse


class BindTargetRequest(ApiSchema):
    """发送绑定验证码的目标地址（邮箱或手机号）。"""

    target: str = Field(min_length=3, max_length=128)


class AdminMeResponse(ApiSchema):
    """管理端当前登录账户信息响应模型。"""

    account_id: str
    account: str
    account_type: AccountType
    nickname: str | None = None
    avatar: str | None = None
    role_ids: list[str]
    dept_ids: list[str]
    group_ids: list[str]
    role_id_names: list[IdNameResponse] = Field(default_factory=list)
    dept_id_names: list[IdNameResponse] = Field(default_factory=list)
    group_id_names: list[IdNameResponse] = Field(default_factory=list)
    permission_keys: list[str]
    password_expired: WireBool = False
    force_bind_email: WireBool = False
    force_bind_phone: WireBool = False
    force_bind_identity: WireBool = False
    identity: IdentityStatusResponse | None = None
    profile: ProfileUserAdminResponse


class PortalMeResponse(ApiSchema):
    """门户端当前登录账户信息响应模型。"""

    account_id: str
    account: str
    account_type: AccountType
    nickname: str | None = None
    avatar: str | None = None
    role_ids: list[str] = Field(default_factory=list)
    dept_ids: list[str] = Field(default_factory=list)
    group_ids: list[str] = Field(default_factory=list)
    role_id_names: list[IdNameResponse] = Field(default_factory=list)
    dept_id_names: list[IdNameResponse] = Field(default_factory=list)
    group_id_names: list[IdNameResponse] = Field(default_factory=list)
    permission_keys: list[str] = Field(default_factory=list)
    password_expired: WireBool = False
    force_bind_email: WireBool = False
    force_bind_phone: WireBool = False
    force_bind_identity: WireBool = False
    identity: IdentityStatusResponse | None = None
    profile: ProfileUserPortalResponse
