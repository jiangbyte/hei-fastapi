""" Author: Charlie """

import json
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountStatusEnum, AccountType
from app.core.config.settings import settings
from app.core.exceptions.business import AuthenticationError, BusinessError
from app.core.security.password import hash_password, verify_password
from app.core.security.session import SessionPayload, session_store
from app.core.security.token import generate_token
from app.modules.auth.policy import (
    ensure_identity_allowed,
    get_register_policy,
    no_user_policy_for,
)
from app.modules.auth.protection import login_protection_service
from app.modules.auth.schema import (
    CancelAccountRequest,
    ForgotPasswordRequest,
    LoginPayload,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
)
from app.modules.auth.session_service import AccountSessionService
from app.modules.iam.account.model import SysAccount
from app.modules.iam.account.notify import notify_account_cancel_lifecycle
from app.modules.iam.account.password_helper import (
    get_password_age_days,
    is_password_expired,
    validate_and_record_password,
)
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.account.schema import (
    AccountCreateRequest,
    AccountDeptAssignRequest,
    AccountRoleAssignRequest,
)
from app.modules.iam.enums import AccountIdentityType
from app.modules.sys.audit.service import OperationAuditService
from app.modules.user.portal.repository import PortalUserProfileRepository
from app.modules.user.portal.schema import PortalProfileUpsertPayload
from app.platform.cache.keys import login_otp_key, password_reset_token_key
from app.platform.cache.redis import get_redis
from app.platform.config.reader import config_reader
from app.platform.db.transaction import transactional
from app.platform.email.sender import send_templated_mail
from app.platform.observability.metrics import record_login_attempt
from app.platform.sms.sender import send_templated_sms

_PASSWORD_RESET_URL_KEYS = {
    AccountType.ADMIN: "AUTH_PASSWORD_RESET_URL_ADMIN",
    AccountType.PORTAL: "AUTH_PASSWORD_RESET_URL_PORTAL",
}


