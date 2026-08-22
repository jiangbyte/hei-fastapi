""" Author: Charlie

工作台 API（对齐 hei-boot AdminWorkspaceController / AdminWorkspaceShortcutController）。
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.schema import ApiResponse, success
from app.core.security.session import SessionPayload
from app.deps.auth import get_current_session, require_account_type
from app.deps.db import get_db_session
from app.modules.workspace.schema import (
    WorkspaceOverviewResponse,
    WorkspaceShortcutResult,
    WorkspaceShortcutSaveRequest,
)
from app.modules.workspace.service import WorkspaceService

router = APIRouter()


@router.get(
    "/v1/admin/workspace/overview",
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
    response_model=ApiResponse[WorkspaceOverviewResponse],
)
async def overview(
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[WorkspaceOverviewResponse]:
    """工作台总览：快捷应用 + 本人近期操作/登录。"""
    return success(await WorkspaceService(db).overview(session))


@router.get(
    "/v1/admin/workspace/shortcuts",
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
    response_model=ApiResponse[list[WorkspaceShortcutResult]],
)
async def list_shortcuts(
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[WorkspaceShortcutResult]]:
    """查询当前用户快捷应用列表。"""
    return success(await WorkspaceService(db).list_shortcuts(session))


@router.post(
    "/v1/admin/workspace/shortcuts",
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
    response_model=ApiResponse[list[WorkspaceShortcutResult]],
)
async def save_shortcuts(
    payload: WorkspaceShortcutSaveRequest,
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[WorkspaceShortcutResult]]:
    """全量替换当前用户快捷应用。"""
    return success(await WorkspaceService(db).replace_shortcuts(session, payload))
