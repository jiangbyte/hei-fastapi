""" Author: Charlie """

from datetime import UTC, datetime

from sqlalchemy import Select, String, and_, cast, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

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
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: MsgNoticeCreateRequest) -> MsgNotice:
        entity = MsgNotice(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, entity_id: str) -> MsgNotice | None:
        return await self.db.get(MsgNotice, entity_id)

    async def get_required(self, entity_id: str) -> MsgNotice:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError("MsgNotice not found")
        return entity

    async def update(self, payload: MsgNoticeUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        for key, value in payload.model_dump(exclude={"id"}).items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, entity_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(entity_ids))
        stmt = select(MsgNotice.id).where(MsgNotice.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("MsgNotice not found")
        await self.db.execute(delete(MsgNoticeRead).where(MsgNoticeRead.notice_id.in_(unique_ids)))
        await self.db.execute(delete(MsgNotice).where(MsgNotice.id.in_(unique_ids)))

    async def page_admin(self, query: MsgNoticeAdminPageQuery) -> tuple[list[MsgNotice], int]:
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
        await self.db.execute(
            update(MsgNotice)
            .where(
                MsgNotice.id == entity_id,
                MsgNotice.kind == NoticeKind.ANNOUNCEMENT.value,
            )
            .values(view_count=MsgNotice.view_count + 1)
        )
        await self.db.flush()
