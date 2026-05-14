from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from core.pojo import PageBounds, BaseExportParam
from core.pojo.datetime_mixin import DateTimeValidatorMixin


class ModuleVO(DateTimeValidatorMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    code: str
    name: str
    category: str
    icon: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    is_visible: Optional[str] = None
    status: Optional[str] = None
    sort_code: Optional[int] = 0
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_name: Optional[str] = None


class ResourceVO(DateTimeValidatorMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    route_path: Optional[str] = None
    component_path: Optional[str] = None
    redirect_path: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_visible: Optional[str] = None
    is_cache: Optional[str] = None
    is_affix: Optional[str] = None
    is_breadcrumb: Optional[str] = None
    external_url: Optional[str] = None
    extra: Optional[str] = None
    status: Optional[str] = None
    sort_code: Optional[int] = 0
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_name: Optional[str] = None


class ResourcePageParam(PageBounds):
    pass


class ResourceExportParam(BaseExportParam):
    pass


class ResourceImportParam(BaseModel):
    data: List[ResourceVO]

class ModulePageParam(PageBounds):
    pass


class ModuleExportParam(BaseExportParam):
    pass


class ModuleImportParam(BaseModel):
    data: List[ModuleVO]
