""" Author: Charlie

仪表盘路由：提供管理端概览数据接口。
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.schema import ApiResponse, success
from app.deps.auth import require_account_type, require_permission
from app.deps.db import get_db_session
from app.modules.dashboard.schema import DashboardOverviewResponse
from app.modules.dashboard.service import DashboardService

router = APIRouter()


@router.get(
    "/v1/admin/dashboard/overview",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("dashboard:overview:view")),
    ],
    response_model=ApiResponse[DashboardOverviewResponse],
)
async def overview(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DashboardOverviewResponse]:
    """管理端仪表盘概览数据。"""
    return success(await DashboardService(db).overview())
