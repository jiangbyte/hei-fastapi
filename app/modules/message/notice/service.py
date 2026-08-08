""" Author: Charlie """

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.exceptions.business import BusinessError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.session import SessionPayload
from app.modules.message.enums import NoticeKind, NoticeStatus
from app.modules.message.notice.model import MsgNoticeRead
from app.modules.message.notice.repository import MsgNoticeRepository
from app.modules.message.notice.schema import (
    MsgNoticeAdminPageQuery,
    MsgNoticeCreateRequest,
    MsgNoticeSchema,
    MsgNoticeUpdateRequest,
    MyNoticePageQuery,
    NoticeReadRequest,
    PinNoticeRequest,
)
from app.modules.user.utils.profile import enrich_audit_name, enrich_audit_names
from app.platform.db.transaction import transactional


class MsgNoticeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MsgNoticeRepository(db)

    async def create(self, payload: MsgNoticeCreateRequest) -> None:
        async with transactional(self.db):
            data = payload.model_dump()
            status = str(data.get("status") or NoticeStatus.DRAFT.value).upper()
            if status in {"ENABLED", "ENABLE"}:
                status = NoticeStatus.DRAFT.value
            if status not in {
                NoticeStatus.DRAFT.value,
                NoticeStatus.PUBLISHED.value,
                NoticeStatus.REVOKED.value,
            }:
                status = NoticeStatus.DRAFT.value
            data["status"] = status
            if status == NoticeStatus.PUBLISHED.value and not data.get("publish_at"):
                data["publish_at"] = datetime.now(UTC)
            await self.repo.create(MsgNoticeCreateRequest(**data))

    async def update(self, payload: MsgNoticeUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> MsgNoticeSchema:
        entity = await self.repo.get_required(query.id)
        schema = to_schema(MsgNoticeSchema, entity)
        return await enrich_audit_name(self.db, schema, account_type=AccountType.ADMIN)

    async def page_admin(self, query: MsgNoticeAdminPageQuery) -> PageData[MsgNoticeSchema]:
        items, total = await self.repo.page_admin(query)
        schemas = to_schema_list(MsgNoticeSchema, items)
        schemas = await enrich_audit_names(self.db, schemas, account_type=AccountType.ADMIN)
        return build_page(query, total, schemas)

    async def publish(self, payload: IdsRequest, session: SessionPayload) -> None:
        async with transactional(self.db):
            now = datetime.now(UTC)
            for entity_id in payload.ids:
                entity = await self.repo.get_required(entity_id)
                entity.status = NoticeStatus.PUBLISHED.value
                entity.publish_at = now
                entity.sender_account_type = str(session.account_type)
                entity.sender_account_id = session.account_id
            await self.db.flush()

    async def revoke(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            now = datetime.now(UTC)
            for entity_id in payload.ids:
                entity = await self.repo.get_required(entity_id)
                entity.status = NoticeStatus.REVOKED.value
                entity.revoked_at = now
            await self.db.flush()

    async def pin(self, payload: PinNoticeRequest) -> None:
        async with transactional(self.db):
            entity = await self.repo.get_required(payload.id)
            if entity.kind != NoticeKind.ANNOUNCEMENT.value:
                raise BusinessError("仅公告支持置顶")
            entity.is_pinned = payload.is_pinned
            entity.pinned_until = payload.pinned_until
            await self.db.flush()

    async def page_my(
        self,
        query: MyNoticePageQuery,
        session: SessionPayload,
    ) -> PageData[MsgNoticeSchema]:
        items, total, read_id_set = await self.repo.page_my(
            query,
            str(session.account_type),
            session.account_id,
        )
        schemas = [_build_schema(item, read_id_set) for item in items]
        return build_page(query, total, schemas)

    async def page_portal_list(
        self,
        query: MyNoticePageQuery,
        session: SessionPayload | None = None,
    ) -> PageData[MsgNoticeSchema]:
        account_type = AccountType.PORTAL.value
        account_id: str | None = None
        if session and str(session.account_type) == AccountType.PORTAL.value:
            account_type = str(session.account_type)
            account_id = session.account_id
        items, total, read_id_set = await self.repo.page_my(
            query,
            account_type,
            account_id,
            kind=NoticeKind.ANNOUNCEMENT.value,
        )
        schemas = [_build_schema(item, read_id_set) for item in items]
        return build_page(query, total, schemas)

    async def my_detail(self, query: IdQuery, session: SessionPayload) -> MsgNoticeSchema:
        async with transactional(self.db):
            await self.repo.increment_view_count(query.id)
            await self.repo.mark_read([query.id], str(session.account_type), session.account_id)
        entity = await self.repo.get_required(query.id)
        read_set = await self._check_read([entity.id], session)
        return _build_schema(entity, read_set)

    async def count_unread(self, session: SessionPayload) -> int:
        return await self.repo.count_unread(str(session.account_type), session.account_id)

    async def mark_read(self, payload: NoticeReadRequest, session: SessionPayload) -> None:
        async with transactional(self.db):
            await self.repo.mark_read(payload.ids, str(session.account_type), session.account_id)

    async def mark_all_read(self, session: SessionPayload) -> None:
        async with transactional(self.db):
            await self.repo.mark_all_read(str(session.account_type), session.account_id)

    async def _check_read(self, notice_ids: list[str], session: SessionPayload) -> set[str]:
        if not notice_ids:
            return set()
        stmt = select(MsgNoticeRead.notice_id).where(
            MsgNoticeRead.notice_id.in_(notice_ids),
            MsgNoticeRead.account_type == str(session.account_type),
            MsgNoticeRead.account_id == session.account_id,
        )
        return set((await self.db.execute(stmt)).scalars().all())


def _build_schema(item, read_id_set: set[str]) -> MsgNoticeSchema:
    schema = to_schema(MsgNoticeSchema, item)
    schema.is_read = item.id in read_id_set
    return schema
