from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from core.pojo import PageBounds, BaseExportParam
from core.pojo.datetime_mixin import DateTimeValidatorMixin


class OrgVO(DateTimeValidatorMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    code: str
    name: str
    category: str
    parent_id: Optional[str] = None
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


class GrantOrgRoleParam(BaseModel):
    org_id: str
    role_ids: List[str]
    scope: Optional[str] = None
    custom_scope_group_ids: Optional[str] = None


class OrgTreeVO(BaseModel):
    """Org tree node with children"""
    id: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None
    sort_code: Optional[int] = 0
    children: List["OrgTreeVO"] = []


class OrgTreeParam(BaseModel):
    category: Optional[str] = None


class OrgPageParam(PageBounds):
    parent_id: Optional[str] = None
    keyword: Optional[str] = None


class OrgExportParam(BaseExportParam):
    pass


class OrgImportParam(BaseModel):
    data: List[OrgVO]
