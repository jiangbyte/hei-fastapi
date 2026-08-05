from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType, StorageProvider
from app.core.config.settings import settings
from app.core.response.pagination import Current, PageData, PageQuery, Size
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import Id, IdQuery, IdsRequest
from app.core.security.session import SessionPayload
from app.deps.auth import get_current_session, require_account_type, require_permission
from app.deps.db import get_db_session
from app.modules.sys.file.schema import (
    FileAdminPageQuery,
    FileUpdateRequest,
    FileUploadRequest,
    FileUrlRequest,
    FileUrlResponse,
    SysFileSchema,
)
from app.modules.sys.file.service import FileService

router = APIRouter()


@router.post(
    "/sys/file/upload",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:file:upload")),
    ],
    response_model=ApiResponse[SysFileSchema],
)
async def upload(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    storage_config_id: Annotated[str | None, Form()] = None,
    storage_provider: Annotated[StorageProvider | None, Form()] = None,
) -> ApiResponse[SysFileSchema]:
    content = await file.read(settings.storage.upload_max_bytes + 1)
    return success(
        await FileService(db).upload(
            FileUploadRequest(
                filename=file.filename or "file.bin",
                content=content,
                content_type=file.content_type or "application/octet-stream",
                storage_config_id=storage_config_id,
                storage_provider=storage_provider,
            )
        )
    )


@router.post(
    "/sys/file/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:file:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await FileService(db).delete(payload)
    return success()


@router.post(
    "/sys/file/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:file:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: FileUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await FileService(db).update(payload)
    return success()


@router.get(
    "/sys/file/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:file:detail")),
    ],
    response_model=ApiResponse[SysFileSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SysFileSchema]:
    return success(await FileService(db).detail(query))


@router.post(
    "/sys/file/list_by_ids",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:file:detail")),
    ],
    response_model=ApiResponse[list[SysFileSchema]],
)
async def list_by_ids(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SysFileSchema]]:
    return success(await FileService(db).list_by_ids(payload))


@router.get(
    "/sys/file/download",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:file:url")),
    ],
    response_class=Response,
)
async def download(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    return await FileService(db).download_by_id(query)


@router.post(
    "/sys/file/url",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:file:url")),
    ],
    response_model=ApiResponse[FileUrlResponse],
)
async def url(
    payload: FileUrlRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[FileUrlResponse]:
    return success(
        FileUrlResponse(
            object_name=payload.object_name,
            url=await FileService(db).get_url(payload),
        )
    )


@router.post(
    "/sys/file/presigned_url",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:file:presignedurl")),
    ],
    response_model=ApiResponse[FileUrlResponse],
)
async def presigned_url(
    payload: FileUrlRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[FileUrlResponse]:
    return success(
        FileUrlResponse(
            object_name=payload.object_name,
            url=await FileService(db).get_presigned_url(payload),
        )
    )


@router.get(
    "/sys/file/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:file:page")),
    ],
    response_model=ApiResponse[PageData[SysFileSchema]],
)
async def page(
    query: Annotated[FileAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[PageData[SysFileSchema]]:
    return success(await FileService(db).page(query, session))
