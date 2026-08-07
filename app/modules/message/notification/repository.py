"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:50
"""

from datetime import datetime

from sqlalchemy import Select, String, cast, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.message.enums import NotificationStatus, TargetScope
from app.modules.message.notification.model import (
    MsgNotification,
    MsgNotificationRead,
)
from app.modules.message.notification.schema import (
    MsgNotificationAdminPageQuery,
    MsgNotificationCreateRequest,
    MsgNotificationUpdateRequest,
    MyNotificationPageQuery,
)


class MsgNotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: MsgNotificationCreateRequest) -> MsgNotification:
        entity = MsgNotification(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, entity_id: str) -> MsgNotification | None:
        return await self.db.get(MsgNotification, entity_id)

    async def get_required(self, entity_id: str) -> MsgNotification:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError("MsgNotification not found")
        return entity

    async def update(self, payload: MsgNotificationUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        for key, value in payload.model_dump(exclude={"id"}).items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, entity_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(entity_ids))
        stmt = select(MsgNotification.id).where(MsgNotification.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("MsgNotification not found")
        await self.db.execute(delete(MsgNotification).where(MsgNotification.id.in_(unique_ids)))

    async def page_admin(
        self, query: MsgNotificationAdminPageQuery
    ) -> tuple[list[MsgNotification], int]:
        stmt: Select[tuple[MsgNotification]] = select(MsgNotification)
        count_stmt = select(func.count(MsgNotification.id))
        filters = []
        if query.title:
            filters.append(MsgNotification.title.ilike(f"%{query.title}%"))
        if query.category:
            filters.append(MsgNotification.category.ilike(f"%{query.category}%"))
        if query.status is not None:
            filters.append(MsgNotification.status == query.status)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(MsgNotification.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total

    async def page_my_notifications(
        self, query: MyNotificationPageQuery, account_type: str, account_id: str
    ) -> tuple[list[MsgNotification], int, set[str]]:
        """返回 (items, total, read_id_set)。仅 PUBLISHED 且符合目标范围、对给定账户可见的通知。"""
        stmt: Select[tuple[MsgNotification]] = select(MsgNotification)
        filters = [MsgNotification.status == NotificationStatus.PUBLISHED]

        filters.append(
            MsgNotification.target_scope.in_(
                [
                    TargetScope.ALL,
                    TargetScope.ACCOUNT_TYPE,
                ]
            )
        )
        filters.append(
            (func.json_array_length(MsgNotification.target_account_types) == 0)
            | cast(MsgNotification.target_account_types, String).contains('"' + account_type + '"')
        )

        if query.category:
            filters.append(MsgNotification.category == query.category)

        count_stmt = select(func.count(MsgNotification.id)).where(*filters)
        stmt = (
            stmt.where(*filters)
            .order_by(MsgNotification.publish_at.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()

        read_id_set: set[str] = set()
        if items:
            notification_ids = [item.id for item in items]
            read_stmt = select(MsgNotificationRead.notification_id).where(
                MsgNotificationRead.notification_id.in_(notification_ids),
                MsgNotificationRead.account_type == account_type,
                MsgNotificationRead.account_id == account_id,
            )
            read_id_set = {row for row in (await self.db.execute(read_stmt)).scalars().all()}

        return items, total, read_id_set

    async def count_unread(self, account_type: str, account_id: str) -> int:
        """统计账户可见的 PUBLISHED 通知数，减去已读。"""
        published_stmt = select(func.count(MsgNotification.id)).where(
            MsgNotification.status == NotificationStatus.PUBLISHED,
            MsgNotification.target_scope.in_([TargetScope.ALL, TargetScope.ACCOUNT_TYPE]),
            (func.json_array_length(MsgNotification.target_account_types) == 0)
            | cast(MsgNotification.target_account_types, String).contains('"' + account_type + '"'),
        )
        published_total = (await self.db.execute(published_stmt)).scalar_one()

        read_stmt = select(func.count(MsgNotificationRead.id)).where(
            MsgNotificationRead.account_type == account_type,
            MsgNotificationRead.account_id == account_id,
        )
        read_total = (await self.db.execute(read_stmt)).scalar_one()

        return published_total - read_total

    async def mark_read(
        self, notification_ids: list[str], account_type: str, account_id: str
    ) -> None:
        """批量插入已读记录，跳过已存在项（唯一约束）。"""
        now = datetime.utcnow()
        values = [
            {
                "notification_id": nid,
                "account_type": account_type,
                "account_id": account_id,
                "read_at": now,
            }
            for nid in notification_ids
        ]
        if not values:
            return
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = (
            pg_insert(MsgNotificationRead)
            .values(values)
            .on_conflict_do_nothing(
                index_elements=["notification_id", "account_type", "account_id"],
            )
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def mark_all_read(self, account_type: str, account_id: str) -> None:
        """将账户可见的全部 PUBLISHED 通知标记为已读。"""
        published_ids_stmt = select(MsgNotification.id).where(
            MsgNotification.status == NotificationStatus.PUBLISHED,
            MsgNotification.target_scope.in_([TargetScope.ALL, TargetScope.ACCOUNT_TYPE]),
            (func.json_array_length(MsgNotification.target_account_types) == 0)
            | cast(MsgNotification.target_account_types, String).contains('"' + account_type + '"'),
        )
        published_ids = list((await self.db.execute(published_ids_stmt)).scalars().all())
        if not published_ids:
            return
        await self.mark_read(published_ids, account_type, account_id)
