from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData
from app.core.response.schema import ApiResponse, success
from app.deps.auth import require_account_type, require_permission
from app.deps.db import get_db_session
from app.modules.auth.session_admin_service import SessionAdminService
from app.modules.auth.session_schema import (
    SessionAccountItem,
    SessionAnalysisResponse,
    SessionExitRequest,
    SessionPageQuery,
    SessionTokenExitRequest,
    SessionTokenInfo,
    SessionTokensQuery,
)

router = APIRouter()


@router.get(
    "/auth/sessions/analysis",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("auth:session:analysis")),
    ],
    response_model=ApiResponse[SessionAnalysisResponse],
)
async def analysis(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SessionAnalysisResponse]:
    return success(await SessionAdminService(db).analysis())


@router.get(
    "/auth/sessions/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("auth:session:page")),
    ],
    response_model=ApiResponse[PageData[SessionAccountItem]],
)
async def page(
    query: Annotated[SessionPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[SessionAccountItem]]:
    return success(await SessionAdminService(db).page(query))


@router.get(
    "/auth/sessions/tokens",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("auth:session:tokenlist")),
    ],
    response_model=ApiResponse[list[SessionTokenInfo]],
)
async def tokens(
    query: Annotated[SessionTokensQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SessionTokenInfo]]:
    return success(await SessionAdminService(db).tokens(query))


@router.post(
    "/auth/sessions/exit",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("auth:session:exit")),
    ],
    response_model=ApiResponse[None],
)
async def exit_sessions(
    payload: SessionExitRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await SessionAdminService(db).exit_sessions(payload.targets)
    return success()


@router.post(
    "/auth/sessions/token/exit",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("auth:session:tokenexit")),
    ],
    response_model=ApiResponse[None],
)
async def exit_tokens(
    payload: SessionTokenExitRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await SessionAdminService(db).exit_tokens(payload.tokens)
    return success()
