"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:48
"""

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.message.terminal.model import (
    MsgTerminal,
)
from app.modules.message.terminal.schema import (
    MsgTerminalAdminPageQuery,
    MsgTerminalCreateRequest,
    MsgTerminalUpdateRequest,
)


class MsgTerminalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: MsgTerminalCreateRequest) -> MsgTerminal:
        entity = MsgTerminal(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, entity_id: str) -> MsgTerminal | None:
        return await self.db.get(MsgTerminal, entity_id)

    async def get_required(self, entity_id: str) -> MsgTerminal:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError("MsgTerminal not found")
        return entity

    async def update(self, payload: MsgTerminalUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        for key, value in payload.model_dump(exclude={"id"}).items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, entity_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(entity_ids))
        stmt = select(MsgTerminal.id).where(MsgTerminal.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("MsgTerminal not found")
        await self.db.execute(delete(MsgTerminal).where(MsgTerminal.id.in_(unique_ids)))

    async def page_admin(self, query: MsgTerminalAdminPageQuery) -> tuple[list[MsgTerminal], int]:
        stmt: Select[tuple[MsgTerminal]] = select(MsgTerminal)
        count_stmt = select(func.count(MsgTerminal.id))
        filters = []
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(MsgTerminal.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total

    async def find_by_device(
        self, account_type: str, account_id: str, device_type: str, device_id: str
    ) -> MsgTerminal | None:
        stmt = select(MsgTerminal).where(
            MsgTerminal.account_type == account_type,
            MsgTerminal.account_id == account_id,
            MsgTerminal.device_type == device_type,
            MsgTerminal.device_id == device_id,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_by_account(self, account_type: str, account_id: str) -> list[MsgTerminal]:
        stmt = select(MsgTerminal).where(
            MsgTerminal.account_type == account_type,
            MsgTerminal.account_id == account_id,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def set_online(self, terminal_id: str, online: bool) -> None:
        stmt = update(MsgTerminal).where(MsgTerminal.id == terminal_id).values(is_online=online)
        await self.db.execute(stmt)

    async def mark_all_offline(self, account_type: str, account_id: str) -> None:
        stmt = (
            update(MsgTerminal)
            .where(
                MsgTerminal.account_type == account_type,
                MsgTerminal.account_id == account_id,
            )
            .values(is_online=False)
        )
        await self.db.execute(stmt)

    async def any_online(self, account_type: str, account_id: str) -> bool:
        stmt = (
            select(MsgTerminal.id)
            .where(
                MsgTerminal.account_type == account_type,
                MsgTerminal.account_id == account_id,
                MsgTerminal.is_online,
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first() is not None
