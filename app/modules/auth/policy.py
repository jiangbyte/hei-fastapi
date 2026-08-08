""" Author: Charlie

按 AccountType 读取登录/注册策略（sys_config UPPER_SNAKE）。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config.enums import AccountType, account_config_key
from app.core.config.settings import settings
from app.core.exceptions.business import AuthenticationError, BusinessError
from app.modules.iam.enums import AccountIdentityType
from app.platform.config.reader import config_reader


@dataclass(frozen=True, slots=True)
class LoginTypePolicy:
    allow_phone: bool
    phone_no_user_policy: str
    allow_email: bool
    email_no_user_policy: str
    allow_otp: bool
    failure_window_seconds: int
    max_failures: int
    lock_seconds: int


@dataclass(frozen=True, slots=True)
class RegisterTypePolicy:
    enabled: bool
    require_phone: bool
    require_email: bool
    default_role_id: str
    default_dept_id: str


@dataclass(frozen=True, slots=True)
class AuthOptions:
    account_type: AccountType
    allow_account: bool
    allow_email: bool
    allow_phone: bool
    allow_otp: bool
    register_enabled: bool
    register_require_phone: bool
    register_require_email: bool
    password_change_verify_method: str
    copyright_text: str
    copyright_url: str


def get_login_policy(account_type: AccountType) -> LoginTypePolicy:
    prefix = "AUTH_LOGIN"
    shared_window = settings.auth.login_failure_window_seconds
    shared_max = settings.auth.login_account_max_failures
    shared_lock = settings.auth.login_lock_seconds
    return LoginTypePolicy(
        allow_phone=config_reader.get_bool(
            account_config_key(prefix, account_type, "ALLOW_PHONE"), True
        ),
        phone_no_user_policy=(
            config_reader.get(account_config_key(prefix, account_type, "PHONE_NO_USER_POLICY"))
            or "DENY"
        ).strip().upper(),
        allow_email=config_reader.get_bool(
            account_config_key(prefix, account_type, "ALLOW_EMAIL"), True
        ),
        email_no_user_policy=(
            config_reader.get(account_config_key(prefix, account_type, "EMAIL_NO_USER_POLICY"))
            or "DENY"
        ).strip().upper(),
        allow_otp=config_reader.get_bool(
            account_config_key(prefix, account_type, "ALLOW_OTP"), True
        ),
        failure_window_seconds=config_reader.get_int(
            account_config_key(prefix, account_type, "FAILURE_WINDOW_SECONDS"),
            shared_window,
        ),
        max_failures=config_reader.get_int(
            account_config_key(prefix, account_type, "MAX_FAILURES"),
            shared_max,
        ),
        lock_seconds=config_reader.get_int(
            account_config_key(prefix, account_type, "LOCK_SECONDS"),
            shared_lock,
        ),
    )


def get_register_policy(account_type: AccountType) -> RegisterTypePolicy:
    prefix = "AUTH_REGISTER"
    default_enabled = (
        settings.auth.portal_register_enabled
        if account_type == AccountType.PORTAL
        else False
    )
    return RegisterTypePolicy(
        enabled=config_reader.get_bool(
            account_config_key(prefix, account_type, "ENABLED"),
            default_enabled,
        ),
        require_phone=config_reader.get_bool(
            account_config_key(prefix, account_type, "REQUIRE_PHONE"), False
        ),
        require_email=config_reader.get_bool(
            account_config_key(prefix, account_type, "REQUIRE_EMAIL"),
            account_type == AccountType.PORTAL,
        ),
        default_role_id=(
            config_reader.get(account_config_key(prefix, account_type, "DEFAULT_ROLE_ID")) or ""
        ).strip(),
        default_dept_id=(
            config_reader.get(account_config_key(prefix, account_type, "DEFAULT_DEPT_ID")) or ""
        ).strip(),
    )


def get_auth_options(account_type: AccountType) -> AuthOptions:
    login = get_login_policy(account_type)
    register = get_register_policy(account_type)
    return AuthOptions(
        account_type=account_type,
        allow_account=True,
        allow_email=login.allow_email,
        allow_phone=login.allow_phone,
        allow_otp=login.allow_otp,
        register_enabled=register.enabled,
        register_require_phone=register.require_phone,
        register_require_email=register.require_email,
        password_change_verify_method=(
            config_reader.get("PASSWORD_CHANGE_VERIFY_METHOD") or "OLD_PASSWORD"
        ).strip().upper(),
        copyright_text=(config_reader.get("COPYRIGHT_TEXT") or "").strip(),
        copyright_url=(config_reader.get("COPYRIGHT_URL") or "").strip(),
    )


def ensure_identity_allowed(
    account_type: AccountType,
    identity_type: AccountIdentityType,
    *,
    login_mode: str = "PASSWORD",
) -> LoginTypePolicy:
    policy = get_login_policy(account_type)
    mode = (login_mode or "PASSWORD").strip().upper()
    if mode == "OTP" and not policy.allow_otp:
        raise BusinessError("OTP login is disabled")
    if identity_type == AccountIdentityType.EMAIL and not policy.allow_email:
        raise BusinessError("Email login is disabled")
    if identity_type == AccountIdentityType.PHONE and not policy.allow_phone:
        raise BusinessError("Phone login is disabled")
    if identity_type == AccountIdentityType.ACCOUNT and mode == "OTP":
        raise BusinessError("OTP login requires email or phone")
    return policy


def no_user_policy_for(
    policy: LoginTypePolicy,
    identity_type: AccountIdentityType,
) -> str:
    if identity_type == AccountIdentityType.EMAIL:
        return policy.email_no_user_policy
    if identity_type == AccountIdentityType.PHONE:
        return policy.phone_no_user_policy
    return "DENY"


def deny_if_locked_message() -> AuthenticationError:
    return AuthenticationError("Account is temporarily locked")
