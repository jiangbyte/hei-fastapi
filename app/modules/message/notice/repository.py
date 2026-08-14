""" Author: Charlie

消息通知仓储层：封装消息的增删改查、可见性过滤与阅读状态管理。
"""

from datetime import UTC, datetime

from sqlalchemy import Select, String, and_, cast, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from app.core.db.batch import chunked
from app.core.exceptions.business import NotFoundError
from app.modules.message.enums import NoticeKind, NoticeStatus, TargetScope
from app.modules.message.notice.model import MsgNotice, MsgNoticeRead
from app.modules.message.notice.schema import (
    MsgNoticeAdminPageQuery,
    MsgNoticeCreateRequest,
    MsgNoticeUpdateRequest,
    MyNoticePageQuery,
)


def _visible_to_account(account_type: str, account_id: str | None = None) -> ColumnElement[bool]:
    """构造「对指定账户可见」的过滤条件（按类型匹配或按 ID 精确匹配）。"""
    type_match = (func.json_array_length(MsgNotice.target_account_types) == 0) | cast(
        MsgNotice.target_account_types, String
    ).contains('"' + account_type + '"')
    clauses: list[ColumnElement[bool]] = [
        and_(
            MsgNotice.target_scope.in_([TargetScope.ALL.value, TargetScope.ACCOUNT_TYPE.value]),
            type_match,
        )
    ]
    if account_id:
        clauses.append(
            and_(
                MsgNotice.target_scope == TargetScope.SPECIFIC.value,
                cast(MsgNotice.target_account_ids, String).contains('"' + account_id + '"'),
            )
        )
    return or_(*clauses)


def _published_filters(
    *,
    account_type: str,
    account_id: str | None = None,
    kind: str | None = None,
) -> list[ColumnElement[bool]]:
    """构造已发布消息的通用过滤条件（含可见性、公告未过期判断）。"""
    now = datetime.now(UTC)
    filters: list[ColumnElement[bool]] = [
        MsgNotice.status == NoticeStatus.PUBLISHED.value,
        _visible_to_account(account_type, account_id),
        or_(
            MsgNotice.kind != NoticeKind.ANNOUNCEMENT.value,
            MsgNotice.expire_at.is_(None),
            MsgNotice.expire_at > now,
        ),
    ]
    if kind:
        filters.append(MsgNotice.kind == kind.upper())
    return filters


