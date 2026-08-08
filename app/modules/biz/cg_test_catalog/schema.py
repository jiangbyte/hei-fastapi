"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-08-08 21:09:53
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema, Id
from app.core.schema.wire import WireBool, WireInt

class CgTestCatalogCreateRequest(ApiSchema):
    parent_id: str | None = None
    code: str
    name: str
    category: str | None = None
    status: str
    sort: WireInt
    is_visible: WireBool
    icon: str | None = None
    description: str | None = None
    extra: dict[str, Any]


class CgTestCatalogUpdateRequest(CgTestCatalogCreateRequest):
    id: Id


class CgTestCatalogAdminPageQuery(PageQuery):
    code: str | None = None
    name: str | None = None
    category: str | None = None
    status: str | None = None


class CgTestCatalogSchema(ApiSchema):
    id: str
    parent_id: str | None = None
    code: str
    name: str
    category: str | None = None
    status: str
    sort: WireInt
    is_visible: WireBool
    icon: str | None = None
    description: str | None = None
    extra: dict[str, Any]
    parent_id_name: str | None = None
    created_at: datetime
    created_by: str | None = None
    created_name: str | None = None
    owner_dept_id: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    updated_name: str | None = None


class CgTestCatalogTreeNode(CgTestCatalogSchema):
    children: list["CgTestCatalogTreeNode"] = Field(default_factory=list)
