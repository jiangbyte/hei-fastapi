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
from app.modules.iam.relation.model import SysIamRelation
from app.modules.iam.resource.service import ResourceService
from app.modules.iam.role.model import SysRole
from app.modules.iam.role.repository import RoleRepository
from app.modules.iam.role.schema import (
    RoleAdminPageQuery,
    RoleCreateRequest,
    RoleGrantResourceRequest,
    RoleGrantUserRequest,
    RoleOwnResourceResponse,
    RoleOwnUserResponse,
    RoleUpdateRequest,
    SysRoleSchema,
)
from app.modules.user.utils.profile import get_profiles_batch
from app.platform.db.transaction import transactional


class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RoleRepository(db)

    async def create(
        self,
        payload: RoleCreateRequest,
        session: SessionPayload | None = None,
    ) -> None:
        if session is not None and payload.owner_dept_id:
            await self._ensure_depts_visible(session, "iam:role:create", [payload.owner_dept_id])
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(
        self,
        payload: RoleUpdateRequest,
        session: SessionPayload | None = None,
    ) -> None:
        if session is not None:
            await self._ensure_roles_visible(session, "iam:role:update", [payload.id])
            if payload.owner_dept_id:
                await self._ensure_depts_visible(
                    session,
                    "iam:role:update",
                    [payload.owner_dept_id],
                )
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest, session: SessionPayload | None = None) -> None:
        if session is not None:
            await self._ensure_roles_visible(session, "iam:role:delete", payload.ids)
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery, session: SessionPayload | None = None) -> SysRoleSchema:
        if session is not None:
            await self._ensure_roles_visible(session, "iam:role:detail", [query.id])
        schema = to_schema(SysRoleSchema, await self.repo.get_required(query.id))
        await self._resolve_names([schema])
        return schema

    async def page_admin(
        self,
        query: RoleAdminPageQuery,
        session: SessionPayload | None = None,
    ) -> PageData[SysRoleSchema]:
        data_scope_filter = (
            await self._role_scope_filter(session, "iam:role:page") if session is not None else None
        )
        items, total = await self.repo.page_admin(query, data_scope_filter)
        schemas = to_schema_list(SysRoleSchema, items)
        await self._resolve_names(schemas)
        return build_page(query, total, schemas)

    async def own_resource(
        self,
        query: IdQuery,
        session: SessionPayload | None = None,
    ) -> RoleOwnResourceResponse:
        if session is not None:
            await self._ensure_roles_visible(session, "iam:role:ownresource", [query.id])
        return RoleOwnResourceResponse(
            id=query.id,
            modules=await ResourceService(self.db).list_grant_modules(),
            grant_info_list=await self.repo.list_resource_grants(query.id),
        )

    async def grant_resource(
        self,
        payload: RoleGrantResourceRequest,
        session: SessionPayload | None = None,
    ) -> None:
        if session is not None:
            await self._ensure_roles_visible(session, "iam:role:grantresource", [payload.id])
        async with transactional(self.db):
            old_account_ids = await self.repo.list_account_ids_by_role(payload.id)
            await self.repo.replace_resource_grants(payload)
        await self._refresh_accounts(old_account_ids)

    async def own_user(
        self,
        query: IdQuery,
        session: SessionPayload | None = None,
    ) -> RoleOwnUserResponse:
        account_filter = (
            await self._account_scope_filter(session, "iam:role:ownuser")
            if session is not None
            else None
        )
        if session is not None:
            await self._ensure_roles_visible(session, "iam:role:ownuser", [query.id])
        users = await self.repo.list_accounts(account_filter)
        role_users = await self.repo.list_role_accounts(query.id, account_filter)
        return RoleOwnUserResponse(
            id=query.id,
            users=await AccountQueryService(self.db).build_account_schemas(users),
            account_ids=[account.id for account in role_users],
        )

    async def grant_user(
        self,
        payload: RoleGrantUserRequest,
        session: SessionPayload | None = None,
    ) -> None:
        if session is not None:
            await self._ensure_roles_visible(session, "iam:role:grantuser", [payload.id])
            await self._ensure_accounts_visible(session, "iam:role:grantuser", payload.account_ids)
        async with transactional(self.db):
            old_account_ids = await self.repo.list_account_ids_by_role(payload.id)
            await self.repo.replace_role_accounts(payload)
        await self._refresh_accounts(sorted(set(old_account_ids + payload.account_ids)))

    async def _resolve_names(self, dtos: list[SysRoleSchema]) -> None:
        """批量解析部门名称和创建人/更新人昵称。"""
        dept_ids = {d.owner_dept_id for d in dtos if d.owner_dept_id}
        creator_ids = set()
        for d in dtos:
            if d.created_by:
                creator_ids.add(d.created_by)
            if d.updated_by:
                creator_ids.add(d.updated_by)
        if dept_ids:
            dept_map = await self.repo.resolve_dept_names(list(dept_ids))
            for d in dtos:
                if d.owner_dept_id and d.owner_dept_id in dept_map:
                    d.owner_dept_name = dept_map[d.owner_dept_id]
        if creator_ids:
            profiles = await get_profiles_batch(self.db, AccountType.ADMIN, list(creator_ids))
            for d in dtos:
                if d.created_by and d.created_by in profiles:
                    d.created_name = getattr(profiles[d.created_by], "nickname", None)
                if d.updated_by and d.updated_by in profiles:
                    d.updated_name = getattr(profiles[d.updated_by], "nickname", None)

    async def _refresh_accounts(self, account_ids: list[str]) -> None:
        await AccountSessionService(self.db).refresh_accounts_sessions(sorted(set(account_ids)))

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
        if await self.repo.count_roles_in_scope(unique_ids, data_scope_filter) != len(unique_ids):
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
