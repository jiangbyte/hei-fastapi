"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-08-08 21:09:52
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
from app.modules.user.utils.profile import enrich_audit_names


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
            await self.repo.create(payload, owner_dept_id=default_owner_dept_id(session))

    async def update(self, payload: CgTestActivityUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> CgTestActivitySchema:
        schema = to_schema(CgTestActivitySchema, await self.repo.get_required(query.id))
        await enrich_audit_names(self.db, [schema], account_type=AccountType.ADMIN)
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
        await enrich_audit_names(self.db, records, account_type=AccountType.ADMIN)
        return build_page(query, total, records)
