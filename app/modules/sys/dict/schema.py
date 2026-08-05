"""系统字典模块 Schema，类型字段使用枚举以保证值和字典数据一致。"""

from datetime import datetime
from typing import Annotated

from pydantic import Field

from app.core.config.enums import StatusEnum, SysBizCategory
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema

DictId = Annotated[str, Field(min_length=1, max_length=32)]


class DictCreateRequest(ApiSchema):
    code: str = Field(min_length=1, max_length=50, pattern=r"^[A-Z0-9_]+$")
    label: str | None = Field(default=None, max_length=255)
    value: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=32)
    category: SysBizCategory | None = None
    parent_id: DictId | None = None
    status: StatusEnum = StatusEnum.ENABLED
    sort: int = 0


class DictUpdateRequest(DictCreateRequest):
    id: DictId


class DictIdQuery(ApiSchema):
    id: DictId


class DictIdsRequest(ApiSchema):
    ids: list[DictId] = Field(min_length=1)


class DictAdminPageQuery(PageQuery):
    code: str | None = Field(default=None, max_length=50, pattern=r"^[A-Z0-9_]+$")
    category: SysBizCategory | None = None
    parent_id: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, max_length=16)


class DictTreeQuery(ApiSchema):
    category: SysBizCategory | None = None


class SysDictSchema(ApiSchema):
    id: str
    code: str
    label: str | None = None
    value: str | None = None
    color: str | None = None
    category: SysBizCategory | None = None
    parent_id: str | None = None
    parent_id_name: str | None = None
    status: StatusEnum | str
    sort: int
    created_at: datetime
    created_by: str | None = None
    created_name: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    updated_name: str | None = None


class SysDictTreeNode(ApiSchema):
    id: str
    code: str
    label: str | None = None
    value: str | None = None
    color: str | None = None
    category: SysBizCategory | None = None
    parent_id: str | None = None
    parent_id_name: str | None = None
    status: StatusEnum | str
    sort: int
    children: list["SysDictTreeNode"] = Field(default_factory=list)
