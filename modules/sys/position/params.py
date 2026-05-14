from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from core.pojo import PageBounds, BaseExportParam
from core.pojo.datetime_mixin import DateTimeValidatorMixin


class PositionVO(DateTimeValidatorMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    code: str
    name: str
    category: str
    org_id: Optional[str] = None
    group_id: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    sort_code: Optional[int] = 0
    org_names: Optional[List[str]] = None
    group_names: Optional[List[str]] = None
    extra: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_name: Optional[str] = None


class PositionPageParam(PageBounds):
    keyword: Optional[str] = None
    group_id: Optional[str] = None
    org_id: Optional[str] = None


class PositionExportParam(BaseExportParam):
    pass


class PositionImportParam(BaseModel):
    data: List[PositionVO]
