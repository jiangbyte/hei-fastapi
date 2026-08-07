"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:48
"""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.session import SessionPayload
from app.modules.message.terminal.repository import (
    MsgTerminalRepository,
)
from app.modules.message.terminal.schema import (
    MsgTerminalAdminPageQuery,
    MsgTerminalCreateRequest,
    MsgTerminalSchema,
    MsgTerminalUpdateRequest,
    PushTokenUpdateRequest,
    TerminalRegisterRequest,
)
from app.platform.db.transaction import transactional


class MsgTerminalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MsgTerminalRepository(db)

    async def create(self, payload: MsgTerminalCreateRequest) -> None:
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: MsgTerminalUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> MsgTerminalSchema:
        return to_schema(MsgTerminalSchema, await self.repo.get_required(query.id))

    async def page_admin(self, query: MsgTerminalAdminPageQuery) -> PageData[MsgTerminalSchema]:
        items, total = await self.repo.page_admin(query)
        return build_page(query, total, to_schema_list(MsgTerminalSchema, items))

    async def register(
        self, payload: TerminalRegisterRequest, session: SessionPayload
    ) -> MsgTerminalSchema:
        async with transactional(self.db):
            existing = await self.repo.find_by_device(
                account_type=str(session.account_type),
                account_id=session.account_id,
                device_type=payload.device_type,
                device_id=payload.device_id or "",
            )
            if existing:
                existing.device_name = payload.device_name
                existing.app_version = payload.app_version
                existing.is_online = True
                existing.last_login_at = datetime.now(UTC)
                await self.db.flush()
                return to_schema(MsgTerminalSchema, existing)

            create_payload = MsgTerminalCreateRequest(
                account_type=str(session.account_type),
                account_id=session.account_id,
                device_type=payload.device_type,
                device_name=payload.device_name,
                device_id=payload.device_id,
                app_version=payload.app_version,
                is_online=True,
                last_login_at=datetime.now(UTC),
                extra={},
            )
            entity = await self.repo.create(create_payload)
            return to_schema(MsgTerminalSchema, entity)

    async def unregister(self, entity_id: str, session: SessionPayload) -> None:
        async with transactional(self.db):
            entity = await self.repo.get_required(entity_id)
            if (
                entity.account_type != str(session.account_type)
                or entity.account_id != session.account_id
            ):
                raise NotFoundError("MsgTerminal not found")
            await self.repo.delete_many([entity_id])

    async def update_push_token(
        self, payload: PushTokenUpdateRequest, session: SessionPayload
    ) -> None:
        async with transactional(self.db):
            entity = await self.repo.get_required(payload.id)
            if (
                entity.account_type != str(session.account_type)
                or entity.account_id != session.account_id
            ):
                raise NotFoundError("MsgTerminal not found")
            entity.push_token = payload.push_token
            entity.push_provider = payload.push_provider
            await self.db.flush()

    async def my_list(self, session: SessionPayload) -> list[MsgTerminalSchema]:
        items = await self.repo.list_by_account(
            account_type=str(session.account_type),
            account_id=session.account_id,
        )
        return to_schema_list(MsgTerminalSchema, items)
