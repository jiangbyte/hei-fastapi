from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import IdQuery, IdsRequest
from app.deps.auth import require_account_type, require_permission
from app.deps.db import get_db_session
from app.modules.sys.config.storage_schema import (
    StorageConfigCreateRequest,
    StorageConfigSetDefaultRequest,
    StorageConfigUpdateRequest,
    SysStorageConfigSchema,
)
from app.modules.sys.config.storage_service import StorageConfigService

router = APIRouter()


@router.post(
    "/sys/storage-config/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: StorageConfigCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await StorageConfigService(db).create(payload)
    return success()


@router.post(
    "/sys/storage-config/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: StorageConfigUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await StorageConfigService(db).update(payload)
    return success()


@router.post(
    "/sys/storage-config/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await StorageConfigService(db).delete(payload)
    return success()


@router.get(
    "/sys/storage-config/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:page")),
    ],
    response_model=ApiResponse[SysStorageConfigSchema],
)
async def detail(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[IdQuery, Depends()],
) -> ApiResponse[SysStorageConfigSchema]:
    return success(await StorageConfigService(db).detail(query))


@router.get(
    "/sys/storage-config/list",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:page")),
    ],
    response_model=ApiResponse[list[SysStorageConfigSchema]],
)
async def list_config(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SysStorageConfigSchema]]:
    return success(await StorageConfigService(db).list_all())


@router.post(
    "/sys/storage-config/set-default",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:config:update")),
    ],
    response_model=ApiResponse[None],
)
async def set_default(
    payload: StorageConfigSetDefaultRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await StorageConfigService(db).set_default(payload)
    return success()
