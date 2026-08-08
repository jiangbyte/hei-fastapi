""" Author: Charlie """

from datetime import datetime

from pydantic import Field

from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema


class WeakPasswordCreateRequest(ApiSchema):
    password: str = Field(min_length=1, max_length=255)


class WeakPasswordUpdateRequest(WeakPasswordCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class WeakPasswordAdminPageQuery(PageQuery):
    password: str | None = Field(default=None, max_length=255)


class WeakPasswordListQuery(ApiSchema):
    password: str | None = Field(default=None, max_length=255)


class SysWeakPasswordSchema(ApiSchema):
    id: str
    password: str
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None
