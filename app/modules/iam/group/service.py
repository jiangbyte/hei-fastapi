""" Author: Charlie """

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.exceptions.business import AuthorizationError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.data_scope import build_data_scope_filter, resolve_data_scope_dept_ids
from app.core.security.session import SessionPayload
from app.modules.auth.session_service import AccountSessionService
from app.modules.iam.account.model import SysAccount
from app.modules.iam.account.query_service import AccountQueryService
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.enums import GrantSubjectType
from app.modules.iam.group.model import SysGroup
from app.modules.iam.group.repository import GroupRepository
from app.modules.iam.group.schema import (
    GroupAdminPageQuery,
    GroupCreateRequest,
    GroupGrantResourceRequest,
    GroupGrantRoleRequest,
    GroupGrantUserRequest,
    GroupOwnResourceResponse,
    GroupOwnRoleResponse,
    GroupOwnUserResponse,
    GroupResourceGrantInfo,
    GroupRoleAssignRequest,
    GroupUpdateRequest,
    SysGroupRoleRelSchema,
    SysGroupSchema,
)
from app.modules.iam.relation.model import SysIamRelation
from app.modules.iam.relation.repository import IamRelationRepository
from app.modules.iam.resource.service import ResourceService
from app.modules.iam.role.model import SysRole
from app.modules.iam.role.repository import RoleRepository
from app.modules.user.utils.profile import get_profiles_batch
from app.platform.db.transaction import transactional


