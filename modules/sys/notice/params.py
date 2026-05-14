from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from core.pojo import PageBounds, BaseExportParam
from core.pojo.datetime_mixin import DateTimeValidatorMixin


class NoticeVO(DateTimeValidatorMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    title: str
    category: str
    type: str
    summary: Optional[str] = None
    content: Optional[str] = None
    cover: Optional[str] = None
    level: Optional[str] = None
    view_count: Optional[int] = 0
    is_top: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    sort_code: Optional[int] = 0
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_name: Optional[str] = None


class NoticePageParam(PageBounds):
    pass


class NoticeExportParam(BaseExportParam):
    pass


class NoticeImportParam(BaseModel):
    data: List[NoticeVO]
