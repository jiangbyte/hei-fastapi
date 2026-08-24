"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-08-08 21:09:52
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import snapshots as audit_snapshots
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
from app.modules.biz.cg_test_activity.model import CgTestActivity
from app.modules.biz.cg_test_activity.repository import (
    CgTestActivityRepository,
)
from app.modules.biz.cg_test_activity.schema import (
    CgTestActivityAdminPageQuery,
    CgTestActivityCreateRequest,
    CgTestActivitySchema,
    CgTestActivityUpdateRequest,
)


class CgTestActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CgTestActivityRepository(db)

    async def create(
        self,
        payload: CgTestActivityCreateRequest,
        session: SessionPayload | None = None,
    ) -> None:
        async with transactional(self.db):
            entity = await self.repo.create(
                payload, owner_dept_id=default_owner_dept_id(session)
            )
        audit_snapshots.created_entity(entity)

    async def update(self, payload: CgTestActivityUpdateRequest) -> None:
        existing = await self.repo.get_required(payload.id)
        audit_snapshots.before_entity(existing)
        async with transactional(self.db):
            await self.repo.update(payload)
            updated = await self.repo.get_required(payload.id)
        audit_snapshots.after_entity(updated)

    async def delete(self, payload: IdsRequest) -> None:
        unique_ids = list(dict.fromkeys(payload.ids))
        if not unique_ids:
            return
        entities = [await self.repo.get_required(entity_id) for entity_id in unique_ids]
        audit_snapshots.deleted_all(entities)
        async with transactional(self.db):
            await self.repo.delete_many(unique_ids)

    async def detail(self, query: IdQuery) -> CgTestActivitySchema:
        schema = to_schema(CgTestActivitySchema, await self.repo.get_required(query.id))
        return schema

    async def page_admin(
        self,
        query: CgTestActivityAdminPageQuery,
        session: SessionPayload | None = None,
    ) -> PageData[CgTestActivitySchema]:
        data_scope_filter = None
        if session is not None:
            data_scope_filter = await build_data_scope_filter(
                self.db,
                session,
                "biz:cgtestactivity:page",
                owner_column=CgTestActivity.created_by,
                dept_column=getattr(CgTestActivity, "owner_dept_id", None),
            )
        items, total = await self.repo.page_admin(query, data_scope_filter)
        records = to_schema_list(CgTestActivitySchema, items)
        return build_page(query, total, records)
