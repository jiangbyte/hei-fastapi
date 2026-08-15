""" Author: Charlie

弱密码库管理端接口：弱密码的增删改查与列表（无业务层，直接走仓储）。
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData, build_page
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.deps.auth import require_account_type, require_permission
from app.deps.db import get_db_session
from app.modules.sys.weak_password.repository import WeakPasswordRepository
from app.modules.sys.weak_password.schema import (
    SysWeakPasswordSchema,
    WeakPasswordAdminPageQuery,
    WeakPasswordCreateRequest,
    WeakPasswordListQuery,
    WeakPasswordUpdateRequest,
)

router = APIRouter()


@router.post(
    "/v1/admin/sys/weak-password/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:weakpassword:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: WeakPasswordCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    """新增弱密码。"""
    await WeakPasswordRepository(db).create(payload)
    return success()


@router.post(
    "/v1/admin/sys/weak-password/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:weakpassword:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: WeakPasswordUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    """更新弱密码。"""
    await WeakPasswordRepository(db).update(payload)
    return success()


@router.post(
    "/v1/admin/sys/weak-password/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:weakpassword:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    """批量删除弱密码。"""
    await WeakPasswordRepository(db).delete_many(payload.ids)
    return success()


@router.get(
    "/v1/admin/sys/weak-password/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:weakpassword:detail")),
    ],
    response_model=ApiResponse[SysWeakPasswordSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SysWeakPasswordSchema]:
    """查询弱密码详情。"""
    return success(
        to_schema(SysWeakPasswordSchema, await WeakPasswordRepository(db).get_required(query.id))
    )


@router.get(
    "/v1/admin/sys/weak-password/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:weakpassword:page")),
    ],
    response_model=ApiResponse[PageData[SysWeakPasswordSchema]],
)
async def page(
    query: Annotated[WeakPasswordAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[SysWeakPasswordSchema]]:
    """分页查询弱密码。"""
    items, total = await WeakPasswordRepository(db).page_admin(query)
    return success(build_page(query, total, to_schema_list(SysWeakPasswordSchema, items)))


@router.get(
    "/v1/admin/sys/weak-password/list",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:weakpassword:list")),
    ],
    response_model=ApiResponse[list[SysWeakPasswordSchema]],
)
async def list_all(
    query: Annotated[WeakPasswordListQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SysWeakPasswordSchema]]:
    """列出全部弱密码。"""
    items = await WeakPasswordRepository(db).list_all(query)
    return success(to_schema_list(SysWeakPasswordSchema, items))
