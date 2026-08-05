from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType, StorageProvider
from app.core.config.settings import settings
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import IdQuery, IdsRequest
from app.deps.auth import require_account_type
from app.deps.db import get_db_session
from app.modules.sys.file.schema import (
    FileUploadRequest,
    FileUrlRequest,
    FileUrlResponse,
    SysFileSchema,
)
from app.modules.sys.file.service import FileService

router = APIRouter()
portal_dependencies = [Depends(require_account_type(AccountType.PORTAL))]


@router.post(
    "/sys/file/upload",
    dependencies=portal_dependencies,
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


@router.get(
    "/sys/file/detail",
    dependencies=portal_dependencies,
    response_model=ApiResponse[SysFileSchema],
)
async def detail(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[IdQuery, Depends()],
) -> ApiResponse[SysFileSchema]:
    return success(await FileService(db).detail(query))


@router.post(
    "/sys/file/list_by_ids",
    dependencies=portal_dependencies,
    response_model=ApiResponse[list[SysFileSchema]],
)
async def list_by_ids(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SysFileSchema]]:
    return success(await FileService(db).list_by_ids(payload))


@router.get(
    "/sys/file/download",
    dependencies=portal_dependencies,
    response_class=Response,
)
async def download(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[IdQuery, Depends()],
) -> Response:
    return await FileService(db).download_by_id(query)


@router.post(
    "/sys/file/url",
    dependencies=portal_dependencies,
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
    dependencies=portal_dependencies,
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
