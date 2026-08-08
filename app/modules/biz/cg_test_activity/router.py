"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-08-08 21:09:52
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import (
    IdQuery,
    IdsRequest,
)
from app.core.security.session import SessionPayload
from app.deps.auth import get_current_session, require_account_type, require_permission
from app.deps.db import get_db_session
from app.modules.biz.cg_test_activity.schema import (
    CgTestActivityAdminPageQuery,
    CgTestActivityCreateRequest,
    CgTestActivitySchema,
    CgTestActivityUpdateRequest,
)
from app.modules.biz.cg_test_activity.service import (
    CgTestActivityService,
)

router = APIRouter()


@router.post(
    "/v1/admin/biz/cg-test-activity/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("biz:cgtestactivity:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: CgTestActivityCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await CgTestActivityService(db).create(payload, session=session)
    return success()


@router.post(
    "/v1/admin/biz/cg-test-activity/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("biz:cgtestactivity:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: CgTestActivityUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await CgTestActivityService(db).update(payload)
    return success()


@router.post(
    "/v1/admin/biz/cg-test-activity/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("biz:cgtestactivity:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await CgTestActivityService(db).delete(payload)
    return success()


@router.get(
    "/v1/admin/biz/cg-test-activity/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("biz:cgtestactivity:detail")),
    ],
    response_model=ApiResponse[CgTestActivitySchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CgTestActivitySchema]:
    return success(await CgTestActivityService(db).detail(query))


@router.get(
    "/v1/admin/biz/cg-test-activity/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("biz:cgtestactivity:page")),
    ],
    response_model=ApiResponse[PageData[CgTestActivitySchema]],
)
async def page(
    query: Annotated[CgTestActivityAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[PageData[CgTestActivitySchema]]:
    return success(await CgTestActivityService(db).page_admin(query, session))
