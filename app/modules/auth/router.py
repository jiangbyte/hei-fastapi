""" Author: Charlie """

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.exceptions.business import BusinessError
from app.core.network.client_ip import get_client_ip
from app.core.response.schema import success
from app.core.security.session import SessionPayload
from app.core.security.session_token import (
    clear_session_cookie,
    extract_session_token,
    set_session_cookie,
)
from app.core.security.transport import (
    CaptchaApiResponse,
    PasswordKeyApiResponse,
    create_captcha,
    create_password_key,
    decrypt_password,
    verify_captcha,
)
from app.deps.auth import get_current_session, require_account_type
from app.deps.db import get_db_session
from app.modules.auth.policy import get_auth_options, get_register_policy
from app.modules.auth.schema import (
    AuthOptionsApiResponse,
    AuthOptionsResponse,
    CancelAccountApiResponse,
    CancelAccountRequest,
    CancelAccountResponse,
    CaptchaFormatQuery,
    ForgotPasswordRequest,
    LoginApiResponse,
    LoginPayload,
    LoginRequest,
    LoginResponse,
    LogoutApiResponse,
    LogoutResponse,
    RegisterApiResponse,
    RegisterRequest,
    ResetPasswordRequest,
    SendLoginCodeRequest,
)
from app.modules.auth.service import AuthService

admin_router = APIRouter()
portal_router = APIRouter()


@admin_router.get("/v1/admin/public/auth-options", response_model=AuthOptionsApiResponse)
async def admin_auth_options() -> AuthOptionsApiResponse:
    return success(_auth_options_response(AccountType.ADMIN))


@portal_router.get("/v1/portal/public/auth-options", response_model=AuthOptionsApiResponse)
async def portal_auth_options() -> AuthOptionsApiResponse:
    return success(_auth_options_response(AccountType.PORTAL))


def _auth_options_response(account_type: AccountType) -> AuthOptionsResponse:
    opts = get_auth_options(account_type)
    return AuthOptionsResponse(
        account_type=opts.account_type,
        allow_account=opts.allow_account,
        allow_email=opts.allow_email,
        allow_phone=opts.allow_phone,
        allow_otp=opts.allow_otp,
        register_enabled=opts.register_enabled,
        register_require_phone=opts.register_require_phone,
        register_require_email=opts.register_require_email,
        password_change_verify_method=opts.password_change_verify_method,
        copyright_text=opts.copyright_text,
        copyright_url=opts.copyright_url,
    )


@admin_router.get("/v1/admin/captcha", response_model=CaptchaApiResponse)
@portal_router.get("/v1/portal/captcha", response_model=CaptchaApiResponse)
async def captcha(
    query: Annotated[CaptchaFormatQuery, Depends()],
) -> CaptchaApiResponse:
    return success(await create_captcha(query.image_format))


@admin_router.get("/v1/admin/password-key", response_model=PasswordKeyApiResponse)
@portal_router.get("/v1/portal/password-key", response_model=PasswordKeyApiResponse)
async def password_key() -> PasswordKeyApiResponse:
    return success(await create_password_key())


async def _login(
    *,
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession,
    account_type: AccountType,
) -> LoginApiResponse:
    await verify_captcha(payload.captcha_id, payload.captcha_value)
    login_mode = (payload.login_mode or "PASSWORD").strip().upper()
    password: str | None = None
    if login_mode != "OTP":
        if not payload.password or not payload.password_key_id:
            raise BusinessError("Password is required")
        password = await decrypt_password(payload.password_key_id, payload.password)
    service = AuthService(db)
    session = await service.login(
        LoginPayload(
            account=payload.account,
            password=password or "",
            account_type=account_type,
            identity_type=payload.identity_type,
            login_mode=login_mode,
            otp_code=payload.otp_code,
            remember_me=payload.remember_me,
            client_ip=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            device_label=_device_label(request.headers.get("user-agent")),
        )
    )
    set_session_cookie(
        response,
        session.token,
        request=request,
        remember_me=payload.remember_me,
    )
    warning = await service.password_expiry_warning_days(session.account_id)
    return success(
        LoginResponse(
            token=session.token,
            account_id=session.account_id,
            account_type=AccountType(str(session.account_type)),
            password_expired=session.password_expired,
            password_expiry_warning_days=warning,
        )
    )


