from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import IdQuery, IdsRequest
from app.deps.auth import require_permission, require_account_type
from app.deps.db import get_db_session
from app.modules.sys.banner.schema import (
    BannerAdminPageQuery,
    BannerCreateRequest,
    BannerUpdateRequest,
    SysBannerSchema,
)
from app.modules.sys.banner.service import BannerService

router = APIRouter()


@router.post(
    "/sys/banners/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:banner:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: BannerCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await BannerService(db).create(payload)
    return success()


@router.post(
    "/sys/banners/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:banner:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: BannerUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await BannerService(db).update(payload)
    return success()


@router.post(
    "/sys/banners/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:banner:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await BannerService(db).delete(payload)
    return success()


@router.get(
    "/sys/banners/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:banner:detail")),
    ],
    response_model=ApiResponse[SysBannerSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SysBannerSchema]:
    return success(await BannerService(db).detail(query))


@router.get(
    "/sys/banners/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:banner:page")),
    ],
    response_model=ApiResponse[PageData[SysBannerSchema]],
)
async def page(
    query: Annotated[BannerAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[SysBannerSchema]]:
    return success(await BannerService(db).page_admin(query))
