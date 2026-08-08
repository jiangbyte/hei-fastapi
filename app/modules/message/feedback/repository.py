""" Author: Charlie

由 HEI 代码生成器生成。
Author: jiangbyte
"""
from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.message.enums import FeedbackStatus
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

    async def create(
        self,
        payload: MsgFeedbackCreateRequest,
        *,
        submitter_account_type: str,
        submitter_account_id: str,
        attach_object_names: list[str] | None = None,
    ) -> MsgFeedback:
        data = payload.model_dump()
        data["attach_object_names"] = (
            attach_object_names
            if attach_object_names is not None
            else data.get("attach_object_names") or []
        )
        entity = MsgFeedback(
            **data,
            status=FeedbackStatus.PENDING.value,
            submitter_account_type=submitter_account_type,
            submitter_account_id=submitter_account_id,
        )
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
        if query.title:
            filters.append(MsgFeedback.title.ilike(f"%{query.title}%"))
        if query.category:
            filters.append(MsgFeedback.category == query.category)
        if query.status:
            filters.append(MsgFeedback.status == query.status)
        if query.submitter_account_type is not None:
            filters.append(
                MsgFeedback.submitter_account_type == query.submitter_account_type.value
            )
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
