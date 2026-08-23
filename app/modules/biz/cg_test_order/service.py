"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-08-08 21:09:54
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.db.transaction import transactional
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import (
    IdQuery,
    IdsRequest,
    to_schema,
    to_schema_list,
)
from app.core.security.data_scope import build_data_scope_filter, default_owner_dept_id
from app.core.security.session import SessionPayload
from app.modules.biz.cg_test_order.model import CgTestOrder
from app.modules.biz.cg_test_order.repository import (
    CgTestOrderItemRepository,
    CgTestOrderRepository,
)
from app.modules.biz.cg_test_order.schema import (
    CgTestOrderAdminPageQuery,
    CgTestOrderCreateRequest,
    CgTestOrderItemAdminPageQuery,
    CgTestOrderItemCreateRequest,
    CgTestOrderItemSchema,
    CgTestOrderItemUpdateRequest,
    CgTestOrderSchema,
    CgTestOrderUpdateRequest,
)


class CgTestOrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CgTestOrderRepository(db)

    async def create(
        self,
        payload: CgTestOrderCreateRequest,
        session: SessionPayload | None = None,
    ) -> None:
        async with transactional(self.db):
            await self.repo.create(payload, owner_dept_id=default_owner_dept_id(session))

    async def update(self, payload: CgTestOrderUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> CgTestOrderSchema:
        schema = to_schema(CgTestOrderSchema, await self.repo.get_required(query.id))
        return schema

    async def page_admin(
        self,
        query: CgTestOrderAdminPageQuery,
        session: SessionPayload | None = None,
    ) -> PageData[CgTestOrderSchema]:
        data_scope_filter = None
        if session is not None:
            data_scope_filter = await build_data_scope_filter(
                self.db,
                session,
                "biz:cgtestorder:page",
                owner_column=CgTestOrder.created_by,
                dept_column=getattr(CgTestOrder, "owner_dept_id", None),
            )
        items, total = await self.repo.page_admin(query, data_scope_filter)
        records = to_schema_list(CgTestOrderSchema, items)
        return build_page(query, total, records)


class CgTestOrderItemService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CgTestOrderItemRepository(db)

    async def create(self, payload: CgTestOrderItemCreateRequest) -> None:
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: CgTestOrderItemUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> CgTestOrderItemSchema:
        schema = to_schema(CgTestOrderItemSchema, await self.repo.get_required(query.id))
        return schema

    async def page_admin(self, query: CgTestOrderItemAdminPageQuery) -> PageData[CgTestOrderItemSchema]:
        items, total = await self.repo.page_admin(query)
        records = to_schema_list(CgTestOrderItemSchema, items)
        return build_page(query, total, records)
