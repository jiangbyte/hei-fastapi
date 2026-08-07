"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-08-07 07:26:16
"""

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.exceptions.business import NotFoundError
from app.modules.biz.cg_test_order.model import (
    CgTestOrder,
    CgTestOrderItem,
)
from app.modules.biz.cg_test_order.schema import (
    CgTestOrderAdminPageQuery,
    CgTestOrderCreateRequest,
    CgTestOrderItemAdminPageQuery,
    CgTestOrderItemCreateRequest,
    CgTestOrderItemUpdateRequest,
    CgTestOrderUpdateRequest,
)


class CgTestOrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        payload: CgTestOrderCreateRequest,
        *,
        owner_dept_id: str | None = None,
    ) -> CgTestOrder:
        entity = CgTestOrder(**payload.model_dump())
        if owner_dept_id is not None:
            entity.owner_dept_id = owner_dept_id
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, entity_id: str) -> CgTestOrder | None:
        return await self.db.get(CgTestOrder, entity_id)

    async def get_required(self, entity_id: str) -> CgTestOrder:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError("CgTestOrder not found")
        return entity

    async def update(self, payload: CgTestOrderUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        for key, value in payload.model_dump(exclude={"id"}).items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, entity_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(entity_ids))
        stmt = select(CgTestOrder.id).where(CgTestOrder.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("CgTestOrder not found")
        await self.db.execute(delete(CgTestOrder).where(CgTestOrder.id.in_(unique_ids)))

    async def page_admin(
        self,
        query: CgTestOrderAdminPageQuery,
        data_scope_filter: ColumnElement[bool] | None = None,
    ) -> tuple[list[CgTestOrder], int]:
        stmt: Select[tuple[CgTestOrder]] = select(CgTestOrder)
        count_stmt = select(func.count(CgTestOrder.id))
        filters = []
        if query.name:
            filters.append(CgTestOrder.name.ilike(f"%{query.name}%"))
        if query.status is not None:
            filters.append(CgTestOrder.status == query.status)
        if query.type:
            filters.append(CgTestOrder.type.ilike(f"%{query.type}%"))
        if data_scope_filter is not None:
            filters.append(data_scope_filter)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = stmt.order_by(CgTestOrder.id.desc()).offset(query.offset).limit(query.size)
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total


class CgTestOrderItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: CgTestOrderItemCreateRequest) -> CgTestOrderItem:
        entity = CgTestOrderItem(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, entity_id: str) -> CgTestOrderItem | None:
        return await self.db.get(CgTestOrderItem, entity_id)

    async def get_required(self, entity_id: str) -> CgTestOrderItem:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError("CgTestOrderItem not found")
        return entity

    async def update(self, payload: CgTestOrderItemUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        for key, value in payload.model_dump(exclude={"id"}).items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, entity_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(entity_ids))
        stmt = select(CgTestOrderItem.id).where(CgTestOrderItem.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("CgTestOrderItem not found")
        await self.db.execute(delete(CgTestOrderItem).where(CgTestOrderItem.id.in_(unique_ids)))

    async def page_admin(self, query: CgTestOrderItemAdminPageQuery) -> tuple[list[CgTestOrderItem], int]:
        stmt: Select[tuple[CgTestOrderItem]] = select(CgTestOrderItem)
        count_stmt = select(func.count(CgTestOrderItem.id))
        filters = []
        if query.order_id:
            filters.append(CgTestOrderItem.order_id == query.order_id)
        if query.name:
            filters.append(CgTestOrderItem.name.ilike(f"%{query.name}%"))
        if query.category:
            filters.append(CgTestOrderItem.category.ilike(f"%{query.category}%"))
        if query.status is not None:
            filters.append(CgTestOrderItem.status == query.status)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = stmt.order_by(CgTestOrderItem.id.desc()).offset(query.offset).limit(query.size)
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total
