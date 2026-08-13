""" Author: Charlie

门户资源 HTTP 路由：向 Portal 端公开当前可见资源。
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response.schema import ApiResponse, success
from app.deps.db import get_db_session
from app.modules.iam.resource.schema import SysResourceSchema
from app.modules.iam.resource.service import ResourceService

router = APIRouter()


@router.get(
    "/v1/portal/sys/resources/current",
    response_model=ApiResponse[list[SysResourceSchema]],
)
async def current_resources(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SysResourceSchema]]:
    return success(await ResourceService(db).list_public_portal_resources())
