from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from core.enums import DataScopeEnum
from core.pojo import PageBounds, BaseExportParam
from core.pojo.datetime_mixin import DateTimeValidatorMixin


class RoleVO(DateTimeValidatorMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    code: str
    name: str
    category: str
    description: Optional[str] = None
    status: Optional[str] = None
    sort_code: Optional[int] = 0
    extra: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_name: Optional[str] = None


class RolePageParam(PageBounds):
    pass


class RoleExportParam(BaseExportParam):
    pass


class RoleImportParam(BaseModel):
    data: List[RoleVO]


class PermissionItem(BaseModel):
    permission_code: str
    scope: str = DataScopeEnum.ALL.value
    custom_scope_group_ids: Optional[str] = None
    custom_scope_org_ids: Optional[str] = None


class GrantPermissionParam(BaseModel):
    role_id: str
    permissions: List[PermissionItem]


class ButtonPermissionScope(BaseModel):
    permission_code: str
    scope: str = DataScopeEnum.ALL.value
    custom_scope_group_ids: Optional[str] = None
    custom_scope_org_ids: Optional[str] = None


class GrantResourceParam(BaseModel):
    role_id: str
    resource_ids: List[str]
    permissions: List[ButtonPermissionScope] = []
