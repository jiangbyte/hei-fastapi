""" Author: Charlie """

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.core.security.session import SessionPayload, session_store
from app.modules.iam.account.model import SysAccount
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.relation.repository import IamRelationRepository
from app.modules.iam.role.constants import SUPER_ADMIN_ROLE_CODE


class AccountSessionService:
    """构建并刷新账户会话，不依赖 auth 业务流程。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.relation_repo = IamRelationRepository(db)

    async def build_session_payload(
        self,
        account: SysAccount,
        token: str,
        *,
        remember_me: bool = True,
        password_expired: bool = False,
        client_ip: str | None = None,
        user_agent: str | None = None,
        device_label: str | None = None,
    ) -> SessionPayload:
        authorization = await self.relation_repo.get_account_authorization(account.id)
        return self._build_session_payload_from_authorization(
            account,
            token,
            authorization,
            remember_me=remember_me,
            password_expired=password_expired,
            client_ip=client_ip,
            user_agent=user_agent,
            device_label=device_label,
        )

    async def refresh_account_sessions(self, account_id: str) -> None:
        await self.refresh_accounts_sessions([account_id])

    async def refresh_accounts_sessions(self, account_ids: list[str]) -> None:
        accounts = await self.account_repo.list_accounts_by_ids(account_ids)
        if not accounts:
            return
        account_map = {account.id: account for account in accounts}
        authorizations = await self.relation_repo.get_accounts_authorization(
            list(account_map.keys())
        )
        targets = [(account.account_type, account.id) for account in accounts]
        payload_factories = {}

        for account in accounts:
            authorization = authorizations[account.id]

            async def payload_factory(
                token: str,
                current_account: SysAccount = account,
                current_authorization: dict = authorization,
            ) -> SessionPayload:
                # 从旧会话中保留 remember_me
                old = await session_store.get(token)
                return self._build_session_payload_from_authorization(
                    current_account,
                    token,
                    current_authorization,
                    remember_me=old.remember_me if old else True,
                )

            payload_factories[(account.account_type, account.id)] = payload_factory

        await session_store.refresh_accounts_sessions(targets, payload_factories)

    async def delete_account_sessions(self, account_type: str, account_id: str) -> None:
        await session_store.delete_account_sessions(account_type, account_id)

    async def delete_accounts_sessions(self, targets: list[tuple[str, str]]) -> None:
        await session_store.delete_accounts_sessions(targets)

    def _build_session_payload_from_authorization(
        self,
        account: SysAccount,
        token: str,
        authorization: dict,
        *,
        remember_me: bool = True,
        password_expired: bool = False,
        client_ip: str | None = None,
        user_agent: str | None = None,
        device_label: str | None = None,
    ) -> SessionPayload:
        permission_keys = set(authorization["permission_keys"])
        button_codes = set(authorization["button_codes"])
        if SUPER_ADMIN_ROLE_CODE in authorization["role_codes"]:
            permission_keys.add("*:*:*")
            button_codes.add("*:*:*")
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=settings.auth.token_ttl_seconds)
        return SessionPayload(
            token=token,
            account_id=account.id,
            account_type=account.account_type,
            remember_me=remember_me,
            password_expired=password_expired,
            role_ids=authorization["role_ids"],
            dept_ids=authorization["dept_ids"],
            group_ids=authorization["group_ids"],
            resource_ids=authorization["resource_ids"],
            button_codes=sorted(button_codes),
            permission_keys=sorted(permission_keys),
            permission_grants=authorization["permission_grants"],
            client_ip=client_ip,
            user_agent=user_agent,
            device_label=device_label,
            login_at=now.isoformat(),
            last_active_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
        )
