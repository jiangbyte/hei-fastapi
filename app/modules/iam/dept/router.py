""" Author: Charlie """

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
from app.modules.iam.dept.schema import (
    DeptAdminPageQuery,
    DeptCreateRequest,
    DeptTreeNode,
    DeptUpdateRequest,
    SysDeptSchema,
)
from app.modules.iam.dept.service import DeptService

router = APIRouter()


@router.post(
    "/v1/admin/sys/depts/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:dept:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: DeptCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await DeptService(db).create(payload, session)
    return success()


@router.post(
    "/v1/admin/sys/depts/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:dept:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: DeptUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await DeptService(db).update(payload, session)
    return success()


@router.post(
    "/v1/admin/sys/depts/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:dept:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await DeptService(db).delete(payload, session)
    return success()


@router.get(
    "/v1/admin/sys/depts/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:dept:detail")),
    ],
    response_model=ApiResponse[SysDeptSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[SysDeptSchema]:
    return success(await DeptService(db).detail(query, session))


@router.get(
    "/v1/admin/sys/depts/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:dept:page")),
    ],
    response_model=ApiResponse[PageData[SysDeptSchema]],
)
async def page(
    query: Annotated[DeptAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[PageData[SysDeptSchema]]:
    return success(await DeptService(db).page_admin(query, session))


@router.get(
    "/v1/admin/sys/depts/tree",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:dept:list")),
    ],
    response_model=ApiResponse[list[DeptTreeNode]],
)
async def list_dept_tree(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[list[DeptTreeNode]]:
    return success(await DeptService(db).list_dept_tree(session))
