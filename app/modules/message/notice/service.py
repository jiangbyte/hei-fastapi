""" Author: Charlie

消息通知服务层：创建、发布、撤回、置顶与阅读状态管理。
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.db.transaction import transactional
from app.core.exceptions.business import BusinessError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.session import SessionPayload
from app.modules.message.enums import NoticeKind, NoticeStatus
from app.modules.message.notice.model import SysNoticeRead
from app.modules.message.notice.repository import SysNoticeRepository
from app.modules.message.notice.schema import (
    MyNoticePageQuery,
    NoticeReadRequest,
    PinNoticeRequest,
    SysNoticeAdminPageQuery,
    SysNoticeCreateRequest,
    SysNoticeSchema,
    SysNoticeUpdateRequest,
)
from app.modules.user.utils.profile import enrich_audit_name, enrich_audit_names


class SysNoticeService:
    """消息通知业务服务，编排仓储并提供发布/阅读等用例。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SysNoticeRepository(db)

    async def create(self, payload: SysNoticeCreateRequest) -> None:
        """创建消息：规范化状态，并在发布时补写发布时间。"""
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
            await self.repo.create(SysNoticeCreateRequest(**data))

    async def update(self, payload: SysNoticeUpdateRequest) -> None:
        """更新消息。"""
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        """批量删除消息。"""
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysNoticeSchema:
        """管理端查询消息详情，并补充审计人姓名。"""
        entity = await self.repo.get_required(query.id)
        schema = to_schema(SysNoticeSchema, entity)
        return await enrich_audit_name(self.db, schema, account_type=AccountType.ADMIN)

    async def page_admin(self, query: SysNoticeAdminPageQuery) -> PageData[SysNoticeSchema]:
        """管理端分页查询消息。"""
        items, total = await self.repo.page_admin(query)
        schemas = to_schema_list(SysNoticeSchema, items)
        schemas = await enrich_audit_names(self.db, schemas, account_type=AccountType.ADMIN)
        return build_page(query, total, schemas)

    async def publish(self, payload: IdsRequest, session: SessionPayload) -> None:
        """发布消息，记录发布时间与发送者（批量单条 UPDATE）。"""
        async with transactional(self.db):
            await self.repo.publish_many(
                payload.ids,
                now=datetime.now(UTC),
                sender_account_type=str(session.account_type),
                sender_account_id=session.account_id,
            )

    async def revoke(self, payload: IdsRequest) -> None:
        """撤回消息，记录撤回时间（批量单条 UPDATE）。"""
        async with transactional(self.db):
            await self.repo.revoke_many(payload.ids, now=datetime.now(UTC))

    async def pin(self, payload: PinNoticeRequest) -> None:
        """置顶/取消置顶公告（仅公告支持置顶）。"""
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
    ) -> PageData[SysNoticeSchema]:
        """分页查询当前用户可见消息，并标记是否已读。"""
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
    ) -> PageData[SysNoticeSchema]:
        """门户列表页查询公告（匿名可见，登录后附加个性化信息）。"""
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

    async def my_detail(self, query: IdQuery, session: SessionPayload) -> SysNoticeSchema:
        """查询当前用户消息详情，并顺带自增查看数、标记已读。"""
        async with transactional(self.db):
            await self.repo.increment_view_count(query.id)
            await self.repo.mark_read([query.id], str(session.account_type), session.account_id)
        entity = await self.repo.get_required(query.id)
        read_set = await self._check_read([entity.id], session)
        return _build_schema(entity, read_set)

    async def count_unread(self, session: SessionPayload) -> int:
        """统计当前用户未读消息数。"""
        return await self.repo.count_unread(str(session.account_type), session.account_id)

    async def mark_read(self, payload: NoticeReadRequest, session: SessionPayload) -> None:
        """将指定消息标记为当前用户已读。"""
        async with transactional(self.db):
            await self.repo.mark_read(payload.ids, str(session.account_type), session.account_id)

    async def mark_all_read(self, session: SessionPayload) -> None:
        """将当前用户全部可见消息标记为已读。"""
        async with transactional(self.db):
            await self.repo.mark_all_read(str(session.account_type), session.account_id)

    async def _check_read(self, notice_ids: list[str], session: SessionPayload) -> set[str]:
        """查询给定消息中已被当前用户阅读的 ID 集合。"""
        if not notice_ids:
            return set()
        stmt = select(SysNoticeRead.notice_id).where(
            SysNoticeRead.notice_id.in_(notice_ids),
            SysNoticeRead.account_type == str(session.account_type),
            SysNoticeRead.account_id == session.account_id,
        )
        return set((await self.db.execute(stmt)).scalars().all())


def _build_schema(item, read_id_set: set[str]) -> SysNoticeSchema:
    """由实体构建消息响应，并标记是否已读。"""
    schema = to_schema(SysNoticeSchema, item)
    schema.is_read = item.id in read_id_set
    return schema
