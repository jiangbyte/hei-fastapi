""" Author: Charlie """

from datetime import datetime

from sqlalchemy import Select, case, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import StatusEnum
from app.core.exceptions.business import NotFoundError
from app.modules.sys.banner.enums import BannerDisplayScope
from app.modules.sys.banner.model import SysBanner
from app.modules.sys.banner.schema import (
    BannerAdminPageQuery,
    BannerCreateRequest,
    BannerPublicListQuery,
    BannerUpdateRequest,
)


class BannerRepository:
    """展示图仓储，负责直接持久化和展示查询。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: BannerCreateRequest) -> None:
        entity = SysBanner(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()

    async def get_by_id(self, banner_id: str) -> SysBanner | None:
        return await self.db.get(SysBanner, banner_id)

    async def get_required(self, banner_id: str) -> SysBanner:
        entity = await self.get_by_id(banner_id)
        if entity is None:
            raise NotFoundError("Display image not found")
        return entity

    async def update(self, payload: BannerUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        data = payload.model_dump(exclude={"id"})
        for key, value in data.items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, banner_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(banner_ids))
        stmt = select(SysBanner.id).where(SysBanner.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("Display image not found")
        await self.db.execute(delete(SysBanner).where(SysBanner.id.in_(unique_ids)))

    async def page_admin(self, query: BannerAdminPageQuery) -> tuple[list[SysBanner], int]:
        stmt: Select[tuple[SysBanner]] = select(SysBanner)
        count_stmt = select(func.count(SysBanner.id))
        filters = []
        if query.display_scope:
            filters.append(SysBanner.display_scope == query.display_scope)
        if query.category:
            filters.append(SysBanner.category == query.category)
        if query.type:
            filters.append(SysBanner.type == query.type)
        if query.position:
            filters.append(SysBanner.position == query.position)
        if query.status:
            filters.append(SysBanner.status == str(query.status))
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(SysBanner.sort.asc(), SysBanner.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total

    async def list_public(
        self,
        *,
        now: datetime,
        query: BannerPublicListQuery,
    ) -> list[SysBanner]:
        stmt = select(SysBanner).where(
            SysBanner.display_scope == BannerDisplayScope.PORTAL.value,
            SysBanner.status == StatusEnum.ENABLED.value,
            SysBanner.position == query.position,
            or_(SysBanner.start_at.is_(None), SysBanner.start_at <= now),
            or_(SysBanner.end_at.is_(None), SysBanner.end_at >= now),
        )
        if query.category:
            stmt = stmt.where(SysBanner.category == query.category)
        if query.type:
            stmt = stmt.where(SysBanner.type == query.type)
        stmt = stmt.order_by(SysBanner.sort.asc(), SysBanner.id.desc())
        return list((await self.db.execute(stmt)).scalars().all())

    async def is_public_visible(self, banner_id: str, now: datetime) -> bool:
        stmt = select(SysBanner.id).where(
            SysBanner.id == banner_id,
            SysBanner.display_scope == BannerDisplayScope.PORTAL.value,
            SysBanner.status == StatusEnum.ENABLED.value,
            or_(SysBanner.start_at.is_(None), SysBanner.start_at <= now),
            or_(SysBanner.end_at.is_(None), SysBanner.end_at >= now),
        )
        return (await self.db.execute(stmt)).scalar_one_or_none() is not None

    async def increment_interactions(self, deltas: dict[str, int]) -> None:
        positive_deltas = {banner_id: delta for banner_id, delta in deltas.items() if delta > 0}
        if not positive_deltas:
            return
        await self.db.execute(
            update(SysBanner)
            .where(SysBanner.id.in_(positive_deltas))
            .values(
                interaction_count=SysBanner.interaction_count
                + case(positive_deltas, value=SysBanner.id, else_=0)
            )
        )
