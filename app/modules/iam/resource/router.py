from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import Current, PageData, PageQuery, Size
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import Id, IdQuery, IdsRequest
from app.core.security.session import SessionPayload
from app.deps.auth import get_current_session, require_account_type, require_permission
from app.deps.db import get_db_session
from app.modules.iam.enums import ResourceModuleClient
from app.modules.iam.resource.schema import (
    ResourceAdminPageQuery,
    ResourceButtonCreateRequest,
    ResourceButtonPageQuery,
    ResourceButtonSchema,
    ResourceButtonUpdateRequest,
    ResourceCreateRequest,
    ResourceModuleAdminPageQuery,
    ResourceModuleCreateRequest,
    ResourceModuleSelectorOption,
    ResourceModuleSelectorQuery,
    ResourceModuleUpdateRequest,
    ResourcePermissionBindRequest,
    ResourceTreeNode,
    ResourceTreeQuery,
    ResourceUpdateRequest,
    SysResourceModuleSchema,
    SysResourcePermissionRelSchema,
    SysResourceSchema,
)
from app.modules.iam.resource.service import ResourceModuleService, ResourceService
from app.modules.iam.schema import PermissionRegistryItem

router = APIRouter()


@router.post(
    "/sys/resources/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: ResourceCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ResourceService(db).create(payload)
    return success()


@router.post(
    "/sys/resources/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: ResourceUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ResourceService(db).update(payload)
    return success()


@router.post(
    "/sys/resources/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ResourceService(db).delete(payload)
    return success()


@router.get(
    "/sys/resources/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:detail")),
    ],
    response_model=ApiResponse[SysResourceSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SysResourceSchema]:
    return success(await ResourceService(db).detail(query))


@router.get(
    "/sys/resources/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:page")),
    ],
    response_model=ApiResponse[PageData[SysResourceSchema]],
)
async def page(
    query: Annotated[ResourceAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[SysResourceSchema]]:
    return success(await ResourceService(db).page_admin(query))


@router.get(
    "/sys/resources/current",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
    ],
    response_model=ApiResponse[list[SysResourceSchema]],
)
async def current_resources(
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SysResourceSchema]]:
    return success(
        await ResourceService(db).list_current_resources(
            session,
            module_client=ResourceModuleClient.ADMIN,
        )
    )


@router.get(
    "/sys/resources/tree",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:list")),
    ],
    response_model=ApiResponse[list[ResourceTreeNode]],
)
async def list_resource_tree(
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[ResourceTreeQuery, Depends()],
) -> ApiResponse[list[ResourceTreeNode]]:
    return success(await ResourceService(db).list_resource_tree(session, query))


@router.post(
    "/resource-permissions",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:grant")),
    ],
    response_model=ApiResponse[SysResourcePermissionRelSchema],
)
async def bind_resource_permission(
    payload: ResourcePermissionBindRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[SysResourcePermissionRelSchema]:
    return success(await ResourceService(db).bind_resource_permission(payload, session))


@router.get(
    "/permission-registry",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:grant")),
    ],
    response_model=ApiResponse[list[PermissionRegistryItem]],
)
async def permission_registry(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[PermissionRegistryItem]]:
    return success(await ResourceService(db).list_permission_registry_items())


@router.post(
    "/sys/resource-buttons/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:create")),
        Depends(require_permission("iam:resource:grant")),
    ],
    response_model=ApiResponse[ResourceButtonSchema],
)
async def create_button(
    payload: ResourceButtonCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[ResourceButtonSchema]:
    return success(await ResourceService(db).create_button(payload, session))


@router.post(
    "/sys/resource-buttons/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:update")),
        Depends(require_permission("iam:resource:grant")),
    ],
    response_model=ApiResponse[ResourceButtonSchema],
)
async def update_button(
    payload: ResourceButtonUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[ResourceButtonSchema]:
    return success(await ResourceService(db).update_button(payload, session))


@router.post(
    "/sys/resource-buttons/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete_button(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ResourceService(db).delete_button(payload)
    return success()


@router.get(
    "/sys/resource-buttons/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resource:list")),
    ],
    response_model=ApiResponse[PageData[ResourceButtonSchema]],
)
async def button_page(
    query: Annotated[ResourceButtonPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[ResourceButtonSchema]]:
    return success(await ResourceService(db).page_buttons(query))


@router.post(
    "/sys/resource-modules/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resourcemodule:create")),
    ],
    response_model=ApiResponse[None],
)
async def create_resource_module(
    payload: ResourceModuleCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ResourceModuleService(db).create(payload)
    return success()


@router.post(
    "/sys/resource-modules/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resourcemodule:update")),
    ],
    response_model=ApiResponse[None],
)
async def update_resource_module(
    payload: ResourceModuleUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ResourceModuleService(db).update(payload)
    return success()


@router.post(
    "/sys/resource-modules/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resourcemodule:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete_resource_module(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await ResourceModuleService(db).delete(payload)
    return success()


@router.get(
    "/sys/resource-modules/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resourcemodule:detail")),
    ],
    response_model=ApiResponse[SysResourceModuleSchema],
)
async def resource_module_detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SysResourceModuleSchema]:
    return success(await ResourceModuleService(db).detail(query))


@router.get(
    "/sys/resource-modules/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:resourcemodule:page")),
    ],
    response_model=ApiResponse[PageData[SysResourceModuleSchema]],
)
async def resource_module_page(
    query: Annotated[ResourceModuleAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PageData[SysResourceModuleSchema]]:
    return success(await ResourceModuleService(db).page_admin(query))


@router.get(
    "/sys/resource-modules/selector",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
    ],
    response_model=ApiResponse[list[ResourceModuleSelectorOption]],
)
async def resource_module_selector(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    query: Annotated[ResourceModuleSelectorQuery, Depends()],
) -> ApiResponse[list[ResourceModuleSelectorOption]]:
    return success(await ResourceModuleService(db).selector(query))
