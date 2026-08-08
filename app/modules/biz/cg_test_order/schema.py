"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-08-08 21:09:54
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema, Id
from app.core.schema.wire import WireBool, WireInt, WireFloat

class CgTestOrderCreateRequest(ApiSchema):
    order_no: str
    name: str
    customer_name: str
    customer_phone: str | None = None
    status: str
    type: str
    ordered_at: datetime
    paid_at: datetime | None = None
    total_amount: WireFloat
    item_count: WireInt
    need_invoice: WireBool
    invoice_config: dict[str, Any]
    remark: str | None = None
    extra: dict[str, Any] | None = Field(default_factory=dict)


class CgTestOrderUpdateRequest(CgTestOrderCreateRequest):
    id: Id


class CgTestOrderAdminPageQuery(PageQuery):
    name: str | None = None
    status: str | None = None
    type: str | None = None


class CgTestOrderSchema(ApiSchema):
    id: str
    order_no: str
    name: str
    customer_name: str
    customer_phone: str | None = None
    status: str
    type: str
    ordered_at: datetime
    paid_at: datetime | None = None
    total_amount: WireFloat
    item_count: WireInt
    need_invoice: WireBool
    invoice_config: dict[str, Any]
    remark: str | None = None
    extra: dict[str, Any] | None = Field(default_factory=dict)
    created_at: datetime
    created_by: str | None = None
    created_name: str | None = None
    owner_dept_id: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    updated_name: str | None = None


class CgTestOrderItemCreateRequest(ApiSchema):
    order_id: str
    sku_code: str
    name: str
    category: str | None = None
    status: str
    quantity: WireInt
    unit_price: WireFloat
    shipped_at: datetime | None = None
    is_gift: WireBool
    item_config: dict[str, Any]
    remark: str | None = None
    extra: dict[str, Any] | None = Field(default_factory=dict)


class CgTestOrderItemUpdateRequest(CgTestOrderItemCreateRequest):
    id: Id


class CgTestOrderItemAdminPageQuery(PageQuery):
    order_id: str | None = Field(default=None, max_length=64)
    name: str | None = None
    category: str | None = None
    status: str | None = None


class CgTestOrderItemSchema(ApiSchema):
    id: str
    order_id: str
    sku_code: str
    name: str
    category: str | None = None
    status: str
    quantity: WireInt
    unit_price: WireFloat
    shipped_at: datetime | None = None
    is_gift: WireBool
    item_config: dict[str, Any]
    remark: str | None = None
    extra: dict[str, Any] | None = Field(default_factory=dict)
    created_at: datetime
    created_by: str | None = None
    created_name: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    updated_name: str | None = None
