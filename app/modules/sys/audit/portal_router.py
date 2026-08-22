""" Author: Charlie

门户端操作审计：当前用户本人日志查询。
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import IdQuery
from app.core.security.session import SessionPayload
from app.deps.auth import get_current_session, require_account_type
from app.deps.db import get_db_session
from app.modules.sys.audit.schema import OperationAuditPageQuery, OperationAuditRecord
from app.modules.sys.audit.service import OperationAuditService

router = APIRouter()


@router.get(
    "/v1/portal/sys/audit/my-page",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[PageData[OperationAuditRecord]],
    response_model_exclude_none=False,
)
async def my_page(
    query: Annotated[OperationAuditPageQuery, Depends()],
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[OperationAuditRecord]]:
    """当前门户用户本人审计日志分页。"""
    return success(
        await OperationAuditService(db).my_page(query, session.account_id)
    )


@router.get(
    "/v1/portal/sys/audit/my-detail",
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
    response_model=ApiResponse[OperationAuditRecord],
    response_model_exclude_none=False,
)
async def my_detail(
    query: Annotated[IdQuery, Depends()],
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[OperationAuditRecord]:
    """当前门户用户本人审计详情。"""
    return success(
        await OperationAuditService(db).my_detail(query.id, session.account_id)
    )
