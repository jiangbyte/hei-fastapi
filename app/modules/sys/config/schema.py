from datetime import datetime
from typing import Any

from pydantic import Field

from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema


class ConfigCreateRequest(ApiSchema):
    config_key: str = Field(min_length=1, max_length=255)
    config_value: str | None = None
    category: str | None = Field(default=None, max_length=255)
    remark: str | None = Field(default=None, max_length=255)
    sort_code: int = 0
    ext_json: dict[str, Any] = Field(default_factory=dict)


class ConfigUpdateRequest(ConfigCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class ConfigAdminPageQuery(PageQuery):
    config_key: str | None = Field(default=None, max_length=255)
    category: str | None = Field(default=None, max_length=255)


class SysConfigSchema(ApiSchema):
    id: str
    config_key: str
    config_value: str | None = None
    category: str | None = None
    remark: str | None = None
    sort_code: int
    ext_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None


class ConfigBatchItem(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    config_key: str = Field(min_length=1, max_length=255)
    config_value: str | None = None


class ConfigBatchSaveRequest(ApiSchema):
    items: list[ConfigBatchItem]


class CategoryQuery(ApiSchema):
    category: str | None = Field(default=None, max_length=255)
