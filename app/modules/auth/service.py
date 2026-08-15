""" Author: Charlie

认证服务：登录签发、登录验证码、注册、密码找回/重置、注销与账号注销等核心业务逻辑。
"""

import json
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache.keys import (
    bind_otp_key,
    login_otp_key,
    password_reset_token_key,
    register_otp_key,
)
from app.core.cache.redis import get_redis
from app.core.config.enums import AccountStatusEnum, AccountType
from app.core.config.reader import config_reader
from app.core.config.settings import settings
from app.core.db.transaction import transactional
from app.core.email.sender import send_templated_mail
from app.core.exceptions.business import AuthenticationError, BusinessError
from app.core.observability.metrics import record_login_attempt
from app.core.security.password import hash_password, verify_password
from app.core.security.session import SessionPayload, session_store
from app.core.security.token import generate_token
from app.core.sms.sender import send_templated_sms
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
    LoginResponse,
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
from app.modules.user.portal.repository import ProfileUserPortalRepository
from app.modules.user.portal.schema import ProfileUserPortalUpsertPayload

# 各账户类型对应的密码重置链接模板配置键。
_PASSWORD_RESET_URL_KEYS = {
    AccountType.ADMIN: "AUTH_PASSWORD_RESET_URL_ADMIN",
    AccountType.PORTAL: "AUTH_PASSWORD_RESET_URL_PORTAL",
}


