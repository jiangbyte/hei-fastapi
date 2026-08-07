""" Author: Charlie """

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.exceptions.business import NotFoundError
from app.modules.iam.position.model import SysPosition
from app.modules.iam.position.schema import (
    PositionAdminPageQuery,
    PositionCreateRequest,
    PositionUpdateRequest,
)


class PositionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: PositionCreateRequest) -> None:
        position = SysPosition(**payload.model_dump())
        self.db.add(position)
        await self.db.flush()

    async def get_by_id(self, position_id: str) -> SysPosition | None:
        return await self.db.get(SysPosition, position_id)

    async def get_required(self, position_id: str) -> SysPosition:
        entity = await self.get_by_id(position_id)
        if entity is None:
            raise NotFoundError("Position not found")
        return entity

    async def update(self, payload: PositionUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        data = payload.model_dump(exclude={"id"})
        for key, value in data.items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, position_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(position_ids))
        if not unique_ids:
            return
        stmt = select(SysPosition.id).where(SysPosition.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("Position not found")
        await self.db.execute(delete(SysPosition).where(SysPosition.id.in_(unique_ids)))

    async def count_positions_in_scope(
        self,
        position_ids: list[str],
        data_scope_filter: ColumnElement[bool],
    ) -> int:
        unique_ids = list(dict.fromkeys(position_ids))
        if not unique_ids:
            return 0
        stmt = select(func.count(SysPosition.id)).where(
            SysPosition.id.in_(unique_ids), data_scope_filter
        )
        return int((await self.db.execute(stmt)).scalar_one())

    async def page_admin(
        self,
        query: PositionAdminPageQuery,
        data_scope_filter: ColumnElement[bool] | None = None,
    ) -> tuple[list[SysPosition], int]:
        stmt: Select[tuple[SysPosition]] = select(SysPosition)
        count_stmt = select(func.count(SysPosition.id))
        filters = []
        if query.name:
            filters.append(SysPosition.name.contains(query.name))
        if query.category:
            filters.append(SysPosition.category == query.category)
        if query.status:
            filters.append(SysPosition.status == query.status)
        if data_scope_filter is not None:
            filters.append(data_scope_filter)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(SysPosition.sort.asc(), SysPosition.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        positions = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return positions, total
