from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from core.pojo import PageBounds, BaseExportParam
from core.pojo.datetime_mixin import DateTimeValidatorMixin


class BannerVO(DateTimeValidatorMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    title: str
    image: str
    category: str
    type: str
    position: str
    url: Optional[str] = None
    link_type: Optional[str] = "URL"
    summary: Optional[str] = None
    description: Optional[str] = None
    sort_code: Optional[int] = 0
    view_count: Optional[int] = 0
    click_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_name: Optional[str] = None


class BannerPageParam(PageBounds):
    pass


class BannerExportParam(BaseExportParam):
    pass


class BannerImportParam(BaseModel):
    data: List[BannerVO]
