from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import Current, PageData, PageQuery, Size
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import Id, IdQuery, IdsRequest
from app.deps.auth import require_account_type, require_permission
from app.deps.db import get_db_session
from app.modules.sys.codegen.schema import (
    CodegenFieldsQuery,
    CodegenFieldsUpdateBatchRequest,
    CodegenParentResourceOption,
    CodegenParentResourcesQuery,
    CodegenPlanCreateRequest,
    CodegenPlanPageQuery,
    CodegenPlanUpdateRequest,
    CodegenPreviewSchema,
    CodegenTableColumnsQuery,
    CodegenType,
    DatabaseColumnSchema,
    DatabaseTableSchema,
    SysCodegenFieldSchema,
    SysCodegenPlanSchema,
)
from app.modules.sys.codegen.service import CodegenService

router = APIRouter()


@router.post(
    "/sys/codegen/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: CodegenPlanCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await CodegenService(db).create(payload)
    return success()


@router.post(
    "/sys/codegen/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: CodegenPlanUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await CodegenService(db).update(payload)
    return success()


@router.post(
    "/sys/codegen/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await CodegenService(db).delete(payload)
    return success()


@router.get(
    "/sys/codegen/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:detail")),
    ],
    response_model=ApiResponse[SysCodegenPlanSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SysCodegenPlanSchema]:
    return success(await CodegenService(db).detail(query))


@router.get(
    "/sys/codegen/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:page")),
    ],
    response_model=ApiResponse[PageData[SysCodegenPlanSchema]],
)
async def page(
    query: Annotated[CodegenPlanPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[SysCodegenPlanSchema]]:
    return success(await CodegenService(db).page_admin(query))


@router.get(
    "/sys/codegen/tables",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:tables")),
    ],
    response_model=ApiResponse[list[DatabaseTableSchema]],
)
async def tables(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[DatabaseTableSchema]]:
    return success(await CodegenService(db).tables())


@router.get(
    "/sys/codegen/table-columns",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:tables")),
    ],
    response_model=ApiResponse[list[DatabaseColumnSchema]],
)
async def table_columns(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[CodegenTableColumnsQuery, Depends()],
) -> ApiResponse[list[DatabaseColumnSchema]]:
    return success(await CodegenService(db).table_columns(query))


@router.get(
    "/sys/codegen/fields",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:detail")),
    ],
    response_model=ApiResponse[list[SysCodegenFieldSchema]],
)
async def fields(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[CodegenFieldsQuery, Depends()],
) -> ApiResponse[list[SysCodegenFieldSchema]]:
    return success(await CodegenService(db).fields(query))


@router.post(
    "/sys/codegen/fields/update-batch",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:update")),
    ],
    response_model=ApiResponse[None],
)
async def update_fields_batch(
    payload: CodegenFieldsUpdateBatchRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await CodegenService(db).update_fields_batch(payload)
    return success()


@router.get(
    "/sys/codegen/parent-resources",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:detail")),
    ],
    response_model=ApiResponse[list[CodegenParentResourceOption]],
)
async def parent_resources(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[CodegenParentResourcesQuery, Depends()],
) -> ApiResponse[list[CodegenParentResourceOption]]:
    return success(await CodegenService(db).parent_resources(query))


@router.get(
    "/sys/codegen/preview",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:preview")),
    ],
    response_model=ApiResponse[CodegenPreviewSchema],
)
async def preview(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CodegenPreviewSchema]:
    return success(await CodegenService(db).preview(query))


@router.get(
    "/sys/codegen/download",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("sys:codegen:download")),
    ],
)
async def download(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    content, filename = await CodegenService(db).download(query)
    return Response(
        content=content,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