class GroupService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GroupRepository(db)
        self.relation_repo = IamRelationRepository(db)

    async def create(
        self,
        payload: GroupCreateRequest,
        session: SessionPayload | None = None,
    ) -> None:
        if session is not None and payload.owner_dept_id:
            await self._ensure_depts_visible(session, "iam:group:create", [payload.owner_dept_id])
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(
        self,
        payload: GroupUpdateRequest,
        session: SessionPayload | None = None,
    ) -> None:
        if session is not None:
            await self._ensure_groups_visible(session, "iam:group:update", [payload.id])
            if payload.owner_dept_id:
                await self._ensure_depts_visible(
                    session,
                    "iam:group:update",
                    [payload.owner_dept_id],
                )
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest, session: SessionPayload | None = None) -> None:
        if session is not None:
            await self._ensure_groups_visible(session, "iam:group:delete", payload.ids)
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery, session: SessionPayload | None = None) -> SysGroupSchema:
        if session is not None:
            await self._ensure_groups_visible(session, "iam:group:detail", [query.id])
        schema = to_schema(SysGroupSchema, await self.repo.get_required(query.id))
        await self._resolve_creator_names([schema])
        return schema

    async def page_admin(
        self,
        query: GroupAdminPageQuery,
        session: SessionPayload | None = None,
    ) -> PageData[SysGroupSchema]:
        data_scope_filter = (
            await self._group_scope_filter(session, "iam:group:page")
            if session is not None
            else None
        )
        items, total = await self.repo.page_admin(query, data_scope_filter)
        schemas = to_schema_list(SysGroupSchema, items)
        await self._resolve_creator_names(schemas)
        return build_page(query, total, schemas)

    async def assign_group_role(
        self,
        payload: GroupRoleAssignRequest,
        session: SessionPayload | None = None,
    ) -> SysGroupRoleRelSchema:
        if session is not None:
            await self._ensure_groups_visible(session, "iam:group:grantrole", [payload.group_id])
            await self._ensure_roles_visible(session, "iam:group:grantrole", [payload.role_id])
        async with transactional(self.db):
            return to_schema(SysGroupRoleRelSchema, await self.repo.assign_group_to_role(payload))

    async def own_user(
        self,
        query: IdQuery,
        session: SessionPayload | None = None,
    ) -> GroupOwnUserResponse:
        account_filter = (
            await self._account_scope_filter(session, "iam:group:ownuser")
            if session is not None
            else None
        )
        if session is not None:
            await self._ensure_groups_visible(session, "iam:group:ownuser", [query.id])
        users = await self.repo.list_accounts(account_filter)
        group_users = await self.repo.list_group_accounts(query.id, account_filter)
        return GroupOwnUserResponse(
            id=query.id,
            users=await AccountQueryService(self.db).build_account_schemas(users),
            account_ids=[account.id for account in group_users],
        )

    async def grant_user(
        self,
        payload: GroupGrantUserRequest,
        session: SessionPayload | None = None,
    ) -> None:
        if session is not None:
            await self._ensure_groups_visible(session, "iam:group:grantuser", [payload.id])
            await self._ensure_accounts_visible(session, "iam:group:grantuser", payload.account_ids)
        async with transactional(self.db):
            old_account_ids = await self.repo.list_account_ids_by_group(payload.id)
            await self.repo.replace_group_accounts(payload)
        await self._refresh_accounts(sorted(set(old_account_ids + payload.account_ids)))

    async def own_role(
        self,
        query: IdQuery,
        session: SessionPayload | None = None,
    ) -> GroupOwnRoleResponse:
        role_filter = (
            await self._role_scope_filter(session, "iam:group:ownrole")
            if session is not None
            else None
        )
        if session is not None:
            await self._ensure_groups_visible(session, "iam:group:ownrole", [query.id])
        return GroupOwnRoleResponse(
            id=query.id,
            roles=await self.repo.list_all_roles(role_filter),
            role_ids=await self.repo.list_group_role_ids(query.id, role_filter),
        )

    async def grant_role(
        self,
        payload: GroupGrantRoleRequest,
        session: SessionPayload | None = None,
    ) -> None:
        if session is not None:
            await self._ensure_groups_visible(session, "iam:group:grantrole", [payload.id])
            await self._ensure_roles_visible(session, "iam:group:grantrole", payload.role_ids)
        async with transactional(self.db):
            account_ids = await self.repo.list_account_ids_by_group(payload.id)
            await self.repo.replace_group_roles(payload)
        await self._refresh_accounts(account_ids)

    async def own_resource(
        self,
        query: IdQuery,
        session: SessionPayload | None = None,
    ) -> GroupOwnResourceResponse:
        if session is not None:
            await self._ensure_groups_visible(session, "iam:group:ownresource", [query.id])
        return GroupOwnResourceResponse(
            id=query.id,
            modules=await ResourceService(self.db).list_grant_modules(),
            grant_info_list=[
                GroupResourceGrantInfo.model_validate(grant)
                for grant in await self.relation_repo.list_subject_resource_grants(
                    GrantSubjectType.GROUP,
                    query.id,
                )
            ],
        )

    async def grant_resource(
        self,
        payload: GroupGrantResourceRequest,
        session: SessionPayload | None = None,
    ) -> None:
        if session is not None:
            await self._ensure_groups_visible(session, "iam:group:grantresource", [payload.id])
        async with transactional(self.db):
            account_ids = await self.repo.list_account_ids_by_group(payload.id)
            await self.relation_repo.replace_subject_resource_grant_infos(
                GrantSubjectType.GROUP,
                payload.id,
                payload.grant_info_list,
            )
        await self._refresh_accounts(account_ids)

    async def _resolve_creator_names(self, items: list[SysGroupSchema]) -> None:
        """批量查询 created_by / updated_by 对应的昵称。"""
        account_ids: set[str] = set()
        for item in items:
            if item.created_by:
                account_ids.add(item.created_by)
            if item.updated_by:
                account_ids.add(item.updated_by)
        if not account_ids:
            return
        profiles = await get_profiles_batch(self.db, AccountType.ADMIN, list(account_ids))
        for item in items:
            if item.created_by and item.created_by in profiles:
                item.created_name = getattr(profiles[item.created_by], "nickname", None)
            if item.updated_by and item.updated_by in profiles:
                item.updated_name = getattr(profiles[item.updated_by], "nickname", None)

    async def _refresh_accounts(self, account_ids: list[str]) -> None:
        await AccountSessionService(self.db).refresh_accounts_sessions(sorted(set(account_ids)))

    async def _group_scope_filter(self, session: SessionPayload, permission_key: str):
        return await build_data_scope_filter(
            self.db,
            session,
            permission_key,
            owner_column=SysGroup.created_by,
            dept_column=SysGroup.owner_dept_id,
        )

    async def _role_scope_filter(self, session: SessionPayload, permission_key: str):
        return await build_data_scope_filter(
            self.db,
            session,
            permission_key,
            owner_column=SysRole.created_by,
            dept_column=SysRole.owner_dept_id,
        )

    async def _account_scope_filter(self, session: SessionPayload, permission_key: str):
        return await build_data_scope_filter(
            self.db,
            session,
            permission_key,
            owner_column=SysAccount.id,
            dept_column=SysIamRelation.target_id,
        )

    async def _ensure_groups_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        group_ids: list[str],
    ) -> None:
        unique_ids = list(dict.fromkeys(group_ids))
        if not unique_ids:
            return
        data_scope_filter = await self._group_scope_filter(session, permission_key)
        if await self.repo.count_groups_in_scope(unique_ids, data_scope_filter) != len(unique_ids):
            raise AuthorizationError("Group is outside current data scope")

    async def _ensure_roles_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        role_ids: list[str],
    ) -> None:
        unique_ids = list(dict.fromkeys(role_ids))
        if not unique_ids:
            return
        data_scope_filter = await self._role_scope_filter(session, permission_key)
        count = await RoleRepository(self.db).count_roles_in_scope(unique_ids, data_scope_filter)
        if count != len(unique_ids):
            raise AuthorizationError("Role is outside current data scope")

    async def _ensure_accounts_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        account_ids: list[str],
    ) -> None:
        unique_ids = list(dict.fromkeys(account_ids))
        if not unique_ids:
            return
        data_scope_filter = await self._account_scope_filter(session, permission_key)
        count = await AccountRepository(self.db).count_accounts_in_scope(
            unique_ids,
            data_scope_filter,
        )
        if count != len(unique_ids):
            raise AuthorizationError("Account is outside current data scope")

    async def _ensure_depts_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        dept_ids: list[str],
    ) -> None:
        unique_ids = list(dict.fromkeys(dept_ids))
        if not unique_ids:
            return
        visible_dept_ids = await resolve_data_scope_dept_ids(self.db, session, permission_key)
        if visible_dept_ids is None:
            return
        allowed_ids = set(visible_dept_ids)
        if any(dept_id not in allowed_ids for dept_id in unique_ids):
            raise AuthorizationError("Dept is outside current data scope")
