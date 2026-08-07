""" Author: Charlie """

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData
from app.core.response.schema import ApiResponse, success
from app.core.security.session import SessionPayload
from app.deps.auth import get_current_session, require_account_type
from app.deps.db import get_db_session
from app.modules.message.message.schema import (
    MessagePageQuery,
    MessageReadRequest,
    MessageSchema,
    MessageUnreadCountQuery,
    RevokeMessageRequest,
    SendMessageRequest,
    UnreadCountResponse,
)
from app.modules.message.message.service import MessageService

admin_router = APIRouter()
portal_router = APIRouter()


def register_current_user_routes(router: APIRouter, account_type: AccountType) -> None:
    deps = [Depends(require_account_type(account_type))]
    base = f"/v1/{account_type.value.lower()}/message/messages"

    @router.post(f"{base}/send", dependencies=deps, response_model=ApiResponse[MessageSchema])
    async def send(
        payload: SendMessageRequest,
        session: Annotated[SessionPayload, Depends(get_current_session)],
        db: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> ApiResponse[MessageSchema]:
        return success(await MessageService(db).send(payload, session))

    @router.post(f"{base}/reply", dependencies=deps, response_model=ApiResponse[MessageSchema])
    async def reply(
        payload: SendMessageRequest,
        session: Annotated[SessionPayload, Depends(get_current_session)],
        db: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> ApiResponse[MessageSchema]:
        return success(await MessageService(db).reply(payload, session))

    @router.post(f"{base}/revoke", dependencies=deps, response_model=ApiResponse[None])
    async def revoke(
        payload: RevokeMessageRequest,
        session: Annotated[SessionPayload, Depends(get_current_session)],
        db: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> ApiResponse[None]:
        await MessageService(db).revoke(payload, session)
        return success()

    @router.post(f"{base}/read", dependencies=deps, response_model=ApiResponse[None])
    async def read(
        payload: MessageReadRequest,
        session: Annotated[SessionPayload, Depends(get_current_session)],
        db: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> ApiResponse[None]:
        await MessageService(db).mark_read(payload, session)
        return success()

    @router.get(
        f"{base}/page", dependencies=deps, response_model=ApiResponse[PageData[MessageSchema]]
    )
    async def page(
        query: Annotated[MessagePageQuery, Depends()],
        session: Annotated[SessionPayload, Depends(get_current_session)],
        db: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> ApiResponse[PageData[MessageSchema]]:
        return success(await MessageService(db).page_messages(query, session))

    @router.get(
        f"{base}/unread-count",
        dependencies=deps,
        response_model=ApiResponse[UnreadCountResponse],
    )
    async def unread_count(
        query: Annotated[MessageUnreadCountQuery, Depends()],
        session: Annotated[SessionPayload, Depends(get_current_session)],
        db: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> ApiResponse[UnreadCountResponse]:
        return success(await MessageService(db).unread_count(query, session))


register_current_user_routes(admin_router, AccountType.ADMIN)
register_current_user_routes(portal_router, AccountType.PORTAL)
