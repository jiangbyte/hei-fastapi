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
from app.modules.iam.account.schema import (
    AccountCreateRequest,
    AccountAdminPageQuery,
    AccountDeptAssignRequest,
    AccountGrantDeptRequest,
    AccountGrantGroupRequest,
    AccountGrantResourceRequest,
    AccountGrantRoleRequest,
    AccountGroupAssignRequest,
    AccountOwnDeptResponse,
    AccountOwnGroupResponse,
    AccountOwnResourceResponse,
    AccountOwnRoleResponse,
    AccountRoleAssignRequest,
    AccountUpdateRequest,
    SysAccountDeptRelSchema,
    SysAccountGroupRelSchema,
    SysAccountRoleRelSchema,
    SysAccountSchema,
)
from app.modules.iam.account.service import AccountService

router = APIRouter()


@router.post(
    "/sys/accounts/create",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:create")),
    ],
    response_model=ApiResponse[None],
)
async def create(
    payload: AccountCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await AccountService(db).create(payload)
    return success()


@router.post(
    "/sys/accounts/update",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:update")),
    ],
    response_model=ApiResponse[None],
)
async def update(
    payload: AccountUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await AccountService(db).update(payload, session)
    return success()


@router.post(
    "/sys/accounts/delete",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:delete")),
    ],
    response_model=ApiResponse[None],
)
async def delete(
    payload: IdsRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await AccountService(db).delete(payload, session)
    return success()


@router.get(
    "/sys/accounts/detail",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:detail")),
    ],
    response_model=ApiResponse[SysAccountSchema],
)
async def detail(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[SysAccountSchema]:
    return success(await AccountService(db).detail(query, session))


@router.get(
    "/sys/accounts/page",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:page")),
    ],
    response_model=ApiResponse[PageData[SysAccountSchema]],
)
async def page(
    query: Annotated[AccountAdminPageQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[PageData[SysAccountSchema]]:
    return success(await AccountService(db).page_admin(query, session))


@router.post(
    "/account-roles",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:grantrole")),
    ],
    response_model=ApiResponse[SysAccountRoleRelSchema],
)
async def assign_account_role(
    payload: AccountRoleAssignRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[SysAccountRoleRelSchema]:
    return success(await AccountService(db).assign_account_role(payload, session))


@router.post(
    "/account-groups",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:grantgroup")),
    ],
    response_model=ApiResponse[SysAccountGroupRelSchema],
)
async def assign_account_group(
    payload: AccountGroupAssignRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[SysAccountGroupRelSchema]:
    return success(await AccountService(db).assign_account_group(payload, session))


@router.post(
    "/account-depts",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:grantdept")),
    ],
    response_model=ApiResponse[SysAccountDeptRelSchema],
)
async def assign_account_dept(
    payload: AccountDeptAssignRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[SysAccountDeptRelSchema]:
    return success(await AccountService(db).assign_account_dept(payload, session))


@router.get(
    "/sys/accounts/own-resource",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:ownresource")),
    ],
    response_model=ApiResponse[AccountOwnResourceResponse],
    summary="获取用户资源授权",
)
async def own_resource(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[AccountOwnResourceResponse]:
    return success(await AccountService(db).own_resource(query, session))


@router.post(
    "/sys/accounts/grant-resource",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:grantresource")),
    ],
    response_model=ApiResponse[None],
    summary="给用户授权资源",
)
async def grant_resource(
    payload: AccountGrantResourceRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await AccountService(db).grant_resource(payload, session)
    return success()


@router.get(
    "/sys/accounts/own-role",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:ownrole")),
    ],
    response_model=ApiResponse[AccountOwnRoleResponse],
    summary="获取用户角色授权",
)
async def own_role(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[AccountOwnRoleResponse]:
    return success(await AccountService(db).own_role(query, session))


@router.post(
    "/sys/accounts/grant-role",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:grantrole")),
    ],
    response_model=ApiResponse[None],
    summary="给用户授权角色",
)
async def grant_role(
    payload: AccountGrantRoleRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await AccountService(db).grant_role(payload, session)
    return success()


@router.get(
    "/sys/accounts/own-group",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:owngroup")),
    ],
    response_model=ApiResponse[AccountOwnGroupResponse],
    summary="获取用户组授权",
)
async def own_group(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[AccountOwnGroupResponse]:
    return success(await AccountService(db).own_group(query, session))


@router.post(
    "/sys/accounts/grant-group",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:grantgroup")),
    ],
    response_model=ApiResponse[None],
    summary="给用户授权用户组",
)
async def grant_group(
    payload: AccountGrantGroupRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await AccountService(db).grant_group(payload, session)
    return success()


@router.get(
    "/sys/accounts/own-dept",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:owndept")),
    ],
    response_model=ApiResponse[AccountOwnDeptResponse],
    summary="获取用户部门授权",
)
async def own_dept(
    query: Annotated[IdQuery, Depends()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[AccountOwnDeptResponse]:
    return success(await AccountService(db).own_dept(query, session))


@router.post(
    "/sys/accounts/grant-dept",
    dependencies=[
        Depends(require_account_type(AccountType.ADMIN)),
        Depends(require_permission("iam:account:grantdept")),
    ],
    response_model=ApiResponse[None],
    summary="给用户授权部门",
)
async def grant_dept(
    payload: AccountGrantDeptRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session: Annotated[SessionPayload, Depends(get_current_session)],
) -> ApiResponse[None]:
    await AccountService(db).grant_dept(payload, session)
    return success()
