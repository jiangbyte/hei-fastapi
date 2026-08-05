from datetime import datetime

from pydantic import Field

from app.core.config.enums import AccountStatusEnum, AccountType
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema
from app.modules.iam.enums import AccountIdentityBindStatus, AccountIdentityType
from app.modules.iam.schema import (
    AccountIdentitySchema as AccountIdentitySchema,
)
from app.modules.iam.schema import (
    ResourceGrantModuleOption,
    RoleOption,
)
from app.modules.iam.schema import (
    SysAccountSchema as SysAccountSchema,
)


class AccountIdentityUpsertPayload(ApiSchema):
    account_id: str
    identity_type: AccountIdentityType
    identifier: str = Field(min_length=1, max_length=128)
    verified: bool = False
    is_primary: bool = False
    bind_status: AccountIdentityBindStatus = AccountIdentityBindStatus.BOUND


class AccountCreateRequest(ApiSchema):
    account: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=512)
    password_key_id: str | None = Field(default=None, max_length=64)
    account_type: AccountType
    account_status: AccountStatusEnum = AccountStatusEnum.ENABLED
    name: str | None = Field(default=None, max_length=64)
    nickname: str | None = Field(default=None, max_length=64)
    avatar: str | None = None
    signature: str | None = None
    phone: str | None = None
    email: str | None = None
    email_login_enabled: bool = False
    phone_login_enabled: bool = False
    email_identity: str | None = Field(default=None, max_length=128)
    phone_identity: str | None = Field(default=None, max_length=32)
    email_identity_verified: bool = False
    phone_identity_verified: bool = False
    email_identity_bind_status: AccountIdentityBindStatus = AccountIdentityBindStatus.BOUND
    phone_identity_bind_status: AccountIdentityBindStatus = AccountIdentityBindStatus.BOUND
    bio: str | None = Field(default=None, max_length=255)
    level: str | None = Field(default=None, max_length=32)
    remark: str | None = None


class AccountUpdateRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    account: str = Field(min_length=3, max_length=64)
    password: str | None = Field(default=None, min_length=1, max_length=512)
    password_key_id: str | None = Field(default=None, max_length=64)
    account_type: AccountType
    account_status: AccountStatusEnum = AccountStatusEnum.ENABLED
    name: str | None = Field(default=None, max_length=64)
    nickname: str | None = Field(default=None, max_length=64)
    avatar: str | None = None
    signature: str | None = None
    phone: str | None = None
    email: str | None = None
    email_login_enabled: bool = False
    phone_login_enabled: bool = False
    email_identity: str | None = Field(default=None, max_length=128)
    phone_identity: str | None = Field(default=None, max_length=32)
    email_identity_verified: bool = False
    phone_identity_verified: bool = False
    email_identity_bind_status: AccountIdentityBindStatus = AccountIdentityBindStatus.BOUND
    phone_identity_bind_status: AccountIdentityBindStatus = AccountIdentityBindStatus.BOUND
    bio: str | None = Field(default=None, max_length=255)
    level: str | None = Field(default=None, max_length=32)
    remark: str | None = None


class AccountCancelPayload(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    cancel_reason: str | None = None


class AccountAdminPageQuery(PageQuery):
    account: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=64)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=128)
    account_type: AccountType | None = None
    account_status: AccountStatusEnum | None = None


class AccountRoleAssignRequest(ApiSchema):
    account_id: str
    role_id: str


class AccountGroupAssignRequest(ApiSchema):
    account_id: str
    group_id: str


class AccountDeptAssignRequest(ApiSchema):
    account_id: str
    dept_id: str
    is_primary: bool = False


class AccountGroupOption(ApiSchema):
    id: str
    name: str
    status: str


class AccountDeptGrantInfo(ApiSchema):
    dept_id: str
    is_primary: bool = False


class AccountResourceGrantInfo(ApiSchema):
    resource_id: str = Field(min_length=1, max_length=64)
    permission_keys: list[str] = Field(default_factory=list)


class SysAccountRoleRelSchema(ApiSchema):
    id: str
    account_id: str
    role_id: str
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None


class SysAccountGroupRelSchema(ApiSchema):
    id: str
    account_id: str
    group_id: str
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None


class SysAccountDeptRelSchema(ApiSchema):
    id: str
    account_id: str
    dept_id: str
    is_primary: bool
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None


class AccountOwnResourceResponse(ApiSchema):
    id: str
    modules: list[ResourceGrantModuleOption] = Field(default_factory=list)
    grant_info_list: list[AccountResourceGrantInfo] = Field(default_factory=list)


class AccountGrantResourceRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    grant_info_list: list[AccountResourceGrantInfo] = Field(default_factory=list)


class AccountOwnRoleResponse(ApiSchema):
    id: str
    roles: list[RoleOption] = Field(default_factory=list)
    role_ids: list[str] = Field(default_factory=list)


class AccountGrantRoleRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    role_ids: list[str] = Field(default_factory=list)


class AccountOwnGroupResponse(ApiSchema):
    id: str
    groups: list[AccountGroupOption] = Field(default_factory=list)
    group_ids: list[str] = Field(default_factory=list)


class AccountGrantGroupRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    group_ids: list[str] = Field(default_factory=list)


class AccountOwnDeptResponse(ApiSchema):
    id: str
    grant_info_list: list[AccountDeptGrantInfo] = Field(default_factory=list)


class AccountGrantDeptRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    grant_info_list: list[AccountDeptGrantInfo] = Field(default_factory=list)