class AuthService:
    """认证服务，负责登录态签发、账户类型校验与会话数据组装。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.session_service = AccountSessionService(db)

    async def login(self, payload: LoginPayload) -> SessionPayload:
        """执行登录流程并签发会话。"""
        login_mode = (payload.login_mode or "PASSWORD").strip().upper()
        try:
            ensure_identity_allowed(
                payload.account_type,
                payload.identity_type,
                login_mode=login_mode,
            )
            await login_protection_service.ensure_allowed(
                account_type=payload.account_type,
                account=payload.account,
                client_ip=payload.client_ip,
            )
            account = await self.account_repo.get_account_by_identifier(
                payload.account,
                [payload.identity_type],
            )
            if account is None:
                account = await self._maybe_auto_create(payload)
            if login_mode == "OTP":
                await self._verify_login_otp(payload)
                self._validate_account_status(account, payload.account_type)
            else:
                self._validate_account(account, payload.password or "", payload.account_type)
        except (AuthenticationError, BusinessError):
            await login_protection_service.record_failure(
                account_type=payload.account_type,
                account=payload.account,
                client_ip=payload.client_ip,
            )
            record_login_attempt(payload.account_type.value, "failure", "invalid_credentials")
            await OperationAuditService(self.db).record(
                module="auth",
                action="login",
                resource_type="account",
                resource_id=payload.account,
                summary=f"{payload.account_type.value} login failed",
                success=False,
                error_message="Invalid or locked login attempt",
                account_type=payload.account_type.value,
                ip=payload.client_ip,
                user_agent=payload.user_agent,
            )
            raise
        assert account is not None
        return await self._issue_session(account, payload)

    async def send_login_code(
        self,
        *,
        account_type: AccountType,
        channel: str,
        target: str,
        client_ip: str | None = None,
    ) -> None:
        channel_u = channel.strip().upper()
        identity = (
            AccountIdentityType.EMAIL if channel_u == "EMAIL" else AccountIdentityType.PHONE
        )
        policy = ensure_identity_allowed(account_type, identity, login_mode="OTP")
        normalized = target.strip().lower() if channel_u == "EMAIL" else target.strip()
        account = await self.account_repo.get_account_by_identifier(normalized, [identity])
        if account is None:
            policy_name = no_user_policy_for(policy, identity)
            if policy_name != "AUTO_CREATE":
                # 不泄露用户是否存在
                return
        code = f"{secrets.randbelow(1_000_000):06d}"
        redis = self._required_redis("Redis is required for OTP login")
        ttl = settings.auth.password_reset_token_ttl_seconds
        await redis.setex(login_otp_key(account_type.value, channel_u, normalized), ttl, code)
        variables = {
            "app_name": settings.app.name,
            "code": code,
            "expire_minutes": max(1, ttl // 60),
        }
        if channel_u == "EMAIL":
            await send_templated_mail("LOGIN_CODE", normalized, variables)
        else:
            await send_templated_sms("LOGIN_CODE", normalized, variables)

    async def _verify_login_otp(self, payload: LoginPayload) -> None:
        code = (payload.otp_code or "").strip()
        if not code:
            raise AuthenticationError("Invalid or expired OTP code")
        channel = (
            "EMAIL"
            if payload.identity_type == AccountIdentityType.EMAIL
            else "PHONE"
            if payload.identity_type == AccountIdentityType.PHONE
            else ""
        )
        if not channel:
            raise BusinessError("OTP login requires email or phone")
        normalized = (
            payload.account.strip().lower()
            if channel == "EMAIL"
            else payload.account.strip()
        )
        redis = self._required_redis("Redis is required for OTP login")
        key = login_otp_key(payload.account_type.value, channel, normalized)
        raw = await redis.get(key)
        stored = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if not stored or stored != code:
            raise AuthenticationError("Invalid or expired OTP code")
        await redis.delete(key)

    async def _maybe_auto_create(self, payload: LoginPayload) -> SysAccount | None:
        policy = ensure_identity_allowed(
            payload.account_type,
            payload.identity_type,
            login_mode=payload.login_mode,
        )
        if no_user_policy_for(policy, payload.identity_type) != "AUTO_CREATE":
            return None
        if payload.account_type == AccountType.ADMIN:
            # 管理端默认仍 DENY；仅显式 AUTO_CREATE 才会走到这里
            pass
        identity = payload.account.strip()
        email = identity if payload.identity_type == AccountIdentityType.EMAIL else None
        phone = identity if payload.identity_type == AccountIdentityType.PHONE else None
        account_name = f"u_{uuid4().hex[:10]}"
        default_password = (settings.auth.default_password or secrets.token_urlsafe(12)).strip()
        async with transactional(self.db):
            account = await self.account_repo.create(
                AccountCreateRequest(
                    account=account_name,
                    password=default_password,
                    account_type=payload.account_type,
                    account_status=AccountStatusEnum.ENABLED,
                    email=email,
                    phone=phone,
                    email_login_enabled=bool(email),
                    phone_login_enabled=bool(phone),
                    email_identity_verified=bool(email),
                    phone_identity_verified=bool(phone),
                ),
                password_hash=hash_password(default_password),
            )
            if payload.account_type == AccountType.PORTAL:
                await PortalUserProfileRepository(self.db).upsert(
                    PortalProfileUpsertPayload(
                        account_id=account.id,
                        name=None,
                        nickname=account_name,
                        phone=phone,
                        email=email,
                        avatar=None,
                        signature=None,
                        bio=None,
                        level=None,
                    ),
                )
            await self._assign_register_defaults(account.id, payload.account_type)
        return account

    async def password_expiry_warning_days(self, account_id: str) -> int | None:
        warning = settings.password_policy.expiry_warning_days
        expire_days = settings.password_policy.expire_days
        if warning <= 0 or expire_days <= 0:
            return None
        age = await get_password_age_days(self.db, account_id)
        if age is None:
            return None
        remaining = expire_days - age
        if 0 < remaining <= warning:
            return int(remaining)
        return None

    async def _issue_session(self, account: SysAccount, payload: LoginPayload) -> SessionPayload:
        password_expired_ = await is_password_expired(self.db, account.id)
        session_payload = await self.session_service.build_session_payload(
            account,
            generate_token(),
            remember_me=payload.remember_me,
            password_expired=password_expired_,
            client_ip=payload.client_ip,
            user_agent=payload.user_agent,
            device_label=payload.device_label,
        )
        ttl = (
            settings.auth.token_ttl_seconds
            if payload.remember_me
            else settings.auth.token_ttl_short_seconds
        )
        await session_store.set(session_payload, ttl_seconds=ttl)
        await session_store.prune_excess_sessions(
            account_type=str(session_payload.account_type),
            account_id=session_payload.account_id,
            max_sessions=settings.auth.max_concurrent_sessions,
        )
        await login_protection_service.record_success(
            account_type=payload.account_type,
            account=payload.account,
            client_ip=payload.client_ip,
        )
        record_login_attempt(payload.account_type.value, "success")
        await OperationAuditService(self.db).record(
            module="auth",
            action="login",
            resource_type="account",
            resource_id=account.id,
            summary=f"{payload.account_type.value} login succeeded",
            success=True,
            account_id=account.id,
            account_type=account.account_type,
            ip=payload.client_ip,
            user_agent=payload.user_agent,
        )
        return session_payload

    async def register_portal(self, payload: RegisterRequest) -> RegisterResponse:
        policy = get_register_policy(AccountType.PORTAL)
        if not policy.enabled:
            raise BusinessError("Portal registration is disabled")
        email = (payload.email or "").strip().lower() or None
        phone = (payload.phone or "").strip() or None
        if policy.require_email and not email:
            raise BusinessError("Email is required for registration")
        if policy.require_phone and not phone:
            raise BusinessError("Phone is required for registration")
        nickname = (payload.nickname or "").strip() or f"user-{uuid4().hex[:8]}"
        async with transactional(self.db):
            account_payload = AccountCreateRequest(
                account=payload.account,
                password=payload.password,
                account_type=AccountType.PORTAL,
                account_status=AccountStatusEnum.ENABLED,
                name=payload.name,
                nickname=nickname,
                email=email,
                phone=phone,
                email_login_enabled=bool(email),
                phone_login_enabled=bool(phone),
                email_identity_verified=bool(email),
                phone_identity_verified=bool(phone),
            )
            account = await self.account_repo.create(
                account_payload,
                password_hash=hash_password(payload.password),
            )
            await validate_and_record_password(
                self.db,
                account.id,
                payload.password,
                changed_by=account.id,
                change_reason="register",
                account=account,
                account_name=payload.account,
                email=email,
                phone=phone,
            )
            await PortalUserProfileRepository(self.db).upsert(
                PortalProfileUpsertPayload(
                    account_id=account.id,
                    name=payload.name,
                    nickname=nickname,
                    phone=phone,
                    email=email,
                    avatar=None,
                    signature=None,
                    bio=None,
                    level=None,
                ),
            )
            await self._assign_register_defaults(account.id, AccountType.PORTAL)
        if email:
            try:
                await send_templated_mail(
                    "REGISTER_SUCCESS",
                    email,
                    {"app_name": settings.app.name, "account": payload.account},
                )
            except BusinessError:
                pass
        response = RegisterResponse(
            account_id=account.id,
            account=payload.account,
            account_type=AccountType.PORTAL,
        )
        await OperationAuditService(self.db).record(
            module="auth",
            action="register",
            resource_type="account",
            resource_id=account.id,
            summary="Portal account registered",
            success=True,
            account_id=account.id,
            account_type=AccountType.PORTAL.value,
        )
        return response

    async def _assign_register_defaults(self, account_id: str, account_type: AccountType) -> None:
        policy = get_register_policy(account_type)
        if policy.default_role_id:
            await self.account_repo.assign_account_to_role(
                AccountRoleAssignRequest(account_id=account_id, role_id=policy.default_role_id)
            )
        if policy.default_dept_id:
            await self.account_repo.assign_account_to_dept(
                AccountDeptAssignRequest(
                    account_id=account_id,
                    dept_id=policy.default_dept_id,
                    is_primary=True,
                )
            )

    async def forgot_password(
        self,
        payload: ForgotPasswordRequest,
        account_type: AccountType,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        email = payload.email.strip().lower()
        account = await self.account_repo.get_account_by_identifier(
            email,
            [AccountIdentityType.EMAIL],
        )
        if account is None or account.account_type != account_type.value:
            await self._record_password_reset_request(
                account_type,
                email,
                False,
                client_ip,
                user_agent,
            )
            return
        try:
            self._validate_account_status(account, account_type)
        except AuthenticationError:
            await self._record_password_reset_request(
                account_type,
                email,
                False,
                client_ip,
                user_agent,
            )
            return

        reset_token = generate_token()
        redis = self._required_redis("Redis is required for password reset")
        await redis.setex(
            password_reset_token_key(reset_token),
            settings.auth.password_reset_token_ttl_seconds,
            json.dumps(
                {
                    "account_id": account.id,
                    "account_type": account_type.value,
                    "email": email,
                    "token_hash": hash_password(reset_token),
                }
            ),
        )
        reset_link = self._build_password_reset_link(account_type, reset_token)
        expire_minutes = settings.auth.password_reset_token_ttl_seconds // 60
        await send_templated_mail(
            "RESET_PASSWORD_CODE",
            email,
            {
                "app_name": settings.app.name,
                "reset_link": reset_link,
                "email": email,
                "expire_minutes": expire_minutes,
            },
        )
        await self._record_password_reset_request(
            account_type,
            email,
            True,
            client_ip,
            user_agent,
            account.id,
        )

    async def reset_password(
        self,
        payload: ResetPasswordRequest,
        account_type: AccountType,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        key = password_reset_token_key(payload.token)
        redis = self._required_redis("Redis is required for password reset")
        raw = await redis.get(key)
        raw_text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if not raw_text:
            raise AuthenticationError("Invalid or expired reset link")
        data = json.loads(raw_text)
        # 身份只绑定在 token→Redis 载荷上，禁止把邮箱放进重置链接或要求客户端回传
        if (
            not data.get("account_id")
            or data.get("account_type") != account_type.value
            or not verify_password(payload.token, data["token_hash"])
        ):
            raise AuthenticationError("Invalid or expired reset link")

        account = await self.account_repo.get_required(str(data["account_id"]))
        self._validate_account_status(account, account_type)
        async with transactional(self.db):
            await validate_and_record_password(
                self.db,
                account.id,
                payload.password,
                changed_by=account.id,
                change_reason="self_reset",
                account=account,
            )
            await self.account_repo.update_password_hash(
                account.id, hash_password(payload.password)
            )
        await redis.delete(key)
        await self.session_service.delete_account_sessions(account.account_type, account.id)
        await OperationAuditService(self.db).record(
            module="auth",
            action="reset_password",
            resource_type="account",
            resource_id=account.id,
            summary=f"{account_type.value} password reset",
            success=True,
            account_id=account.id,
            account_type=account.account_type,
            ip=client_ip,
            user_agent=user_agent,
        )

    async def logout(self, token: str) -> None:
        """注销指定 token 对应的会话。"""
        await session_store.delete(token)
        await OperationAuditService(self.db).record(
            module="auth",
            action="logout",
            resource_type="account",
            resource_id=token,
            summary="Logout",
            success=True,
        )

    async def cancel_current_account(
        self,
        payload: CancelAccountRequest,
        session: SessionPayload,
    ) -> None:
        """注销当前登录账号，并清理该账号下全部会话。"""
        from app.modules.iam.account.schema import AccountCancelPayload

        async with transactional(self.db):
            account = await self.account_repo.cancel(
                AccountCancelPayload(
                    id=session.account_id,
                    cancel_reason=payload.cancel_reason,
                ),
                cancelled_by=session.account_id,
            )
        await self.session_service.delete_account_sessions(account.account_type, account.id)
        await OperationAuditService(self.db).record(
            module="auth",
            action="cancel_account",
            resource_type="account",
            resource_id=account.id,
            summary="Cancel current account",
            success=True,
            account_id=account.id,
            account_type=account.account_type,
        )
        retention_days = config_reader.get_int("ACCOUNT_CANCEL_RETENTION_DAYS", 15)
        cancelled_at = account.cancelled_at or datetime.now(UTC)
        purge_at = (cancelled_at + timedelta(days=retention_days)).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
        await notify_account_cancel_lifecycle(
            scene="ACCOUNT_CANCELLED",
            email=account.cancel_notify_email,
            phone=account.cancel_notify_phone,
            variables={
                "app_name": settings.app.name,
                "retention_days": str(retention_days),
                "purge_at": purge_at,
            },
        )

    def _validate_account(
        self,
        account: SysAccount | None,
        password: str,
        account_type: AccountType,
    ) -> None:
        """校验账号密码、账号状态以及目标账户类型是否允许访问。"""
        if not account or not verify_password(password, account.password_hash):
            raise AuthenticationError("Invalid account or password")
        self._validate_account_status(account, account_type)

    def _validate_account_status(
        self,
        account: SysAccount | None,
        account_type: AccountType,
    ) -> None:
        if account is None:
            raise AuthenticationError("Invalid account or password")
        if (
            account.account_status == AccountStatusEnum.CANCELLED.value
            or account.cancelled_at is not None
        ):
            raise AuthenticationError("Account is cancelled")
        if account.account_status != AccountStatusEnum.ENABLED.value:
            raise AuthenticationError("Account is inactive")
        if account_type == AccountType.ADMIN and account.account_type != AccountType.ADMIN.value:
            raise AuthenticationError("Account is not allowed to access admin account type")
        if account_type == AccountType.PORTAL and account.account_type != AccountType.PORTAL.value:
            raise AuthenticationError("Account is not allowed to access portal account type")

    def _required_redis(self, message: str = "Redis is required"):
        redis = get_redis()
        if redis is None:
            raise BusinessError(message)
        return redis

    def _build_password_reset_link(self, account_type: AccountType, token: str) -> str:
        config_key = _PASSWORD_RESET_URL_KEYS.get(account_type)
        if not config_key:
            raise BusinessError(f"Unsupported account type for password reset: {account_type}")
        base_url = (config_reader.get(config_key) or "").strip()
        if not base_url:
            raise BusinessError(f"Missing sys_config: {config_key}")
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}{urlencode({'token': token})}"

    async def _record_password_reset_request(
        self,
        account_type: AccountType,
        email: str,
        success: bool,
        client_ip: str | None,
        user_agent: str | None,
        account_id: str | None = None,
    ) -> None:
        await OperationAuditService(self.db).record(
            module="auth",
            action="forgot_password",
            resource_type="account",
            resource_id=account_id or email,
            summary=f"{account_type.value} password reset requested",
            success=success,
            account_id=account_id,
            account_type=account_type.value,
            ip=client_ip,
            user_agent=user_agent,
        )
