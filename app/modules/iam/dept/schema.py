from datetime import datetime

from pydantic import Field

from app.core.config.enums import StatusEnum
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema


class DeptCreateRequest(ApiSchema):
    name: str
    category: str
    parent_id: str | None = None
    master_id: str | None = None
    deputy_master_id: str | None = None
    sort: int = 99
    is_virtual: bool = False
    status: StatusEnum = StatusEnum.ENABLED
    extra: dict = Field(default_factory=dict)


class DeptUpdateRequest(DeptCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class DeptAdminPageQuery(PageQuery):
    name: str | None = Field(default=None, max_length=64)
    category: str | None = Field(default=None, max_length=64)
    parent_id: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, max_length=32)


class SysDeptSchema(ApiSchema):
    id: str
    parent_id: str | None = None
    parent_name: str | None = None
    master_id: str | None = None
    master_name: str | None = None
    deputy_master_id: str | None = None
    deputy_master_name: str | None = None
    name: str
    category: str
    sort: int
    is_virtual: bool
    status: str
    extra: dict
    created_at: datetime
    created_by: str | None = None
    created_name: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    updated_name: str | None = None


class DeptTreeNode(ApiSchema):
    id: str
    name: str
    category: str
    parent_id: str | None = None
    status: str
    sort: int = 99
    is_virtual: bool = False
    master_name: str | None = None
    deputy_master_name: str | None = None
    updated_at: datetime | None = None
    children: list["DeptTreeNode"] = Field(default_factory=list)
