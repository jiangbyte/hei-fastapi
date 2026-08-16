""" Author: Charlie

定时任务 Schema：创建/更新/启停载荷、管理端分页查询与响应模型（对齐 hei-boot）。
"""

from datetime import datetime

from pydantic import Field

from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireBool, WireInt


class JobCreateRequest(ApiSchema):
    """任务创建请求（字段对齐 hei-boot SysJobAddParam）。"""

    job_name: str = Field(min_length=1, max_length=128)
    execute_class: str = Field(min_length=1, max_length=255)
    execute_type: str = Field(min_length=1, max_length=16)
    trigger_config: str = Field(min_length=1, max_length=255)
    execute_param: dict | None = None
    description: str | None = Field(default=None, max_length=500)
    sort: WireInt = 0
    enabled: WireBool = True


class JobUpdateRequest(JobCreateRequest):
    """任务更新请求，在创建字段基础上增加主键。"""

    id: str = Field(min_length=1, max_length=64)


class JobEnabledRequest(ApiSchema):
    """任务启停请求。"""

    id: str = Field(min_length=1, max_length=64)
    enabled: WireBool


class JobAdminPageQuery(PageQuery):
    """任务分页查询参数。"""

    job_name: str | None = Field(default=None, max_length=128)
    execute_type: str | None = Field(default=None, max_length=16)
    enabled: WireBool | None = None


class SysJobSchema(ApiSchema):
    """任务响应模型。"""

    id: str
    job_name: str
    execute_class: str
    execute_type: str
    trigger_config: str
    execute_param: dict | None = None
    last_run_time: datetime | None = None
    next_run_time: datetime
    last_execute_result: str | None = None
    enabled: WireBool
    description: str | None = None
    sort: WireInt
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    created_name: str | None = None
    updated_name: str | None = None


class JobLogAdminPageQuery(PageQuery):
    """执行日志分页查询参数。"""

    job_id: str | None = Field(default=None, max_length=64)
    success: WireBool | None = None


class SysJobLogSchema(ApiSchema):
    """执行日志响应模型。"""

    id: str
    job_id: str
    job_name: str
    execute_param: dict | None = None
    execute_time: datetime
    execute_duration_ms: WireInt | None = None
    success: WireBool
    execute_result: str | None = None
    executor: str | None = None
    ip: str | None = None
    process_id: str | None = None
    app_dir: str | None = None
    created_at: datetime
