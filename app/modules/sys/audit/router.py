""" Author: Charlie

操作审计后台接口：分页查询与详情查询，仅管理员可访问。
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import IdQuery
from app.deps.auth import require_account_type, require_permission
from app.deps.db import get_db_session
from app.modules.sys.audit.schema import OperationAuditPageQuery, OperationAuditRecord
from app.modules.sys.audit.service import OperationAuditService

router = APIRouter()


@router.get(
    "/v1/admin/sys/audit/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:audit:page")),
    ],
    response_model=ApiResponse[PageData[OperationAuditRecord]],
)
async def page(
    query: Annotated[OperationAuditPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[OperationAuditRecord]]:
    """后台分页查询操作审计日志。"""
    return success(await OperationAuditService(db).page_admin(query))


@router.get(
    "/v1/admin/sys/audit/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:audit:detail")),
    ],
    response_model=ApiResponse[OperationAuditRecord],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[OperationAuditRecord]:
    """按主键查询单条操作审计日志详情。"""
    return success(await OperationAuditService(db).detail(query))
