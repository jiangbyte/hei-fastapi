"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:52
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.schema import ApiResponse, success
from app.core.schema.base import IdQuery
from app.core.security.session import SessionPayload
from app.deps.auth import get_current_session, require_account_type
from app.deps.db import get_db_session
from app.modules.message.group.schema import (
    GroupCreateRequest,
    GroupDetailRequest,
    GroupJoinRequestCreate,
    GroupJoinRequestHandle,
    GroupJoinRequestSchema,
    GroupMemberAddRequest,
    GroupMemberRemoveRequest,
    GroupMemberSchema,
    GroupSearchQuery,
    GroupUpdateRequest,
    MsgGroupSchema,
    SetMemberRoleRequest,
)
from app.modules.message.group.service import (
    MsgGroupService,
)

admin_router = APIRouter()
portal_router = APIRouter()


# ==================== 当前用户路由 ====================


def register_current_user_routes():
    """为当前已登录用户注册群组路由。"""

    @admin_router.post(
        "/v1/admin/message/groups/create",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[MsgGroupSchema],
    )
    @portal_router.post(
        "/v1/portal/message/groups/create",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[MsgGroupSchema],
    )
    async def create_group(
        payload: GroupCreateRequest,
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[MsgGroupSchema]:
        return success(await MsgGroupService(db).create_group(payload, session))

    @admin_router.post(
        "/v1/admin/message/groups/update",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[MsgGroupSchema],
    )
    @portal_router.post(
        "/v1/portal/message/groups/update",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[MsgGroupSchema],
    )
    async def update_group(
        payload: GroupUpdateRequest,
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[MsgGroupSchema]:
        return success(await MsgGroupService(db).update_group(payload, session))

    @admin_router.post(
        "/v1/admin/message/groups/dissolve",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[None],
    )
    @portal_router.post(
        "/v1/portal/message/groups/dissolve",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[None],
    )
    async def dissolve(
        payload: GroupDetailRequest,
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[None]:
        await MsgGroupService(db).dissolve(payload, session)
        return success()

    @admin_router.post(
        "/v1/admin/message/groups/leave",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[None],
    )
    @portal_router.post(
        "/v1/portal/message/groups/leave",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[None],
    )
    async def leave(
        payload: GroupDetailRequest,
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[None]:
        await MsgGroupService(db).leave(payload, session)
        return success()

    @admin_router.get(
        "/v1/admin/message/groups/my-list",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[list[MsgGroupSchema]],
    )
    @portal_router.get(
        "/v1/portal/message/groups/my-list",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[list[MsgGroupSchema]],
    )
    async def my_list(
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[list[MsgGroupSchema]]:
        return success(await MsgGroupService(db).my_list(session))

    @admin_router.get(
        "/v1/admin/message/groups/search",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[list[MsgGroupSchema]],
    )
    @portal_router.get(
        "/v1/portal/message/groups/search",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[list[MsgGroupSchema]],
    )
    async def search_groups(
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
        query: Annotated[GroupSearchQuery, Depends()],
    ) -> ApiResponse[list[MsgGroupSchema]]:
        return success(await MsgGroupService(db).search_groups(query, session))

    @admin_router.get(
        "/v1/admin/message/groups/detail",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[MsgGroupSchema],
    )
    @portal_router.get(
        "/v1/portal/message/groups/detail",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[MsgGroupSchema],
    )
    async def group_detail(
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
        query: Annotated[IdQuery, Depends()],
    ) -> ApiResponse[MsgGroupSchema]:
        return success(await MsgGroupService(db).group_detail(query, session))

    # ==================== 成员 ====================

    @admin_router.post(
        "/v1/admin/message/groups/members/add",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[None],
    )
    @portal_router.post(
        "/v1/portal/message/groups/members/add",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[None],
    )
    async def add_members(
        payload: GroupMemberAddRequest,
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[None]:
        await MsgGroupService(db).add_members(payload, session)
        return success()

    @admin_router.post(
        "/v1/admin/message/groups/members/remove",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[None],
    )
    @portal_router.post(
        "/v1/portal/message/groups/members/remove",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[None],
    )
    async def remove_members(
        payload: GroupMemberRemoveRequest,
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[None]:
        await MsgGroupService(db).remove_members(payload, session)
        return success()

    @admin_router.post(
        "/v1/admin/message/groups/members/set-role",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[None],
    )
    @portal_router.post(
        "/v1/portal/message/groups/members/set-role",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[None],
    )
    async def set_member_role(
        payload: SetMemberRoleRequest,
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[None]:
        await MsgGroupService(db).set_member_role(payload, session)
        return success()

    @admin_router.get(
        "/v1/admin/message/groups/members/list",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[list[GroupMemberSchema]],
    )
    @portal_router.get(
        "/v1/portal/message/groups/members/list",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[list[GroupMemberSchema]],
    )
    async def list_members(
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
        query: Annotated[IdQuery, Depends()],
    ) -> ApiResponse[list[GroupMemberSchema]]:
        return success(await MsgGroupService(db).list_members(query, session))

    # ==================== 入群申请 ====================

    @admin_router.post(
        "/v1/admin/message/groups/join-requests/apply",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[None],
    )
    @portal_router.post(
        "/v1/portal/message/groups/join-requests/apply",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[None],
    )
    async def apply_join(
        payload: GroupJoinRequestCreate,
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[None]:
        await MsgGroupService(db).apply_join(payload, session)
        return success()

    @admin_router.post(
        "/v1/admin/message/groups/join-requests/handle",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[None],
    )
    @portal_router.post(
        "/v1/portal/message/groups/join-requests/handle",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[None],
    )
    async def handle_join_request(
        payload: GroupJoinRequestHandle,
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[None]:
        await MsgGroupService(db).handle_join_request(payload, session)
        return success()

    @admin_router.get(
        "/v1/admin/message/groups/join-requests/my",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[list[GroupJoinRequestSchema]],
    )
    @portal_router.get(
        "/v1/portal/message/groups/join-requests/my",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[list[GroupJoinRequestSchema]],
    )
    async def my_join_requests(
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[list[GroupJoinRequestSchema]]:
        return success(await MsgGroupService(db).my_join_requests(session))

    @admin_router.get(
        "/v1/admin/message/groups/join-requests/pending",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[list[GroupJoinRequestSchema]],
    )
    @portal_router.get(
        "/v1/portal/message/groups/join-requests/pending",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[list[GroupJoinRequestSchema]],
    )
    async def pending_requests(
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[list[GroupJoinRequestSchema]]:
        return success(await MsgGroupService(db).pending_requests(session))

    @admin_router.get(
        "/v1/admin/message/groups/join-requests/pending-count",
        dependencies=[Depends(require_account_type(AccountType.ADMIN))],
        response_model=ApiResponse[int],
    )
    @portal_router.get(
        "/v1/portal/message/groups/join-requests/pending-count",
        dependencies=[Depends(require_account_type(AccountType.ADMIN, AccountType.PORTAL))],
        response_model=ApiResponse[int],
    )
    async def pending_count(
        db: Annotated[AsyncSession, Depends(get_db_session)],
        session: Annotated[SessionPayload, Depends(get_current_session)],
    ) -> ApiResponse[int]:
        return success(await MsgGroupService(db).pending_count(session))


register_current_user_routes()
