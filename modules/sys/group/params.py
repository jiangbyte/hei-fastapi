from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from core.pojo import PageBounds, BaseExportParam
from core.pojo.datetime_mixin import DateTimeValidatorMixin


class GroupVO(DateTimeValidatorMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    code: str
    name: str
    category: str
    parent_id: Optional[str] = None
    org_id: str
    description: Optional[str] = None
    status: Optional[str] = None
    sort_code: Optional[int] = 0
    org_names: Optional[List[str]] = None
    extra: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class GroupTreeVO(BaseModel):
    """Group tree node with children"""
    id: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    parent_id: Optional[str] = None
    org_id: Optional[str] = None
    status: Optional[str] = None
    sort_code: Optional[int] = 0
    children: List["GroupTreeVO"] = []


class GroupTreeParam(BaseModel):
    org_id: Optional[str] = None
    keyword: Optional[str] = None


class GroupPageParam(PageBounds):
    parent_id: Optional[str] = None
    keyword: Optional[str] = None
    org_id: Optional[str] = None


class GroupExportParam(BaseExportParam):
    pass


class GroupImportParam(BaseModel):
    data: List[GroupVO]

