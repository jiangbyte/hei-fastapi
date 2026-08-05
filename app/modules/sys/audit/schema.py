from datetime import datetime

from pydantic import Field

from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema


class OperationAuditRecord(ApiSchema):
    id: str
    module: str
    resource_type: str | None = None
    resource_id: str | None = None
    action: str
    summary: str | None = None
    before_data: dict | None = None
    after_data: dict | None = None
    account_id: str | None = None
    account_type: str | None = None
    request_id: str | None = None
    ip: str | None = None
    user_agent: str | None = None
    success: bool
    error_message: str | None = None
    created_at: datetime


class OperationAuditCreate(ApiSchema):
    module: str
    resource_type: str | None = None
    resource_id: str | None = None
    action: str
    summary: str | None = None
    before_data: dict | None = None
    after_data: dict | None = None
    account_id: str | None = None
    account_type: str | None = None
    request_id: str | None = None
    ip: str | None = None
    user_agent: str | None = None
    success: bool = True
    error_message: str | None = None


class OperationAuditPageQuery(PageQuery):
    module: str | None = Field(default=None, max_length=64)
    action: str | None = Field(default=None, max_length=64)
    account_id: str | None = Field(default=None, max_length=64)
    success: bool | None = None
