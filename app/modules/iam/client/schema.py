""" Author: Charlie """

from datetime import datetime

from pydantic import Field

from app.core.config.enums import AccountType, DataScope, StatusEnum
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireBool, WireInt
from app.modules.iam.enums import ResourceType


class ClientModuleCreateRequest(ApiSchema):
    name: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=64)
    account_type: AccountType = AccountType.ADMIN
    icon: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=32)
    sort: WireInt = 99
    status: StatusEnum = StatusEnum.ENABLED
    description: str | None = None
    extra: dict = Field(default_factory=dict)


class ClientModuleUpdateRequest(ClientModuleCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class ClientModuleAdminPageQuery(PageQuery):
    name: str | None = Field(default=None, max_length=64)
    code: str | None = Field(default=None, max_length=64)
    account_type: AccountType | None = None
    status: str | None = Field(default=None, max_length=32)


class ClientModuleSelectorQuery(ApiSchema):
    account_type: AccountType | None = None


class SysClientModuleSchema(ApiSchema):
    id: str
    name: str
    code: str
    account_type: AccountType
    icon: str | None = None
    color: str | None = None
    sort: WireInt
    status: str
    description: str | None = None
    extra: dict
    created_at: datetime
    created_by: str | None = None
    created_name: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    updated_name: str | None = None


class ClientModuleSelectorOption(ApiSchema):
    id: str
    name: str
    code: str
    account_type: AccountType
    icon: str | None = None
    color: str | None = None
    sort: WireInt


class ClientResourceCreateRequest(ApiSchema):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=64)
    resource_type: ResourceType
    parent_id: str | None = Field(default=None, max_length=64)
    module_id: str | None = Field(default=None, max_length=64)
    path: str | None = Field(default=None, max_length=255)
    component: str | None = Field(default=None, max_length=255)
    redirect: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=32)
    href: str | None = Field(default=None, max_length=255)
    sort: WireInt = 99
    is_visible: WireBool = True
    is_cache: WireBool = False
    is_affix: WireBool = False
    status: StatusEnum = StatusEnum.ENABLED
    description: str | None = None
    layout: str | None = Field(default=None, max_length=255)
    extra: dict = Field(default_factory=dict)


class ClientResourceUpdateRequest(ClientResourceCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class ClientResourceAdminPageQuery(PageQuery):
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=64)
    resource_type: ResourceType | None = None
    module_id: str | None = Field(default=None, max_length=64)
    parent_id: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, max_length=32)


class ClientResourceTreeQuery(ApiSchema):
    module_id: str | None = Field(default=None, max_length=64)
    account_type: AccountType | None = None


class SysClientResourceSchema(ApiSchema):
    id: str
    parent_id: str | None = None
    code: str
    name: str
    resource_type: ResourceType
    module_id: str | None = None
    module_id_name: str | None = None
    account_type: AccountType | None = None
    path: str | None = None
    component: str | None = None
    redirect: str | None = None
    icon: str | None = None
    color: str | None = None
    href: str | None = None
    sort: WireInt
    is_visible: WireBool
    is_cache: WireBool
    is_affix: WireBool
    status: str
    description: str | None = None
    layout: str | None = None
    extra: dict
    created_at: datetime
    created_by: str | None = None
    created_name: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    updated_name: str | None = None


class ClientResourceTreeNode(SysClientResourceSchema):
    children: list["ClientResourceTreeNode"] = Field(default_factory=list)


class ClientResourcePermissionBindRequest(ApiSchema):
    resource_id: str
    permission_key: str
    account_type: AccountType = AccountType.ADMIN
    data_scope: DataScope = DataScope.SELF
    custom_scope_dept_ids: list[str] = Field(default_factory=list)
    sort: WireInt = 99
    description: str | None = None


class SysClientResourcePermissionRelSchema(ApiSchema):
    id: str
    resource_id: str
    permission_key: str
    data_scope: DataScope
    custom_scope_dept_ids: list[str]
    sort: WireInt
    status: str
    description: str | None = None
    created_at: datetime
    created_by: str | None = None
    created_name: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    updated_name: str | None = None


class ClientResourceGrantInfo(ApiSchema):
    resource_id: str = Field(min_length=1, max_length=64)
    permission_keys: list[str] = Field(default_factory=list)