class AuthService:
    """认证服务，负责登录态签发、账户类型校验与会话数据组装。"""

    def __init__(self, db: AsyncSession):
        """初始化仓储与账户会话服务。"""
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
        """按渠道发送登录验证码，未绑定且策略不允许自动创建时不泄露用户是否存在。"""
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
        """校验 OTP 登录验证码，成功后一次性消费。"""
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

    async def send_bind_code(
        self,
        *,
        account_type: AccountType,
        channel: str,
        target: str,
        account_id: str,
    ) -> None:
        """向待绑定邮箱/手机发送验证码，目标已被其他账号占用时拒绝。"""
        channel_u = channel.strip().upper()
        if channel_u not in {"EMAIL", "PHONE"}:
            raise BusinessError("Unsupported bind channel")
        identity_type = (
            AccountIdentityType.EMAIL
            if channel_u == "EMAIL"
            else AccountIdentityType.PHONE
        )
        normalized = (
            target.strip().lower() if channel_u == "EMAIL" else target.strip()
        )
        if not normalized:
            raise BusinessError("Target is required")
        other = await self.account_repo.get_account_by_identifier(
            normalized, [identity_type]
        )
        if other is not None and other.id != account_id:
            raise BusinessError(
                "邮箱已被使用" if channel_u == "EMAIL" else "手机号已被使用"
            )
        code = f"{secrets.randbelow(1_000_000):06d}"
        redis = self._required_redis("Redis is required for bind verification")
        ttl = settings.auth.password_reset_token_ttl_seconds
        await redis.setex(
            bind_otp_key(account_type.value, channel_u, account_id),
            ttl,
            code,
        )
        variables = {
            "app_name": settings.app.name,
            "code": code,
            "expire_minutes": max(1, ttl // 60),
        }
        if channel_u == "EMAIL":
            await send_templated_mail("BIND_EMAIL_CODE", normalized, variables)
        else:
            await send_templated_sms("BIND_PHONE_CODE", normalized, variables)

    async def consume_bind_code(
        self,
        *,
        account_type: AccountType,
        channel: str,
        account_id: str,
        target: str,
        code: str | None,
    ) -> None:
        """校验并一次性消费绑定验证码（未提供或无效时抛错）。"""
        code_value = (code or "").strip()
        if not code_value:
            raise BusinessError("验证码不能为空")
        channel_u = channel.strip().upper()
        redis = self._required_redis("Redis is required for bind verification")
        key = bind_otp_key(account_type.value, channel_u, account_id)
        raw = await redis.get(key)
        stored = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if not stored or stored != code_value:
            raise BusinessError("验证码无效或已过期")
        await redis.delete(key)

    async def send_register_code(self, *, channel: str, target: str) -> None:
        """发送门户注册通道（邮箱/手机）验证码。"""
        channel_u = channel.strip().upper()
        if channel_u not in {"EMAIL", "PHONE"}:
            raise BusinessError("Unsupported register channel")
        identity_type = (
            AccountIdentityType.EMAIL
            if channel_u == "EMAIL"
            else AccountIdentityType.PHONE
        )
        normalized = (
            target.strip().lower() if channel_u == "EMAIL" else target.strip()
        )
        if not normalized:
            raise BusinessError("Target is required")
        if await self.account_repo.get_account_by_identifier(
            normalized, [identity_type]
        ) is not None:
            raise BusinessError(
                "邮箱已被使用" if channel_u == "EMAIL" else "手机号已被使用"
            )
        code = f"{secrets.randbelow(1_000_000):06d}"
        redis = self._required_redis("Redis is required for register verification")
        ttl = settings.auth.password_reset_token_ttl_seconds
        await redis.setex(register_otp_key(channel_u, normalized), ttl, code)
        variables = {
            "app_name": settings.app.name,
            "code": code,
            "expire_minutes": max(1, ttl // 60),
        }
        if channel_u == "EMAIL":
            await send_templated_mail("REGISTER_CODE", normalized, variables)
        else:
            await send_templated_sms("REGISTER_CODE", normalized, variables)

    async def consume_register_code(
        self, *, channel: str, target: str, code: str | None
    ) -> None:
        """校验并一次性消费注册通道验证码。"""
        code_value = (code or "").strip()
        if not code_value:
            raise BusinessError("验证码不能为空")
        channel_u = channel.strip().upper()
        normalized = (
            target.strip().lower() if channel_u == "EMAIL" else target.strip()
        )
        redis = self._required_redis("Redis is required for register verification")
        key = register_otp_key(channel_u, normalized)
        raw = await redis.get(key)
        stored = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if not stored or stored != code_value:
            raise BusinessError("验证码无效或已过期")
        await redis.delete(key)

    async def _maybe_auto_create(self, payload: LoginPayload) -> SysAccount | None:
        """当策略允许 AUTO_CREATE 时自动创建账户并返回，否则返回 None。"""
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
                await ProfileUserPortalRepository(self.db).upsert(
                    ProfileUserPortalUpsertPayload(
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
        """返回密码剩余有效天数（仅在临近过期时），否则返回 None。"""
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
        """组装会话载荷、写入会话存储并记录审计与指标。"""
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
        force_bind_email, force_bind_phone = await self._force_bind_flags(
            account, payload.account_type
        )
        session_payload.force_bind_email = force_bind_email
        session_payload.force_bind_phone = force_bind_phone
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

    async def issue_oauth_session(
        self,
        account: SysAccount,
        account_type: AccountType,
        *,
        login_label: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
        device_label: str | None = None,
    ) -> LoginResponse:
        """为 OAuth 登录签发会话并返回登录结果（含强制绑定标记）。"""
        password_expired_ = await is_password_expired(self.db, account.id)
        session_payload = await self.session_service.build_session_payload(
            account,
            generate_token(),
            remember_me=True,
            password_expired=password_expired_,
            client_ip=client_ip,
            user_agent=user_agent,
            device_label=device_label,
        )
        force_bind_email, force_bind_phone = await self._force_bind_flags(
            account, account_type
        )
        session_payload.force_bind_email = force_bind_email
        session_payload.force_bind_phone = force_bind_phone
        await session_store.set(
            session_payload, ttl_seconds=settings.auth.token_ttl_seconds
        )
        await session_store.prune_excess_sessions(
            account_type=str(session_payload.account_type),
            account_id=session_payload.account_id,
            max_sessions=settings.auth.max_concurrent_sessions,
        )
        record_login_attempt(account_type.value, "success")
        await OperationAuditService(self.db).record(
            module="auth",
            action="oauth_login",
            resource_type="account",
            resource_id=account.id,
            summary=f"{account_type.value} oauth login succeeded",
            success=True,
            account_id=account.id,
            account_type=account.account_type,
            ip=client_ip,
            user_agent=user_agent,
        )
        return LoginResponse(
            token=session_payload.token,
            account_id=account.id,
            account_type=account_type,
            password_expired=password_expired_,
            password_expiry_warning_days=await self.password_expiry_warning_days(
                account.id
            ),
            force_bind_email=session_payload.force_bind_email,
            force_bind_phone=session_payload.force_bind_phone,
        )

    async def _force_bind_flags(
        self, account: SysAccount, account_type: AccountType
    ) -> tuple[bool, bool]:
        """按 AUTH_FORCE_BIND_{TYPE}_{EMAIL|PHONE} 配置与账号已绑定身份计算强制绑定标记。"""
        type_name = account_type.value
        force_email = config_reader.get_bool(
            f"AUTH_FORCE_BIND_{type_name}_EMAIL", False
        ) and not await self.account_repo.has_identity(account.id, AccountIdentityType.EMAIL)
        force_phone = config_reader.get_bool(
            f"AUTH_FORCE_BIND_{type_name}_PHONE", False
        ) and not await self.account_repo.has_identity(account.id, AccountIdentityType.PHONE)
        return bool(force_email), bool(force_phone)

    async def refresh_session(
        self, token: str, account_type: AccountType
    ) -> LoginResponse:
        """刷新当前会话（滑动 TTL）并返回最新登录结果，会话失效时抛错。"""
        session = await session_store.get(token)
        if session is None:
            raise AuthenticationError("Session expired or invalid")
        if str(session.account_type) != account_type.value:
            raise BusinessError("账号类型不匹配")
        await session_store.touch(token)
        account = await self.account_repo.get_required(session.account_id)
        force_bind_email, force_bind_phone = await self._force_bind_flags(
            account, account_type
        )
        return LoginResponse(
            token=session.token,
            account_id=session.account_id,
            account_type=account_type,
            password_expired=session.password_expired,
            password_expiry_warning_days=await self.password_expiry_warning_days(
                session.account_id
            ),
            force_bind_email=force_bind_email,
            force_bind_phone=force_bind_phone,
        )

    async def register_portal(self, payload: RegisterRequest) -> RegisterResponse:
        """执行门户注册（ACCOUNT/EMAIL/PHONE 通道）：创建账户、资料、默认角色/部门。"""
        policy = get_register_policy(AccountType.PORTAL)
        if not policy.enabled:
            raise BusinessError("Portal registration is disabled")
        channel = (payload.register_channel or "ACCOUNT").strip().upper()
        email: str | None = None
        phone: str | None = None
        account_name: str | None = None
        if channel == "ACCOUNT":
            if not config_reader.get_bool("AUTH_REGISTER_PORTAL_ALLOW_ACCOUNT", True):
                raise BusinessError("用户名注册已关闭")
            account_name = (payload.account or "").strip()
            if not account_name:
                raise BusinessError("用户名不能为空")
            if await self.account_repo.get_account_by_identifier(
                account_name, [AccountIdentityType.ACCOUNT]
            ) is not None:
                raise BusinessError("账号已存在")
            # 策略要求联系方式时，ACCOUNT 通道需在载荷中补齐（缺失则拒绝）。
            email = (payload.email or "").strip().lower() or None
            phone = (payload.phone or "").strip() or None
            if policy.require_email and not email:
                raise BusinessError("Email is required for registration")
            if policy.require_phone and not phone:
                raise BusinessError("Phone is required for registration")
        elif channel == "EMAIL":
            if not config_reader.get_bool("AUTH_REGISTER_PORTAL_ALLOW_EMAIL", True):
                raise BusinessError("邮箱注册已关闭")
            email = (payload.email or "").strip().lower() or None
            if not email or "@" not in email:
                raise BusinessError("邮箱格式不正确")
            await self.consume_register_code(channel="EMAIL", target=email, code=payload.otp_code)
            if await self.account_repo.get_account_by_identifier(
                email, [AccountIdentityType.EMAIL]
            ) is not None:
                raise BusinessError("邮箱已被使用")
            account_name = await self._allocate_account_from_contact(email.split("@", 1)[0])
        elif channel == "PHONE":
            if not config_reader.get_bool("AUTH_REGISTER_PORTAL_ALLOW_PHONE", False):
                raise BusinessError("手机注册已关闭")
            phone = (payload.phone or "").strip() or None
            if not phone:
                raise BusinessError("手机号不能为空")
            await self.consume_register_code(channel="PHONE", target=phone, code=payload.otp_code)
            if await self.account_repo.get_account_by_identifier(
                phone, [AccountIdentityType.PHONE]
            ) is not None:
                raise BusinessError("手机号已被使用")
            account_name = await self._allocate_account_from_contact(f"user{phone[-6:]}")
        else:
            raise BusinessError("不支持的注册通道")
        assert account_name
        nickname = (payload.nickname or "").strip() or f"user-{uuid4().hex[:8]}"
        async with transactional(self.db):
            account_payload = AccountCreateRequest(
                account=account_name,
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
                account_name=account_name,
                email=email,
                phone=phone,
            )
            await ProfileUserPortalRepository(self.db).upsert(
                ProfileUserPortalUpsertPayload(
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
                    {"app_name": settings.app.name, "account": account_name},
                )
            except BusinessError:
                pass
        response = RegisterResponse(
            account_id=account.id,
            account=account_name,
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

    async def _allocate_account_from_contact(self, base: str) -> str:
        """由邮箱/手机号派生唯一账号名（保留字母数字，注入熵降低碰撞）。"""
        sanitized = "".join(ch for ch in base if ch.isalnum()).lower()[:16]
        candidate = sanitized or f"user{uuid4().hex[:6]}"
        if await self.account_repo.get_account_by_identifier(
            candidate, [AccountIdentityType.ACCOUNT]
        ) is None:
            return candidate
        # 极低概率碰撞：追加短熵后直接返回（一次查询收尾，避免逐序号循环）。
        return f"{candidate[:12]}{uuid4().hex[:6]}"

    async def _assign_register_defaults(self, account_id: str, account_type: AccountType) -> None:
        """为注册账户分配策略中配置的默认角色与部门。"""
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
        """处理忘记密码：校验账户后生成重置链接并发送邮件。"""
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
        """校验重置 token 并更新账户密码，随后清理会话。"""
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
        """校验账号状态、注销标记与目标账户类型是否允许访问。"""
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
        """获取 Redis 客户端，未初始化时抛出统一业务错误。"""
        redis = get_redis()
        if redis is None:
            raise BusinessError(message)
        return redis

    def _build_password_reset_link(self, account_type: AccountType, token: str) -> str:
        """根据账户类型读取配置的模板地址并拼接 token 生成重置链接。"""
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
        """记录密码重置请求的审计日志。"""
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
