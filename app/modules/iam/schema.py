""" Author: Charlie """

from datetime import datetime

from pydantic import Field

from app.core.config.enums import AccountStatusEnum, AccountType, DataScope
from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireBool
from app.modules.iam.enums import AccountIdentityBindStatus, AccountIdentityType


class AccountIdentitySchema(ApiSchema):
    id: str | None = None
    account_id: str | None = None
    identity_type: AccountIdentityType
    identifier: str = Field(min_length=1, max_length=128)
    verified: WireBool = False
    is_primary: WireBool = False
    bind_status: AccountIdentityBindStatus = AccountIdentityBindStatus.BOUND
    created_at: datetime | None = None
    created_by: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None


class SysAccountSchema(ApiSchema):
    id: str
    account: str
    account_type: AccountType
    account_status: AccountStatusEnum
    name: str | None = None
    nickname: str | None = None
    avatar: str | None = None
    signature: str | None = None
    phone: str | None = None
    email: str | None = None
    email_login_enabled: WireBool = False
    phone_login_enabled: WireBool = False
    email_identity: str | None = None
    phone_identity: str | None = None
    email_identity_verified: WireBool = False
    phone_identity_verified: WireBool = False
    email_identity_bind_status: AccountIdentityBindStatus | None = None
    phone_identity_bind_status: AccountIdentityBindStatus | None = None
    identities: list[AccountIdentitySchema] = Field(default_factory=list)
    bio: str | None = None
    level: str | None = None
    remark: str | None = None
    cancelled_at: datetime | None = Field(default=None, examples=["2026-06-18T12:00:00Z"])
    cancelled_by: str | None = None
    cancel_reason: str | None = None
    last_login_ip: str | None = None
    last_login_address: str | None = None
    last_login_time: datetime | None = None
    last_login_device: str | None = None
    latest_login_ip: str | None = None
    latest_login_address: str | None = None
    latest_login_time: datetime | None = None
    latest_login_device: str | None = None
    created_at: datetime = Field(examples=["2026-06-18T12:00:00Z"])
    created_by: str | None = None
    updated_at: datetime = Field(examples=["2026-06-18T12:00:00Z"])
    updated_by: str | None = None


class RoleOption(ApiSchema):
    id: str
    code: str
    name: str
    status: str


class ResourcePermissionOption(ApiSchema):
    id: str
    permission_key: str
    title: str
    data_scope: DataScope = DataScope.SELF


class ResourceGrantMenuOption(ApiSchema):
    id: str
    module_id: str
    parent_id: str | None = None
    parent_id_name: str
    title: str
    button: list[ResourcePermissionOption] = Field(default_factory=list)


class ResourceGrantModuleOption(ApiSchema):
    id: str
    title: str
    menu: list[ResourceGrantMenuOption] = Field(default_factory=list)


class PermissionRegistryItem(ApiSchema):
    permission_key: str
    name: str
    method: str | None = None
    path: str | None = None
