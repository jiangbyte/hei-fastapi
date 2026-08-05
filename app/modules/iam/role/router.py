from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import Current, PageData, PageQuery, Size
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import Id, IdQuery, IdsRequest
from app.core.security.session import SessionPayload
from app.deps.auth import get_current_session, require_permission, require_account_type
from app.deps.db import get_db_session
from app.modules.iam.role.schema import (
    RoleAdminPageQuery,
    RoleGrantResourceRequest,
    RoleGrantUserRequest,
    RoleOwnResourceResponse,
    RoleOwnUserResponse,
    RoleCreateRequest,
    RoleUpdateRequest,
    SysRoleSchema,
)
from app.modules.iam.role.service import RoleService

router = APIRouter()


@router.post(
    "/sys/roles/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:role:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: RoleCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await RoleService(db).create(payload, session)
    return success()


@router.post(
    "/sys/roles/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:role:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: RoleUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await RoleService(db).update(payload, session)
    return success()


@router.post(
    "/sys/roles/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:role:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await RoleService(db).delete(payload, session)
    return success()


@router.get(
    "/sys/roles/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:role:detail")),
    ],
    response_model=ApiResponse[SysRoleSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[SysRoleSchema]:
    return success(await RoleService(db).detail(query, session))


@router.get(
    "/sys/roles/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:role:page")),
    ],
    response_model=ApiResponse[PageData[SysRoleSchema]],
)
async def page(
    query: Annotated[RoleAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[PageData[SysRoleSchema]]:
    return success(await RoleService(db).page_admin(query, session))


@router.get(
    "/sys/roles/own-resource",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:role:ownresource")),
    ],
    response_model=ApiResponse[RoleOwnResourceResponse],
    summary="获取角色拥有资源",
)
async def own_resource(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[RoleOwnResourceResponse]:
    return success(await RoleService(db).own_resource(query, session))


@router.post(
    "/sys/roles/grant-resource",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:role:grantresource")),
    ],
    response_model=ApiResponse[None],
    summary="给角色授权资源",
)
async def grant_resource(
    payload: RoleGrantResourceRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await RoleService(db).grant_resource(payload, session)
    return success()


@router.get(
    "/sys/roles/own-user",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:role:ownuser")),
    ],
    response_model=ApiResponse[RoleOwnUserResponse],
    summary="获取角色拥有用户",
)
async def own_user(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[RoleOwnUserResponse]:
    return success(await RoleService(db).own_user(query, session))


@router.post(
    "/sys/roles/grant-user",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:role:grantuser")),
    ],
    response_model=ApiResponse[None],
    summary="给角色授权用户",
)
async def grant_user(
    payload: RoleGrantUserRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await RoleService(db).grant_user(payload, session)
    return success()
