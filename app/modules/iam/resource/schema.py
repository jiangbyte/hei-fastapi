from datetime import datetime

from pydantic import Field

from app.core.config.enums import DataScope, StatusEnum
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema
from app.modules.iam.enums import ResourceModuleClient, ResourceType


class ResourceCreateRequest(ApiSchema):
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
    sort: int = 99
    is_visible: bool = True
    is_cache: bool = False
    is_affix: bool = False
    status: StatusEnum = StatusEnum.ENABLED
    description: str | None = None
    layout: str | None = Field(default=None, max_length=255)
    extra: dict = Field(default_factory=dict)


class ResourceUpdateRequest(ResourceCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class ResourceAdminPageQuery(PageQuery):
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=64)
    resource_type: ResourceType | None = None
    module_id: str | None = Field(default=None, max_length=64)
    module_client: ResourceModuleClient | None = None
    parent_id: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, max_length=32)


class ResourceButtonPageQuery(PageQuery):
    parent_id: str = Field(min_length=1, max_length=64)
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, max_length=32)


class SysResourceSchema(ApiSchema):
    id: str
    parent_id: str | None = None
    code: str
    name: str
    resource_type: ResourceType
    module_id: str | None = None
    module_id_name: str | None = None
    module_client: ResourceModuleClient | None = None
    path: str | None = None
    component: str | None = None
    redirect: str | None = None
    icon: str | None = None
    color: str | None = None
    href: str | None = None
    sort: int
    is_visible: bool
    is_cache: bool
    is_affix: bool
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



class ResourcePermissionBindRequest(ApiSchema):
    resource_id: str
    permission_key: str
    data_scope: DataScope = DataScope.SELF
    custom_scope_dept_ids: list[str] = Field(default_factory=list)
    sort: int = 99
    description: str | None = None


class ResourceButtonCreateRequest(ApiSchema):
    parent_id: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=64)
    permission_key: str = Field(min_length=1, max_length=128)
    data_scope: DataScope = DataScope.SELF
    custom_scope_dept_ids: list[str] = Field(default_factory=list)
    sort: int = 99
    status: StatusEnum = StatusEnum.ENABLED
    description: str | None = None


class ResourceButtonUpdateRequest(ResourceButtonCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class SysResourcePermissionRelSchema(ApiSchema):
    id: str
    resource_id: str
    permission_key: str
    data_scope: DataScope
    custom_scope_dept_ids: list[str]
    sort: int
    status: str
    description: str | None = None
    created_at: datetime
    created_by: str | None = None
    created_name: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    updated_name: str | None = None


class ResourceButtonSchema(SysResourceSchema):
    permission_rel_id: str | None = None
    permission_key: str | None = None
    data_scope: DataScope | None = None
    custom_scope_dept_ids: list[str] = Field(default_factory=list)
    permission_description: str | None = None


class ResourceTreeNode(SysResourceSchema):
    children: list["ResourceTreeNode"] = Field(default_factory=list)


class ResourceTreeQuery(ApiSchema):
    module_id: str | None = Field(default=None, max_length=64)
    module_client: ResourceModuleClient | None = None


class ResourceModuleSelectorQuery(ApiSchema):
    client: ResourceModuleClient | None = None


class ResourceModuleCreateRequest(ApiSchema):
    name: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=64)
    client: ResourceModuleClient = ResourceModuleClient.ADMIN
    icon: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=32)
    sort: int = 99
    status: StatusEnum = StatusEnum.ENABLED
    description: str | None = None
    extra: dict = Field(default_factory=dict)


class ResourceModuleUpdateRequest(ResourceModuleCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class ResourceModuleAdminPageQuery(PageQuery):
    name: str | None = Field(default=None, max_length=64)
    code: str | None = Field(default=None, max_length=64)
    client: ResourceModuleClient | None = None
    status: str | None = Field(default=None, max_length=32)


class SysResourceModuleSchema(ApiSchema):
    id: str
    name: str
    code: str
    client: ResourceModuleClient
    icon: str | None = None
    color: str | None = None
    sort: int
    status: str
    description: str | None = None
    extra: dict
    created_at: datetime
    created_by: str | None = None
    created_name: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    updated_name: str | None = None


class ResourceModuleSelectorOption(ApiSchema):
    id: str
    name: str
    code: str
    client: ResourceModuleClient
    icon: str | None = None
    color: str | None = None
