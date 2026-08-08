""" Author: Charlie

由 HEI 代码生成器生成。
Author: jiangbyte
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
from app.modules.message.feedback.schema import (
    MsgFeedbackAdminPageQuery,
    MsgFeedbackCreateRequest,
    MsgFeedbackSchema,
    MsgFeedbackUpdateRequest,
    MyFeedbackPageQuery,
)
from app.modules.message.feedback.service import MsgFeedbackService

admin_router = APIRouter()
portal_router = APIRouter()


# ==================== 管理端 CRUD ====================


@admin_router.get(
    "/v1/admin/message/feedbacks/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("message:feedback:page")),
    ],
    response_model=ApiResponse[PageData[MsgFeedbackSchema]],
)
async def page(
    query: Annotated[MsgFeedbackAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[MsgFeedbackSchema]]:
    return success(await MsgFeedbackService(db).page_admin(query))


@admin_router.get(
    "/v1/admin/message/feedbacks/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("message:feedback:detail")),
    ],
    response_model=ApiResponse[MsgFeedbackSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[MsgFeedbackSchema]:
    return success(await MsgFeedbackService(db).detail(query))


@admin_router.post(
    "/v1/admin/message/feedbacks/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("message:feedback:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: MsgFeedbackUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await MsgFeedbackService(db).update(payload, session)
    return success()


@admin_router.post(
    "/v1/admin/message/feedbacks/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("message:feedback:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await MsgFeedbackService(db).delete(payload)
    return success()


# ==================== 当前用户「我的反馈」（admin / portal） ====================


@admin_router.post(
    "/v1/admin/message/feedbacks/submit",
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
    response_model=ApiResponse[None],
)
async def admin_submit(
    payload: MsgFeedbackCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await MsgFeedbackService(db).submit(payload, session)
    return success()


@admin_router.get(
    "/v1/admin/message/feedbacks/my-page",
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
    response_model=ApiResponse[PageData[MsgFeedbackSchema]],
)
async def admin_my_page(
    query: Annotated[MyFeedbackPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[PageData[MsgFeedbackSchema]]:
    return success(await MsgFeedbackService(db).page_my(query, session))


@admin_router.get(
    "/v1/admin/message/feedbacks/my-detail",
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
    response_model=ApiResponse[MsgFeedbackSchema],
)
async def admin_my_detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[MsgFeedbackSchema]:
    return success(await MsgFeedbackService(db).detail_my(query, session))


@portal_router.post(
    "/v1/portal/message/feedbacks/submit",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[None],
)
async def submit(
    payload: MsgFeedbackCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await MsgFeedbackService(db).submit(payload, session)
    return success()


@portal_router.get(
    "/v1/portal/message/feedbacks/my-page",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[PageData[MsgFeedbackSchema]],
)
async def my_page(
    query: Annotated[MyFeedbackPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[PageData[MsgFeedbackSchema]]:
    return success(await MsgFeedbackService(db).page_my(query, session))


@portal_router.get(
    "/v1/portal/message/feedbacks/my-detail",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[MsgFeedbackSchema],
)
async def my_detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[MsgFeedbackSchema]:
    return success(await MsgFeedbackService(db).detail_my(query, session))
