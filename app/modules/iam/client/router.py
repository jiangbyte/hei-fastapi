""" Author: Charlie

客户端模块与客户端资源管理 HTTP 路由。
"""

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
from app.modules.iam.client.schema import (
    ClientModuleAdminPageQuery,
    ClientModuleCreateRequest,
    ClientModuleSelectorOption,
    ClientModuleSelectorQuery,
    ClientModuleUpdateRequest,
    ClientResourceAdminPageQuery,
    ClientResourceCreateRequest,
    ClientResourcePermissionBindRequest,
    ClientResourceTreeNode,
    ClientResourceTreeQuery,
    ClientResourceUpdateRequest,
    SysClientModuleSchema,
    SysClientResourcePermissionRelSchema,
    SysClientResourceSchema,
)
from app.modules.iam.client.service import ClientModuleService, ClientResourceService

router = APIRouter()


@router.post(
    "/v1/admin/sys/client-modules/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientmodule:create")),
    ],
    response_model=ApiResponse[None],
)
async def create_client_module(
    payload: ClientModuleCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ClientModuleService(db).create(payload)
    return success()


@router.post(
    "/v1/admin/sys/client-modules/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientmodule:update")),
    ],
    response_model=ApiResponse[None],
)
async def update_client_module(
    payload: ClientModuleUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ClientModuleService(db).update(payload)
    return success()


@router.post(
    "/v1/admin/sys/client-modules/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientmodule:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete_client_module(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ClientModuleService(db).delete(payload)
    return success()


@router.get(
    "/v1/admin/sys/client-modules/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientmodule:detail")),
    ],
    response_model=ApiResponse[SysClientModuleSchema],
)
async def client_module_detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SysClientModuleSchema]:
    return success(await ClientModuleService(db).detail(query))


@router.get(
    "/v1/admin/sys/client-modules/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientmodule:page")),
    ],
    response_model=ApiResponse[PageData[SysClientModuleSchema]],
)
async def client_module_page(
    query: Annotated[ClientModuleAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[SysClientModuleSchema]]:
    return success(await ClientModuleService(db).page_admin(query))


@router.get(
    "/v1/admin/sys/client-modules/selector",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientmodule:page")),
    ],
    response_model=ApiResponse[list[SysClientModuleSchema]],
)
async def client_module_selector(
    query: Annotated[ClientModuleSelectorQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SysClientModuleSchema]]:
    return success(await ClientModuleService(db).selector(query))


@router.post(
    "/v1/admin/sys/client-resources/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientresource:create")),
    ],
    response_model=ApiResponse[None],
)
async def create_client_resource(
    payload: ClientResourceCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ClientResourceService(db).create(payload)
    return success()


@router.post(
    "/v1/admin/sys/client-resources/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientresource:update")),
    ],
    response_model=ApiResponse[None],
)
async def update_client_resource(
    payload: ClientResourceUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ClientResourceService(db).update(payload)
    return success()


@router.post(
    "/v1/admin/sys/client-resources/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientresource:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete_client_resource(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ClientResourceService(db).delete(payload)
    return success()


@router.get(
    "/v1/admin/sys/client-resources/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientresource:detail")),
    ],
    response_model=ApiResponse[SysClientResourceSchema],
)
async def client_resource_detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SysClientResourceSchema]:
    return success(await ClientResourceService(db).detail(query))


@router.get(
    "/v1/admin/sys/client-resources/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientresource:page")),
    ],
    response_model=ApiResponse[PageData[SysClientResourceSchema]],
)
async def client_resource_page(
    query: Annotated[ClientResourceAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[SysClientResourceSchema]]:
    return success(await ClientResourceService(db).page_admin(query))


@router.get(
    "/v1/admin/sys/client-resources/tree",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientresource:list")),
    ],
    response_model=ApiResponse[list[ClientResourceTreeNode]],
)
async def client_resource_tree(
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[ClientResourceTreeQuery, Depends()],
) -> ApiResponse[list[ClientResourceTreeNode]]:
    return success(await ClientResourceService(db).list_tree(session, query))


@router.post(
    "/v1/admin/client-resource-permissions",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:clientresource:grant")),
    ],
    response_model=ApiResponse[SysClientResourcePermissionRelSchema],
)
async def bind_client_resource_permission(
    payload: ClientResourcePermissionBindRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[SysClientResourcePermissionRelSchema]:
    return success(await ClientResourceService(db).bind_permission(payload, session))
