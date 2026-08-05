from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response.schema import ApiResponse, success
from app.core.schema.base import IdQuery
from app.deps.db import get_db_session
from app.modules.sys.banner.schema import (
    BannerPublicListQuery,
    SysBannerSchema,
)
from app.modules.sys.banner.service import BannerService

router = APIRouter()


@router.get("/sys/banners/list", response_model=ApiResponse[list[SysBannerSchema]])
async def list_public_banners(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[BannerPublicListQuery, Depends()],
) -> ApiResponse[list[SysBannerSchema]]:
    return success(await BannerService(db).list_public(query))


@router.post("/sys/banners/interaction", response_model=ApiResponse[None])
async def record_banner_interaction(
    payload: IdQuery,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await BannerService(db).record_interaction(payload)
    return success()