class MsgNoticeRepository:
    """消息通知数据仓储，负责 MsgNotice 与阅读记录的持久化查询。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: MsgNoticeCreateRequest) -> MsgNotice:
        """创建消息记录。"""
        entity = MsgNotice(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, entity_id: str) -> MsgNotice | None:
        """按主键查询消息，不存在时返回 None。"""
        return await self.db.get(MsgNotice, entity_id)

    async def get_required(self, entity_id: str) -> MsgNotice:
        """按主键查询消息，不存在时抛出 NotFoundError。"""
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError("MsgNotice not found")
        return entity

    async def update(self, payload: MsgNoticeUpdateRequest) -> None:
        """按载荷字段更新消息（id 除外）。"""
        entity = await self.get_required(payload.id)
        for key, value in payload.model_dump(exclude={"id"}).items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, entity_ids: list[str]) -> None:
        """批量删除消息，并级联清理其阅读记录。"""
        unique_ids = list(dict.fromkeys(entity_ids))
        stmt = select(MsgNotice.id).where(MsgNotice.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("MsgNotice not found")
        await self.db.execute(delete(MsgNoticeRead).where(MsgNoticeRead.notice_id.in_(unique_ids)))
        await self.db.execute(delete(MsgNotice).where(MsgNotice.id.in_(unique_ids)))

    async def publish_many(
        self,
        entity_ids: list[str],
        *,
        now: datetime,
        sender_account_type: str,
        sender_account_id: str,
    ) -> None:
        """批量发布消息：分批校验 ID 均存在，再逐批单条 UPDATE 落库。

        替代逐条 SELECT+UPDATE 的循环，避免 N+1；IN 分批规避变量上限。
        """
        unique_ids = list(dict.fromkeys(entity_ids))
        if not unique_ids:
            return
        for batch in chunked(unique_ids):
            existing_ids = set(
                (
                    await self.db.execute(
                        select(MsgNotice.id).where(MsgNotice.id.in_(batch))
                    )
                )
                .scalars()
                .all()
            )
            if len(existing_ids) != len(batch):
                raise NotFoundError("MsgNotice not found")
            await self.db.execute(
                update(MsgNotice)
                .where(MsgNotice.id.in_(batch))
                .values(
                    status=NoticeStatus.PUBLISHED.value,
                    publish_at=now,
                    sender_account_type=sender_account_type,
                    sender_account_id=sender_account_id,
                )
            )
        await self.db.flush()

    async def revoke_many(self, entity_ids: list[str], *, now: datetime) -> None:
        """批量撤回消息：分批校验 ID 均存在，再逐批单条 UPDATE 落库。"""
        unique_ids = list(dict.fromkeys(entity_ids))
        if not unique_ids:
            return
        for batch in chunked(unique_ids):
            existing_ids = set(
                (
                    await self.db.execute(
                        select(MsgNotice.id).where(MsgNotice.id.in_(batch))
                    )
                )
                .scalars()
                .all()
            )
            if len(existing_ids) != len(batch):
                raise NotFoundError("MsgNotice not found")
            await self.db.execute(
                update(MsgNotice)
                .where(MsgNotice.id.in_(batch))
                .values(status=NoticeStatus.REVOKED.value, revoked_at=now)
            )
        await self.db.flush()

    async def page_admin(self, query: MsgNoticeAdminPageQuery) -> tuple[list[MsgNotice], int]:
        """管理端分页查询消息，支持标题/状态/类型过滤。"""
        stmt: Select[tuple[MsgNotice]] = select(MsgNotice)
        count_stmt = select(func.count(MsgNotice.id))
        filters = []
        if query.title:
            filters.append(MsgNotice.title.ilike(f"%{query.title}%"))
        if query.status is not None:
            filters.append(MsgNotice.status == query.status)
        if query.kind:
            filters.append(MsgNotice.kind == query.kind.upper())
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = stmt.order_by(MsgNotice.id.desc()).offset(query.offset).limit(query.size)
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total

    async def page_my(
        self,
        query: MyNoticePageQuery,
        account_type: str,
        account_id: str | None = None,
        *,
        kind: str | None = None,
    ) -> tuple[list[MsgNotice], int, set[str]]:
        """分页查询对当前账户可见的消息，并返回已读 ID 集合。"""
        published = _published_filters(
            account_type=account_type,
            account_id=account_id,
            kind=kind or query.kind,
        )
        stmt: Select[tuple[MsgNotice]] = select(MsgNotice).where(*published)
        count_stmt = select(func.count(MsgNotice.id)).where(*published)
        stmt = (
            stmt.order_by(MsgNotice.is_pinned.desc(), MsgNotice.publish_at.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()

        read_id_set: set[str] = set()
        if items and account_id:
            notice_ids = [item.id for item in items]
            read_stmt = select(MsgNoticeRead.notice_id).where(
                MsgNoticeRead.notice_id.in_(notice_ids),
                MsgNoticeRead.account_type == account_type,
                MsgNoticeRead.account_id == account_id,
            )
            read_id_set = set((await self.db.execute(read_stmt)).scalars().all())
        return items, total, read_id_set

    async def count_unread(self, account_type: str, account_id: str) -> int:
        """统计当前账户可见消息中的未读数量。"""
        published_stmt = select(MsgNotice.id).where(
            *_published_filters(account_type=account_type, account_id=account_id)
        )
        published_ids = {str(v) for v in (await self.db.execute(published_stmt)).scalars().all()}
        if not published_ids:
            return 0
        read_stmt = select(MsgNoticeRead.notice_id).where(
            MsgNoticeRead.account_type == account_type,
            MsgNoticeRead.account_id == account_id,
            MsgNoticeRead.notice_id.in_(list(published_ids)),
        )
        read_ids = set((await self.db.execute(read_stmt)).scalars().all())
        return len(published_ids - read_ids)

    async def mark_read(self, ids: list[str], account_type: str, account_id: str) -> None:
        """将指定消息标记为当前账户已读（幂等，跳过已读项）。"""
        unique_ids = list(dict.fromkeys(ids))
        existing_stmt = select(MsgNoticeRead.notice_id).where(
            MsgNoticeRead.notice_id.in_(unique_ids),
            MsgNoticeRead.account_type == account_type,
            MsgNoticeRead.account_id == account_id,
        )
        existing_ids = set((await self.db.execute(existing_stmt)).scalars().all())
        new_ids = [nid for nid in unique_ids if nid not in existing_ids]
        for notice_id in new_ids:
            self.db.add(
                MsgNoticeRead(
                    notice_id=notice_id,
                    account_type=account_type,
                    account_id=account_id,
                )
            )
        if new_ids:
            await self.db.flush()

    async def mark_all_read(self, account_type: str, account_id: str) -> None:
        """将当前账户全部可见消息标记为已读。"""
        published_stmt = select(MsgNotice.id).where(
            *_published_filters(account_type=account_type, account_id=account_id)
        )
        published_ids = [str(v) for v in (await self.db.execute(published_stmt)).scalars().all()]
        if not published_ids:
            return
        existing_stmt = select(MsgNoticeRead.notice_id).where(
            MsgNoticeRead.notice_id.in_(published_ids),
            MsgNoticeRead.account_type == account_type,
            MsgNoticeRead.account_id == account_id,
        )
        existing_ids = set((await self.db.execute(existing_stmt)).scalars().all())
        new_ids = [nid for nid in published_ids if nid not in existing_ids]
        for notice_id in new_ids:
            self.db.add(
                MsgNoticeRead(
                    notice_id=notice_id,
                    account_type=account_type,
                    account_id=account_id,
                )
            )
        if new_ids:
            await self.db.flush()

    async def increment_view_count(self, entity_id: str) -> None:
        """公告被查看时自增其查看次数。"""
        await self.db.execute(
            update(MsgNotice)
            .where(
                MsgNotice.id == entity_id,
                MsgNotice.kind == NoticeKind.ANNOUNCEMENT.value,
            )
            .values(view_count=MsgNotice.view_count + 1)
        )
        await self.db.flush()