@admin_router.post("/v1/admin/login", response_model=LoginApiResponse)
async def admin_login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> LoginApiResponse:
    return await _login(
        payload=payload,
        request=request,
        response=response,
        db=db,
        account_type=AccountType.ADMIN,
    )


@portal_router.post("/v1/portal/login", response_model=LoginApiResponse)
async def portal_login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> LoginApiResponse:
    return await _login(
        payload=payload,
        request=request,
        response=response,
        db=db,
        account_type=AccountType.PORTAL,
    )


@admin_router.post("/v1/admin/send-login-code")
@portal_router.post("/v1/portal/send-login-code")
async def send_login_code(
    payload: SendLoginCodeRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    await verify_captcha(payload.captcha_id, payload.captcha_value)
    path = request.url.path
    account_type = AccountType.ADMIN if "/admin/" in path else AccountType.PORTAL
    await AuthService(db).send_login_code(
        account_type=account_type,
        channel=payload.channel,
        target=payload.target,
        client_ip=get_client_ip(request),
    )
    return success()


@portal_router.post("/v1/portal/register", response_model=RegisterApiResponse)
async def portal_register(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> RegisterApiResponse:
    """门户端注册入口，创建门户账户主体和门户资料。"""
    if not get_register_policy(AccountType.PORTAL).enabled:
        raise BusinessError("Portal registration is disabled")
    await verify_captcha(payload.captcha_id, payload.captcha_value)
    password = await decrypt_password(payload.password_key_id, payload.password)
    return success(
        await AuthService(db).register_portal(
            payload.model_copy(update={"password": password or ""})
        )
    )


@admin_router.post("/v1/admin/forgot-password")
async def admin_forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    await verify_captcha(payload.captcha_id, payload.captcha_value)
    await AuthService(db).forgot_password(
        payload,
        AccountType.ADMIN,
        client_ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return success()


@admin_router.post("/v1/admin/reset-password")
async def admin_reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    await verify_captcha(payload.captcha_id, payload.captcha_value)
    password = await decrypt_password(payload.password_key_id, payload.password)
    await AuthService(db).reset_password(
        payload.model_copy(update={"password": password or ""}),
        AccountType.ADMIN,
        client_ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return success()


@portal_router.post("/v1/portal/forgot-password")
async def portal_forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    await verify_captcha(payload.captcha_id, payload.captcha_value)
    await AuthService(db).forgot_password(
        payload,
        AccountType.PORTAL,
        client_ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return success()


@portal_router.post("/v1/portal/reset-password")
async def portal_reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    await verify_captcha(payload.captcha_id, payload.captcha_value)
    password = await decrypt_password(payload.password_key_id, payload.password)
    await AuthService(db).reset_password(
        payload.model_copy(update={"password": password or ""}),
        AccountType.PORTAL,
        client_ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return success()


@portal_router.post(
    "/v1/portal/logout",
    response_model=LogoutApiResponse,
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
)
@admin_router.post(
    "/v1/admin/logout",
    response_model=LogoutApiResponse,
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
)
async def logout(
    request: Request,
    response: Response,
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> LogoutApiResponse:
    """统一退出登录接口，优先读取 cookie / 请求头中的原始 token。"""
    token = extract_session_token(request, authorization) or session.token
    await AuthService(db).logout(token)
    clear_session_cookie(response, request=request)
    return success(LogoutResponse(success=True))


def _device_label(user_agent: str | None) -> str | None:
    if not user_agent:
        return None
    value = user_agent.lower()
    if "mobile" in value or "android" in value or "iphone" in value:
        return "Mobile"
    if "ipad" in value or "tablet" in value:
        return "Tablet"
    return "Desktop"


@portal_router.post(
    "/v1/portal/cancel",
    response_model=CancelAccountApiResponse,
    dependencies=[Depends(require_account_type(AccountType.PORTAL))],
)
@admin_router.post(
    "/v1/admin/cancel",
    response_model=CancelAccountApiResponse,
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
)
async def cancel_account(
    payload: CancelAccountRequest,
    request: Request,
    response: Response,
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CancelAccountApiResponse:
    """统一账号注销接口，只注销当前登录账号。"""
    await AuthService(db).cancel_current_account(payload, session)
    clear_session_cookie(response, request=request)
    return success(CancelAccountResponse(success=True))
