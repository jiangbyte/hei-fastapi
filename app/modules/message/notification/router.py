"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:50
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import IdQuery, IdsRequest
from app.core.security.session import SessionPayload
from app.deps.auth import get_current_session, require_account_type, require_permission
from app.deps.db import get_db_session
from app.modules.message.notification.schema import (
    MsgNotificationAdminPageQuery,
    MsgNotificationCreateRequest,
    MsgNotificationSchema,
    MsgNotificationUpdateRequest,
    MyNotificationPageQuery,
    NotificationReadRequest,
)
from app.modules.message.notification.service import (
    MsgNotificationService,
)

admin_router = APIRouter()
portal_router = APIRouter()


# ── 管理端路由 ──────────────────────────────────────────────────────────────


@admin_router.post(
    "/v1/admin/message/notifications/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("message:notification:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: MsgNotificationCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await MsgNotificationService(db).create(payload)
    return success()


@admin_router.post(
    "/v1/admin/message/notifications/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("message:notification:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: MsgNotificationUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await MsgNotificationService(db).update(payload)
    return success()


@admin_router.post(
    "/v1/admin/message/notifications/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("message:notification:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await MsgNotificationService(db).delete(payload)
    return success()


@admin_router.get(
    "/v1/admin/message/notifications/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("message:notification:detail")),
    ],
    response_model=ApiResponse[MsgNotificationSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[MsgNotificationSchema]:
    return success(await MsgNotificationService(db).detail(query))


@admin_router.get(
    "/v1/admin/message/notifications/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("message:notification:page")),
    ],
    response_model=ApiResponse[PageData[MsgNotificationSchema]],
)
async def page(
    query: Annotated[MsgNotificationAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[MsgNotificationSchema]]:
    return success(await MsgNotificationService(db).page_admin(query))


@admin_router.post(
    "/v1/admin/message/notifications/publish",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("message:notification:publish")),
    ],
    response_model=ApiResponse[None],
)
async def publish(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await MsgNotificationService(db).publish(payload)
    return success()


@admin_router.post(
    "/v1/admin/message/notifications/revoke",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("message:notification:revoke")),
    ],
    response_model=ApiResponse[None],
)
async def revoke(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await MsgNotificationService(db).revoke(payload)
    return success()


# ── Portal / 当前用户路由 ──────────────────────────────────────────────


def register_current_user_routes(router: APIRouter, account_type: AccountType) -> None:
    """为当前已登录用户注册通知路由。"""
    base = f"/v1/{account_type.value.lower()}/message/notifications"
    deps = [Depends(require_account_type(account_type))]

    @router.get(
        f"{base}/my-page",
        dependencies=deps,
        response_model=ApiResponse[PageData[MsgNotificationSchema]],
    )
    async def my_page(
        query: Annotated[MyNotificationPageQuery, Depends()],
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[PageData[MsgNotificationSchema]]:
        return success(await MsgNotificationService(db).page_my_notifications(query, session))

    @router.get(
        f"{base}/my-detail",
        dependencies=deps,
        response_model=ApiResponse[MsgNotificationSchema],
    )
    async def my_detail(
        query: Annotated[IdQuery, Depends()],
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[MsgNotificationSchema]:
        return success(await MsgNotificationService(db).my_detail(query, session))

    @router.get(
        f"{base}/unread-count",
        dependencies=deps,
        response_model=ApiResponse[int],
    )
    async def unread_count(
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[int]:
        return success(await MsgNotificationService(db).count_unread(session))

    @router.post(
        f"{base}/read",
        dependencies=deps,
        response_model=ApiResponse[None],
    )
    async def read(
        payload: NotificationReadRequest,
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[None]:
        await MsgNotificationService(db).mark_read(payload, session)
        return success()

    @router.post(
        f"{base}/read-all",
        dependencies=deps,
        response_model=ApiResponse[None],
    )
    async def read_all(
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[None]:
        await MsgNotificationService(db).mark_all_read(session)
        return success()


register_current_user_routes(portal_router, AccountType.PORTAL)
register_current_user_routes(admin_router, AccountType.ADMIN)
