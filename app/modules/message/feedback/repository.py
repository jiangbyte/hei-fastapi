""" Author: Charlie

由 HEI 代码生成器生成。
Author: jiangbyte
"""
from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.message.feedback.model import MsgFeedback
from app.modules.message.feedback.schema import (
    MsgFeedbackAdminPageQuery,
    MsgFeedbackCreateRequest,
    MsgFeedbackUpdateRequest,
    MyFeedbackPageQuery,
)


class MsgFeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: MsgFeedbackCreateRequest) -> MsgFeedback:
        entity = MsgFeedback(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, entity_id: str) -> MsgFeedback | None:
        return await self.db.get(MsgFeedback, entity_id)

    async def get_required(self, entity_id: str) -> MsgFeedback:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError("MsgFeedback not found")
        return entity

    async def update_status(self, payload: MsgFeedbackUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        entity.status = payload.status
        if payload.reply is not None:
            entity.reply = payload.reply
        await self.db.flush()

    async def delete_many(self, entity_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(entity_ids))
        stmt = select(MsgFeedback.id).where(MsgFeedback.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("MsgFeedback not found")
        await self.db.execute(delete(MsgFeedback).where(MsgFeedback.id.in_(unique_ids)))

    async def page_admin(self, query: MsgFeedbackAdminPageQuery) -> tuple[list[MsgFeedback], int]:
        stmt: Select[tuple[MsgFeedback]] = select(MsgFeedback)
        count_stmt = select(func.count(MsgFeedback.id))
        filters = []
        if query.content:
            filters.append(MsgFeedback.content.ilike(f"%{query.content}%"))
        if query.category:
            filters.append(MsgFeedback.category == query.category)
        if query.status:
            filters.append(MsgFeedback.status == query.status)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(MsgFeedback.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total

    async def page_my(
        self,
        query: MyFeedbackPageQuery,
        account_type: str,
        account_id: str,
    ) -> tuple[list[MsgFeedback], int]:
        stmt = select(MsgFeedback).where(
            MsgFeedback.submitter_account_type == account_type,
            MsgFeedback.submitter_account_id == account_id,
        )
        count_stmt = select(func.count(MsgFeedback.id)).where(
            MsgFeedback.submitter_account_type == account_type,
            MsgFeedback.submitter_account_id == account_id,
        )
        stmt = (
            stmt.order_by(MsgFeedback.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total
