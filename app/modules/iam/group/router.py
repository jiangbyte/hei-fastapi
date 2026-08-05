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
from app.modules.iam.group.schema import (
    GroupAdminPageQuery,
    GroupCreateRequest,
    GroupGrantResourceRequest,
    GroupGrantRoleRequest,
    GroupGrantUserRequest,
    GroupOwnResourceResponse,
    GroupOwnRoleResponse,
    GroupOwnUserResponse,
    GroupRoleAssignRequest,
    GroupUpdateRequest,
    SysGroupRoleRelSchema,
    SysGroupSchema,
)
from app.modules.iam.group.service import GroupService

router = APIRouter()


@router.post(
    "/sys/groups/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: GroupCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await GroupService(db).create(payload, session)
    return success()


@router.post(
    "/sys/groups/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: GroupUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await GroupService(db).update(payload, session)
    return success()


@router.post(
    "/sys/groups/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await GroupService(db).delete(payload, session)
    return success()


@router.get(
    "/sys/groups/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:detail")),
    ],
    response_model=ApiResponse[SysGroupSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[SysGroupSchema]:
    return success(await GroupService(db).detail(query, session))


@router.get(
    "/sys/groups/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:page")),
    ],
    response_model=ApiResponse[PageData[SysGroupSchema]],
)
async def page(
    query: Annotated[GroupAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[PageData[SysGroupSchema]]:
    return success(await GroupService(db).page_admin(query, session))


@router.post(
    "/group-roles",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:grantrole")),
    ],
    response_model=ApiResponse[SysGroupRoleRelSchema],
)
async def assign_group_role(
    payload: GroupRoleAssignRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[SysGroupRoleRelSchema]:
    return success(await GroupService(db).assign_group_role(payload, session))


@router.get(
    "/sys/groups/own-user",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:ownuser")),
    ],
    response_model=ApiResponse[GroupOwnUserResponse],
    summary="获取用户组成员授权",
)
async def own_user(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[GroupOwnUserResponse]:
    return success(await GroupService(db).own_user(query, session))


@router.post(
    "/sys/groups/grant-user",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:grantuser")),
    ],
    response_model=ApiResponse[None],
    summary="给用户组授权成员",
)
async def grant_user(
    payload: GroupGrantUserRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await GroupService(db).grant_user(payload, session)
    return success()


@router.get(
    "/sys/groups/own-role",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:ownrole")),
    ],
    response_model=ApiResponse[GroupOwnRoleResponse],
    summary="获取用户组角色授权",
)
async def own_role(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[GroupOwnRoleResponse]:
    return success(await GroupService(db).own_role(query, session))


@router.post(
    "/sys/groups/grant-role",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:grantrole")),
    ],
    response_model=ApiResponse[None],
    summary="给用户组授权角色",
)
async def grant_role(
    payload: GroupGrantRoleRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await GroupService(db).grant_role(payload, session)
    return success()


@router.get(
    "/sys/groups/own-resource",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:ownresource")),
    ],
    response_model=ApiResponse[GroupOwnResourceResponse],
    summary="获取用户组资源授权",
)
async def own_resource(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[GroupOwnResourceResponse]:
    return success(await GroupService(db).own_resource(query, session))


@router.post(
    "/sys/groups/grant-resource",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:group:grantresource")),
    ],
    response_model=ApiResponse[None],
    summary="给用户组授权资源",
)
async def grant_resource(
    payload: GroupGrantResourceRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await GroupService(db).grant_resource(payload, session)
    return success()
