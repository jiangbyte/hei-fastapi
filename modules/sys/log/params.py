from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from core.pojo import PageBounds, BaseExportParam
from core.pojo.datetime_mixin import DateTimeValidatorMixin


class LogVO(DateTimeValidatorMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    category: Optional[str] = None
    name: Optional[str] = None
    exe_status: Optional[str] = None
    exe_message: Optional[str] = None
    op_ip: Optional[str] = None
    op_address: Optional[str] = None
    op_browser: Optional[str] = None
    op_os: Optional[str] = None
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    req_method: Optional[str] = None
    req_url: Optional[str] = None
    param_json: Optional[str] = None
    result_json: Optional[str] = None
    op_time: Optional[datetime] = None
    op_user: Optional[str] = None
    sign_data: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_name: Optional[str] = None


class LogPageParam(PageBounds):
    keyword: Optional[str] = None
    category: Optional[str] = None
    exe_status: Optional[str] = None


class LogExportParam(BaseExportParam):
    pass


class LogImportParam(BaseModel):
    data: List[LogVO]


class LogDeleteByCategoryParam(BaseModel):
    category: str


# ---- Chart / Statistics result models ----

class LogDailyCount(BaseModel):
    """Daily log count for a single category."""
    day: str = Field(..., description="日期 YYYY-MM-DD")
    category: str = Field(..., description="日志分类")
    count: int = Field(..., ge=0, description="数量")


class LogCategoryTotal(BaseModel):
    """Total log count for a single category."""
    category: str = Field(..., description="日志分类")
    total: int = Field(..., ge=0, description="总数")


class LogBarChartData(BaseModel):
    """Bar chart: daily counts per category for last N days."""
    days: List[str] = Field(default_factory=list)
    series: List["LogCategorySeries"] = Field(default_factory=list)


class LogCategorySeries(BaseModel):
    name: str = Field(..., description="系列名称")
    data: List[int] = Field(default_factory=list, description="每天的数量")


class LogPieChartData(BaseModel):
    """Pie chart: category -> total."""
    data: List[LogCategoryTotal] = Field(default_factory=list)


