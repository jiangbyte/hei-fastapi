import json
from uuid import uuid4
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountStatusEnum, AccountType
from app.core.config.settings import settings
from app.core.exceptions.business import AuthenticationError, BusinessError
from app.core.security.password import hash_password, verify_password
from app.core.security.session import SessionPayload, session_store
from app.core.security.token import generate_token
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
from app.modules.iam.account.repository import AccountRepository
from app.modules.iam.account.password_helper import (
    is_password_expired,
    validate_and_record_password,
)
from app.modules.iam.account.schema import AccountCancelPayload, AccountCreateRequest
from app.modules.iam.enums import AccountIdentityType
from app.platform.config.reader import config_reader
from app.modules.sys.audit.service import OperationAuditService
from app.modules.user.portal.repository import PortalUserProfileRepository
from app.modules.user.portal.schema import PortalProfileUpsertPayload
from app.platform.cache.keys import password_reset_token_key
from app.platform.cache.redis import get_redis
from app.platform.db.transaction import transactional
from app.platform.email.sender import send_mail
from app.platform.observability.metrics import record_login_attempt


class AuthService:
    """认证服务，负责登录态签发、账户类型校验与会话数据组装。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.session_service = AccountSessionService(db)

    async def login(self, payload: LoginPayload) -> SessionPayload:
        """执行登录流程，使用对象承载参数以避免接口层平铺传参。"""
        try:
            await login_protection_service.ensure_allowed(
                account_type=payload.account_type,
                account=payload.account,
                client_ip=payload.client_ip,
            )
            account = await self.account_repo.get_account_by_identifier(
                payload.account,
                [payload.identity_type],
            )
            self._validate_account(account, payload.password, payload.account_type)
        except AuthenticationError:
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

        # 密码过期标记（不影响登录，仅用于前端提示）
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

        # 根据 remember_me 选择合适 TTL
        ttl = (
            settings.auth.token_ttl_seconds
            if payload.remember_me
            else settings.auth.token_ttl_short_seconds
        )
        await session_store.set(session_payload, ttl_seconds=ttl)

        # 清理超出并发限制的旧会话
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
        nickname = (payload.nickname or "").strip() or f"user-{uuid4().hex[:8]}"
        async with transactional(self.db):
            account_payload = AccountCreateRequest(
                account=payload.account,
                password=payload.password,
                account_type=AccountType.PORTAL,
                account_status=AccountStatusEnum.ENABLED,
                name=payload.name,
                nickname=nickname,
                email=payload.email,
                email_login_enabled=True,
                email_identity_verified=bool(payload.email),
            )
            account = await self.account_repo.create(
                account_payload,
                password_hash=hash_password(payload.password),
            )

            # 记录密码历史
            await validate_and_record_password(
                self.db,
                account.id,
                payload.password,
                changed_by=account.id,
                change_reason="register",
            )

            await PortalUserProfileRepository(self.db).upsert(
                PortalProfileUpsertPayload(
                    account_id=account.id,
                    name=payload.name,
                    nickname=nickname,
                    phone=None,
                    email=payload.email,
                    avatar=None,
                    signature=None,
                    bio=None,
                    level=None,
                ),
            )
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
        redis = self._required_redis()
        await redis.setex(
            password_reset_token_key(reset_token),
            settings.auth.password_reset_token_ttl_seconds,
            json.dumps(
                {
                    "account_id": account.id,
                    "email": email,
                    "token_hash": hash_password(reset_token),
                }
            ),
        )
        reset_link = self._build_password_reset_link(account_type, email, reset_token)
        expire_minutes = settings.auth.password_reset_token_ttl_seconds // 60
        tmpl_subject = config_reader.get("mail.template.forgot_password.subject") or "{{app_name}} 密码重置"
        tmpl_body = config_reader.get("mail.template.forgot_password.body") or (
            "请点击以下链接重置密码，"
            "该链接将在 {{expire_minutes}} 分钟内有效。\n\n{{reset_link}}"
        )
        subject = (
            tmpl_subject.replace("{{app_name}}", settings.app.name)
            .replace("{{reset_link}}", reset_link)
            .replace("{{email}}", email)
            .replace("{{expire_minutes}}", str(expire_minutes))
        )
        body = (
            tmpl_body.replace("{{app_name}}", settings.app.name)
            .replace("{{reset_link}}", reset_link)
            .replace("{{email}}", email)
            .replace("{{expire_minutes}}", str(expire_minutes))
        )
        await send_mail(email, subject, body)
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
        redis = self._required_redis()
        raw = await redis.get(key)
        raw_text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if not raw_text:
            raise AuthenticationError("Invalid or expired reset link")
        data = json.loads(raw_text)
        email = payload.email.strip().lower()
        if email != data.get("email") or not verify_password(payload.token, data["token_hash"]):
            raise AuthenticationError("Invalid or expired reset link")

        account = await self.account_repo.get_required(str(data["account_id"]))
        self._validate_account_status(account, account_type)
        async with transactional(self.db):
            # 校验密码强度 + 复用检查
            await validate_and_record_password(
                self.db,
                account.id,
                payload.password,
                changed_by=account.id,
                change_reason="self_reset",
            )
            await self.account_repo.update_password_hash(account.id, hash_password(payload.password))
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
        account: SysAccount,
        account_type: AccountType,
    ) -> None:
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

    def _required_redis(self):
        redis = get_redis()
        if redis is None:
            raise BusinessError("Redis is required for password reset")
        return redis

    def _build_password_reset_link(
        self,
        account_type: AccountType,
        email: str,
        token: str,
    ) -> str:
        base_url = settings.mail.password_reset_url
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
