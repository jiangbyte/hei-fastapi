""" Author: Charlie

账户应用服务：账户生命周期、密码策略、授权以及数据范围可见性校验。
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountStatusEnum, AccountType
from app.core.config.reader import config_reader
from app.core.config.settings import settings
from app.core.db.transaction import transactional
from app.core.exceptions.business import AuthorizationError, BusinessError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema
from app.core.security.data_scope import build_data_scope_filter, resolve_data_scope_dept_ids
from app.core.security.password import hash_password
from app.core.security.session import SessionPayload
from app.core.security.transport import decrypt_password
from app.modules.auth.session_service import AccountSessionService
from app.modules.iam.account.model import SysAccount
from app.modules.iam.account.notify import notify_account_cancel_lifecycle
from app.modules.iam.account.query_service import AccountQueryService
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.account.schema import (
    AccountAdminPageQuery,
    AccountCreateRequest,
    AccountDeptAssignRequest,
    AccountGrantClientResourceRequest,
    AccountGrantDeptRequest,
    AccountGrantGroupRequest,
    AccountGrantResourceRequest,
    AccountGrantRoleRequest,
    AccountGroupAssignRequest,
    AccountOwnClientResourceResponse,
    AccountOwnDeptResponse,
    AccountOwnGroupResponse,
    AccountOwnResourceResponse,
    AccountOwnRoleResponse,
    AccountResourceGrantInfo,
    AccountRoleAssignRequest,
    AccountUpdateRequest,
    SysAccountDeptRelSchema,
    SysAccountGroupRelSchema,
    SysAccountRoleRelSchema,
    SysAccountSchema,
)
from app.modules.iam.client.service import ClientResourceService
from app.modules.iam.enums import GrantSubjectType
from app.modules.iam.group.model import SysGroup
from app.modules.iam.group.repository import GroupRepository
from app.modules.iam.relation.model import SysIamRelation
from app.modules.iam.relation.repository import IamRelationRepository
from app.modules.iam.resource.service import ResourceService
from app.modules.iam.role.model import SysRole
from app.modules.iam.role.repository import RoleRepository
from app.modules.user.admin.repository import AdminUserProfileRepository
from app.modules.user.admin.schema import AdminProfileUpsertPayload
from app.modules.user.portal.repository import PortalUserProfileRepository
from app.modules.user.portal.schema import PortalProfileUpsertPayload


class AccountService:
    """账户应用服务，编排仓储与资料仓储完成账户及授权的读写。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AccountRepository(db)
        self.relation_repo = IamRelationRepository(db)

    async def create(self, payload: AccountCreateRequest) -> None:
        """创建账户并同步写入对应端的用户资料。"""
        self._ensure_status_not_cancelled(payload)
        self._ensure_login_contact_payload(payload)
        password = await self._resolve_password(payload.password, payload.password_key_id)
        if not password:
            password = (settings.auth.default_password or "").strip()
        if not password:
            raise BusinessError("Password is required")
        async with transactional(self.db):
            account = await self.repo.create(
                payload,
                password_hash=hash_password(password),
            )
            match payload.account_type:
                case AccountType.ADMIN:
                    await AdminUserProfileRepository(self.db).upsert(
                        self._admin_profile_payload(account.id, payload),
                    )
                case AccountType.PORTAL:
                    await PortalUserProfileRepository(self.db).upsert(
                        self._portal_profile_payload(account.id, payload),
                    )
                case _:
                    raise BusinessError(f"Unsupported account type: {payload.account_type}")

    async def update(
        self,
        payload: AccountUpdateRequest,
        session: SessionPayload | None = None,
    ) -> None:
        """更新账户与资料；传入 session 时先校验账户可见性。"""
        if session is not None:
            await self._ensure_accounts_visible(session, "iam:account:update", [payload.id])
        self._ensure_status_not_cancelled(payload)
        self._ensure_login_contact_payload(payload)
        password = (
            await self._resolve_password(payload.password, payload.password_key_id)
            if payload.password
            else None
        )
        async with transactional(self.db):
            password_hash = hash_password(password) if password else None
            await self.repo.update(payload, password_hash)
            account = await self.repo.get_required(payload.id)
            match account.account_type:
                case AccountType.ADMIN.value:
                    await AdminUserProfileRepository(self.db).upsert(
                        self._admin_profile_payload(payload.id, payload),
                    )
                case AccountType.PORTAL.value:
                    await PortalUserProfileRepository(self.db).upsert(
                        self._portal_profile_payload(payload.id, payload),
                    )
                case _:
                    raise BusinessError(f"Unsupported account type: {account.account_type}")

    async def delete(self, payload: IdsRequest, session: SessionPayload | None = None) -> None:
        """删除账户，并在事务外清理对应在线会话。"""
        if session is not None:
            await self._ensure_accounts_visible(session, "iam:account:delete", payload.ids)
        accounts = await self.repo.list_accounts_by_ids(payload.ids)
        session_targets = [(account.account_type, account.id) for account in accounts]
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)
        if session_targets:
            await AccountSessionService(self.db).delete_accounts_sessions(session_targets)

    async def purge_expired_cancelled_accounts(
        self,
        retention_days: int | None = None,
    ) -> int:
        """彻底删除注销超过保留期的账户，并向快照联系方式发送通知。"""
        days = (
            retention_days
            if retention_days is not None
            else config_reader.get_int("ACCOUNT_CANCEL_RETENTION_DAYS", 15)
        )
        cutoff = datetime.now(UTC) - timedelta(days=days)
        account_ids = await self.repo.list_expired_cancelled_account_ids(cutoff)
        if not account_ids:
            return 0
        accounts = await self.repo.list_accounts_by_ids(account_ids)
        session_targets = [(account.account_type, account.id) for account in accounts]
        notify_jobs = [
            (
                account.cancel_notify_email,
                account.cancel_notify_phone,
            )
            for account in accounts
        ]
        async with transactional(self.db):
            await self.repo.purge_many(account_ids)
        await AccountSessionService(self.db).delete_accounts_sessions(session_targets)
        purged_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
        variables = {
            "app_name": settings.app.name,
            "purged_at": purged_at,
            "retention_days": str(days),
        }
        for email, phone in notify_jobs:
            await notify_account_cancel_lifecycle(
                scene="ACCOUNT_PURGED",
                email=email,
                phone=phone,
                variables=variables,
            )
        return len(account_ids)

    async def detail(
        self,
        query: IdQuery,
        session: SessionPayload | None = None,
    ) -> SysAccountSchema:
        """查询账户详情，传入 session 时先校验可见性。"""
        if session is not None:
            await self._ensure_accounts_visible(session, "iam:account:detail", [query.id])
        accounts = [await self.repo.get_required(query.id)]
        return (await AccountQueryService(self.db).build_account_schemas(accounts))[0]

    async def page_admin(
        self,
        query: AccountAdminPageQuery,
        session: SessionPayload | None = None,
    ) -> PageData[SysAccountSchema]:
        """分页查询账户，叠加当前会话的数据范围过滤。"""
        data_scope_filter = (
            await self._account_scope_filter(session, "iam:account:page")
            if session is not None
            else None
        )
        accounts, total = await self.repo.page_admin(query, data_scope_filter)
        items = await AccountQueryService(self.db).build_account_schemas(accounts)
        return build_page(query, total, items)

    async def assign_account_role(
        self,
        payload: AccountRoleAssignRequest,
        session: SessionPayload | None = None,
    ) -> SysAccountRoleRelSchema:
        """为账户追加单个角色，传入 session 时校验账户与角色可见性。"""
        if session is not None:
            await self._ensure_accounts_visible(
                session,
                "iam:account:grantrole",
                [payload.account_id],
            )
            await self._ensure_roles_visible(session, "iam:account:grantrole", [payload.role_id])
        async with transactional(self.db):
            return to_schema(
                SysAccountRoleRelSchema,
                await self.repo.assign_account_to_role(payload),
            )

    async def assign_account_group(
        self,
        payload: AccountGroupAssignRequest,
        session: SessionPayload | None = None,
    ) -> SysAccountGroupRelSchema:
        """为账户追加单个账户组，传入 session 时校验账户与组可见性。"""
        if session is not None:
            await self._ensure_accounts_visible(
                session,
                "iam:account:grantgroup",
                [payload.account_id],
            )
            await self._ensure_groups_visible(session, "iam:account:grantgroup", [payload.group_id])
        async with transactional(self.db):
            return to_schema(
                SysAccountGroupRelSchema,
                await self.repo.assign_account_to_group(payload),
            )

    async def assign_account_dept(
        self,
        payload: AccountDeptAssignRequest,
        session: SessionPayload | None = None,
    ) -> SysAccountDeptRelSchema:
        """为账户追加单个部门，传入 session 时校验账户与部门可见性。"""
        if session is not None:
            await self._ensure_accounts_visible(
                session,
                "iam:account:grantdept",
                [payload.account_id],
            )
            await self._ensure_depts_visible(session, "iam:account:grantdept", [payload.dept_id])
        async with transactional(self.db):
            return to_schema(
                SysAccountDeptRelSchema,
                await self.repo.assign_account_to_dept(payload),
            )

    async def own_resource(
        self,
        query: IdQuery,
        session: SessionPayload | None = None,
    ) -> AccountOwnResourceResponse:
        """返回账户拥有的资源授权（模块树 + 授权明细）。"""
        if session is not None:
            await self._ensure_accounts_visible(session, "iam:account:ownresource", [query.id])
        account = await self.repo.get_required(query.id)
        account_type = AccountType(account.account_type)
        return AccountOwnResourceResponse(
            id=query.id,
            modules=await ResourceService(self.db).list_grant_modules(
                module_client=account_type,
            ),
            grant_info_list=[
                AccountResourceGrantInfo.model_validate(grant)
                for grant in await self.relation_repo.list_subject_resource_grants(
                    GrantSubjectType.ACCOUNT,
                    query.id,
                    account_type=account.account_type,
                )
            ],
        )

    async def grant_resource(
        self,
        payload: AccountGrantResourceRequest,
        session: SessionPayload | None = None,
    ) -> None:
        """全量替换账户资源授权，并刷新账户会话。"""
        if session is not None:
            await self._ensure_accounts_visible(session, "iam:account:grantresource", [payload.id])
        account = await self.repo.get_required(payload.id)
        async with transactional(self.db):
            await self.relation_repo.replace_subject_resource_grant_infos(
                GrantSubjectType.ACCOUNT,
                payload.id,
                payload.grant_info_list,
                account_type=account.account_type,
            )
        await self._refresh_accounts([payload.id])

    async def own_client_resource(
        self,
        query: IdQuery,
        session: SessionPayload | None = None,
    ) -> AccountOwnClientResourceResponse:
        """返回账户拥有的客户端资源授权。"""
        if session is not None:
            await self._ensure_accounts_visible(
                session, "iam:account:ownclientresource", [query.id]
            )
        account = await self.repo.get_required(query.id)
        account_type = AccountType(account.account_type)
        return AccountOwnClientResourceResponse(
            id=query.id,
            modules=await ClientResourceService(self.db).list_grant_modules(account_type),
            grant_info_list=[
                AccountResourceGrantInfo.model_validate(grant)
                for grant in await self.relation_repo.list_subject_client_resource_grants(
                    GrantSubjectType.ACCOUNT,
                    query.id,
                    account_type=account.account_type,
                )
            ],
        )

    async def grant_client_resource(
        self,
        payload: AccountGrantClientResourceRequest,
        session: SessionPayload | None = None,
    ) -> None:
        """全量替换账户客户端资源授权，并刷新账户会话。"""
        if session is not None:
            await self._ensure_accounts_visible(
                session, "iam:account:grantclientresource", [payload.id]
            )
        account = await self.repo.get_required(payload.id)
        async with transactional(self.db):
            await self.relation_repo.replace_subject_client_resource_grant_infos(
                GrantSubjectType.ACCOUNT,
                payload.id,
                payload.grant_info_list,
                account_type=account.account_type,
            )
        await self._refresh_accounts([payload.id])

    async def own_role(
        self,
        query: IdQuery,
        session: SessionPayload | None = None,
    ) -> AccountOwnRoleResponse:
        """返回账户直接绑定的角色（叠加角色数据范围过滤）。"""
        role_filter = (
            await self._role_scope_filter(session, "iam:account:ownrole")
            if session is not None
            else None
        )
        if session is not None:
            await self._ensure_accounts_visible(session, "iam:account:ownrole", [query.id])
        role_ids = await self.repo.list_account_direct_role_ids(query.id, role_filter)
        return AccountOwnRoleResponse(
            id=query.id,
            roles=await self.repo.list_roles_by_ids(role_ids),
            role_ids=role_ids,
        )

    async def grant_role(
        self,
        payload: AccountGrantRoleRequest,
        session: SessionPayload | None = None,
    ) -> None:
        """全量替换账户角色，并刷新账户会话。"""
        if session is not None:
            await self._ensure_accounts_visible(session, "iam:account:grantrole", [payload.id])
            await self._ensure_roles_visible(session, "iam:account:grantrole", payload.role_ids)
        async with transactional(self.db):
            await self.repo.replace_account_roles(payload)
        await self._refresh_accounts([payload.id])

    async def own_group(
        self,
        query: IdQuery,
        session: SessionPayload | None = None,
    ) -> AccountOwnGroupResponse:
        """返回账户直接绑定的账户组（叠加组数据范围过滤）。"""
        group_filter = (
            await self._group_scope_filter(session, "iam:account:owngroup")
            if session is not None
            else None
        )
        if session is not None:
            await self._ensure_accounts_visible(session, "iam:account:owngroup", [query.id])
        group_ids = await self.repo.list_account_direct_group_ids(query.id, group_filter)
        return AccountOwnGroupResponse(
            id=query.id,
            groups=await self.repo.list_groups_by_ids(group_ids),
            group_ids=group_ids,
        )

    async def grant_group(
        self,
        payload: AccountGrantGroupRequest,
        session: SessionPayload | None = None,
    ) -> None:
        """全量替换账户账户组，并刷新账户会话。"""
        if session is not None:
            await self._ensure_accounts_visible(session, "iam:account:grantgroup", [payload.id])
            await self._ensure_groups_visible(session, "iam:account:grantgroup", payload.group_ids)
        async with transactional(self.db):
            await self.repo.replace_account_groups(payload)
        await self._refresh_accounts([payload.id])

    async def own_dept(
        self,
        query: IdQuery,
        session: SessionPayload | None = None,
    ) -> AccountOwnDeptResponse:
        """返回账户的部门授权（仅返回当前可见部门）。"""
        if session is not None:
            await self._ensure_accounts_visible(session, "iam:account:owndept", [query.id])
        visible_dept_ids = (
            await resolve_data_scope_dept_ids(self.db, session, "iam:account:owndept")
            if session is not None
            else None
        )
        return AccountOwnDeptResponse(
            id=query.id,
            grant_info_list=await self.repo.list_account_dept_grants(query.id, visible_dept_ids),
        )

    async def grant_dept(
        self,
        payload: AccountGrantDeptRequest,
        session: SessionPayload | None = None,
    ) -> None:
        """全量替换账户部门，并刷新账户会话。"""
        if session is not None:
            await self._ensure_accounts_visible(session, "iam:account:grantdept", [payload.id])
            await self._ensure_depts_visible(
                session,
                "iam:account:grantdept",
                [item.dept_id for item in payload.grant_info_list],
            )
        async with transactional(self.db):
            await self.repo.replace_account_depts(payload)
        await self._refresh_accounts([payload.id])

    async def _refresh_accounts(self, account_ids: list[str]) -> None:
        """刷新指定账户的在线会话缓存。"""
        await AccountSessionService(self.db).refresh_accounts_sessions(sorted(set(account_ids)))

    async def _account_scope_filter(self, session: SessionPayload, permission_key: str):
        """构造账户数据范围过滤条件。"""
        return await build_data_scope_filter(
            self.db,
            session,
            permission_key,
            owner_column=SysAccount.id,
            dept_column=SysIamRelation.target_id,
        )

    async def _role_scope_filter(self, session: SessionPayload, permission_key: str):
        """构造角色数据范围过滤条件。"""
        return await build_data_scope_filter(
            self.db,
            session,
            permission_key,
            owner_column=SysRole.created_by,
            dept_column=SysRole.owner_dept_id,
        )

    async def _group_scope_filter(self, session: SessionPayload, permission_key: str):
        """构造账户组数据范围过滤条件。"""
        return await build_data_scope_filter(
            self.db,
            session,
            permission_key,
            owner_column=SysGroup.created_by,
            dept_column=SysGroup.owner_dept_id,
        )

    async def _ensure_accounts_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        account_ids: list[str],
    ) -> None:
        """校验目标账户均在当前数据范围内，否则抛授权错误。"""
        unique_ids = list(dict.fromkeys(account_ids))
        if not unique_ids:
            return
        data_scope_filter = await self._account_scope_filter(session, permission_key)
        count = await self.repo.count_accounts_in_scope(unique_ids, data_scope_filter)
        if count != len(unique_ids):
            raise AuthorizationError("Account is outside current data scope")

    async def _ensure_roles_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        role_ids: list[str],
    ) -> None:
        """校验目标角色均在当前数据范围内，否则抛授权错误。"""
        unique_ids = list(dict.fromkeys(role_ids))
        if not unique_ids:
            return
        data_scope_filter = await self._role_scope_filter(session, permission_key)
        count = await RoleRepository(self.db).count_roles_in_scope(unique_ids, data_scope_filter)
        if count != len(unique_ids):
            raise AuthorizationError("Role is outside current data scope")

    async def _ensure_groups_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        group_ids: list[str],
    ) -> None:
        """校验目标账户组均在当前数据范围内，否则抛授权错误。"""
        unique_ids = list(dict.fromkeys(group_ids))
        if not unique_ids:
            return
        data_scope_filter = await self._group_scope_filter(session, permission_key)
        count = await GroupRepository(self.db).count_groups_in_scope(unique_ids, data_scope_filter)
        if count != len(unique_ids):
            raise AuthorizationError("Group is outside current data scope")

    async def _ensure_depts_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        dept_ids: list[str],
    ) -> None:
        """校验目标部门均在当前可见部门集合内，否则抛授权错误。"""
        unique_ids = list(dict.fromkeys(dept_ids))
        if not unique_ids:
            return
        visible_dept_ids = await resolve_data_scope_dept_ids(self.db, session, permission_key)
        if visible_dept_ids is None:
            return
        if any(dept_id not in set(visible_dept_ids) for dept_id in unique_ids):
            raise AuthorizationError("Dept is outside current data scope")

    def _admin_profile_payload(
        self,
        account_id: str,
        payload: AccountCreateRequest | AccountUpdateRequest,
    ) -> AdminProfileUpsertPayload:
        """从账户请求构造管理端用户资料载荷。"""
        return AdminProfileUpsertPayload(
            account_id=account_id,
            name=payload.name,
            nickname=payload.nickname,
            avatar=payload.avatar,
            signature=payload.signature,
            phone=payload.phone,
            email=payload.email,
            remark=payload.remark,
        )

    def _portal_profile_payload(
        self,
        account_id: str,
        payload: AccountCreateRequest | AccountUpdateRequest,
    ) -> PortalProfileUpsertPayload:
        """从账户请求构造门户端用户资料载荷。"""
        return PortalProfileUpsertPayload(
            account_id=account_id,
            name=payload.name,
            nickname=payload.nickname,
            avatar=payload.avatar,
            signature=payload.signature,
            phone=payload.phone,
            email=payload.email,
        )

    def _ensure_status_not_cancelled(
        self,
        payload: AccountCreateRequest | AccountUpdateRequest,
    ) -> None:
        """禁止通过管理端将账户状态直接设为已注销。"""
        if payload.account_status == AccountStatusEnum.CANCELLED:
            raise BusinessError("注销状态不允许通过管理端设置")

    def _ensure_login_contact_payload(
        self,
        payload: AccountCreateRequest | AccountUpdateRequest,
    ) -> None:
        """启用邮箱/手机号登录时校验对应联系方式非空。"""
        if (
            payload.email_login_enabled
            and not str(payload.email_identity or payload.email or "").strip()
        ):
            raise BusinessError("Email login requires an email")
        if (
            payload.phone_login_enabled
            and not str(payload.phone_identity or payload.phone or "").strip()
        ):
            raise BusinessError("Phone login requires a phone")

    async def _resolve_password(self, password: str, password_key_id: str | None) -> str:
        """按传输密钥解密密码，无密钥时原样返回。"""
        if not password_key_id:
            return password
        return await decrypt_password(password_key_id, password)
