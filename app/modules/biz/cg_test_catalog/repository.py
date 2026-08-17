"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-08-08 21:09:53
"""

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.db.batch import chunked
from app.core.db.compat import ci_like
from app.core.exceptions.business import NotFoundError
from app.modules.biz.cg_test_catalog.model import (
    CgTestCatalog,
)
from app.modules.biz.cg_test_catalog.schema import (
    CgTestCatalogAdminPageQuery,
    CgTestCatalogCreateRequest,
    CgTestCatalogUpdateRequest,
)


class CgTestCatalogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        payload: CgTestCatalogCreateRequest,
        *,
        owner_dept_id: str | None = None,
    ) -> CgTestCatalog:
        entity = CgTestCatalog(**payload.model_dump())
        if owner_dept_id is not None:
            entity.owner_dept_id = owner_dept_id
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, entity_id: str) -> CgTestCatalog | None:
        return await self.db.get(CgTestCatalog, entity_id)

    async def get_required(self, entity_id: str) -> CgTestCatalog:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError("CgTestCatalog not found")
        return entity

    async def update(self, payload: CgTestCatalogUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        for key, value in payload.model_dump(exclude={"id"}).items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, entity_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(entity_ids))
        if not unique_ids:
            return
        for batch in chunked(unique_ids):
            stmt = select(CgTestCatalog.id).where(CgTestCatalog.id.in_(batch))
            existing_ids = set((await self.db.execute(stmt)).scalars().all())
            if len(existing_ids) != len(batch):
                raise NotFoundError("CgTestCatalog not found")
            await self.db.execute(delete(CgTestCatalog).where(CgTestCatalog.id.in_(batch)))

    async def page_admin(
        self,
        query: CgTestCatalogAdminPageQuery,
        data_scope_filter: ColumnElement[bool] | None = None,
    ) -> tuple[list[CgTestCatalog], int]:
        stmt: Select[tuple[CgTestCatalog]] = select(CgTestCatalog)
        count_stmt = select(func.count(CgTestCatalog.id))
        filters = []
        if query.code:
            filters.append(ci_like(CgTestCatalog.code, f"%{query.code}%"))
        if query.name:
            filters.append(ci_like(CgTestCatalog.name, f"%{query.name}%"))
        if query.category:
            filters.append(ci_like(CgTestCatalog.category, f"%{query.category}%"))
        if query.status is not None:
            filters.append(CgTestCatalog.status == query.status)
        if data_scope_filter is not None:
            filters.append(data_scope_filter)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = stmt.order_by(CgTestCatalog.id.desc()).offset(query.offset).limit(query.size)
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total

    async def get_parent_name_map(self, parent_ids: set[str]) -> dict[str, str]:
        if not parent_ids:
            return {}
        result: dict[str, str] = {}
        for batch in chunked(sorted(parent_ids)):
            stmt = select(CgTestCatalog.id, CgTestCatalog.name).where(
                CgTestCatalog.id.in_(batch)
            )
            rows = (await self.db.execute(stmt)).all()
            result.update({str(id_): str(name or id_) for id_, name in rows})
        return result

    async def list_tree(
        self,
        keyword: str | None = None,
        data_scope_filter: ColumnElement[bool] | None = None,
    ) -> list[CgTestCatalog]:
        stmt = select(CgTestCatalog).order_by(CgTestCatalog.id.asc())
        filters = []
        if keyword:
            filters.append(ci_like(CgTestCatalog.name, f"%{keyword}%"))
        if data_scope_filter is not None:
            filters.append(data_scope_filter)
        if filters:
            stmt = stmt.where(*filters)
        return list((await self.db.execute(stmt)).scalars().all())
