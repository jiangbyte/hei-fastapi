from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData
from app.core.response.schema import ApiResponse, success
from app.deps.auth import require_permission, require_account_type
from app.deps.db import get_db_session
from app.modules.sys.dict.schema import (
    DictAdminPageQuery,
    DictCreateRequest,
    DictIdQuery,
    DictIdsRequest,
    DictTreeQuery,
    DictUpdateRequest,
    SysDictSchema,
    SysDictTreeNode,
)
from app.modules.sys.dict.service import DictService

router = APIRouter()


@router.post(
    "/sys/dicts/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:dict:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: DictCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await DictService(db).create(payload)
    return success()


@router.post(
    "/sys/dicts/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:dict:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: DictUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await DictService(db).update(payload)
    return success()


@router.post(
    "/sys/dicts/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:dict:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: DictIdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await DictService(db).delete(payload)
    return success()


@router.get(
    "/sys/dicts/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:dict:detail")),
    ],
    response_model=ApiResponse[SysDictSchema],
)
async def get(
    query: Annotated[DictIdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SysDictSchema]:
    return success(await DictService(db).get(query))


@router.get(
    "/sys/dicts/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:dict:page")),
    ],
    response_model=ApiResponse[PageData[SysDictSchema]],
)
async def page(
    query: Annotated[DictAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[SysDictSchema]]:
    return success(await DictService(db).page_admin(query))


@router.get(
    "/sys/dicts/tree",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL)),
        # Depends(require_permission("sys:dict:tree")),
    ],
    response_model=ApiResponse[list[SysDictTreeNode]],
)
async def tree(
    query: Annotated[DictTreeQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SysDictTreeNode]]:
    return success(await DictService(db).list_tree(query))
