""" Author: Charlie """

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.config.settings import settings
from app.core.exceptions.business import BusinessError
from app.core.network.client_ip import get_client_ip
from app.core.response.schema import ApiResponse, success
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
from app.modules.auth.schema import (
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
    MfaConfirmApiResponse,
    MfaConfirmRequest,
    MfaDisableRequest,
    MfaLoginRequest,
    MfaSetupApiResponse,
    MfaStatusApiResponse,
    RegisterApiResponse,
    RegisterRequest,
    ResetPasswordRequest,
    WebAuthnRegisterVerifyRequest,
)
from app.modules.auth.service import AuthService

admin_router = APIRouter()
portal_router = APIRouter()


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


@admin_router.post("/v1/admin/login", response_model=LoginApiResponse)
async def admin_login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> LoginApiResponse:
    """管理端登录入口，仅允许管理端用户体系访问。"""
    await verify_captcha(payload.captcha_id, payload.captcha_value)
    password = await decrypt_password(payload.password_key_id, payload.password)
    outcome = await AuthService(db).login(
        LoginPayload(
            account=payload.account,
            password=password or "",
            account_type=AccountType.ADMIN,
            identity_type=payload.identity_type,
            remember_me=payload.remember_me,
            client_ip=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            device_label=_device_label(request.headers.get("user-agent")),
        )
    )
    if outcome.mfa_required:
        return success(
            LoginResponse(
                mfa_required=True,
                challenge_id=outcome.challenge_id,
                webauthn_options=outcome.webauthn_options,
            )
        )
    assert outcome.session is not None
    session = outcome.session
    set_session_cookie(response, session.token, remember_me=payload.remember_me)
    return success(
        LoginResponse(
            token=session.token,
            account_id=session.account_id,
            account_type=AccountType(str(session.account_type)),
            password_expired=session.password_expired,
        )
    )


@admin_router.post("/v1/admin/login/mfa", response_model=LoginApiResponse)
async def admin_login_mfa(
    payload: MfaLoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> LoginApiResponse:
    session = await AuthService(db).complete_mfa_login(
        payload,
        client_ip=get_client_ip(request),
    )
    set_session_cookie(response, session.token, remember_me=session.remember_me)
    return success(
        LoginResponse(
            token=session.token,
            account_id=session.account_id,
            account_type=AccountType(str(session.account_type)),
            password_expired=session.password_expired,
        )
    )


@admin_router.get(
    "/v1/admin/auth/mfa/status",
    response_model=MfaStatusApiResponse,
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
)
async def admin_mfa_status(
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MfaStatusApiResponse:
    return success(await AuthService(db).mfa_status(session))


@admin_router.post(
    "/v1/admin/auth/mfa/setup",
    response_model=MfaSetupApiResponse,
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
)
async def admin_mfa_setup(
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MfaSetupApiResponse:
    return success(await AuthService(db).mfa_setup(session))


@admin_router.post(
    "/v1/admin/auth/mfa/confirm",
    response_model=MfaConfirmApiResponse,
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
)
async def admin_mfa_confirm(
    payload: MfaConfirmRequest,
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MfaConfirmApiResponse:
    return success(await AuthService(db).mfa_confirm(session, payload))


@admin_router.post(
    "/v1/admin/auth/mfa/disable",
    response_model=ApiResponse[None],
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
)
async def admin_mfa_disable(
    payload: MfaDisableRequest,
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    password = await decrypt_password(payload.password_key_id, payload.password)
    await AuthService(db).mfa_disable(
        session,
        payload.model_copy(update={"password": password or ""}),
    )
    return success()


@admin_router.post(
    "/v1/admin/auth/mfa/webauthn/register/options",
    response_model=ApiResponse[dict[str, Any]],
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
)
async def admin_webauthn_register_options(
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, Any]]:
    return success(await AuthService(db).webauthn_register_options(session))


@admin_router.post(
    "/v1/admin/auth/mfa/webauthn/register/verify",
    response_model=ApiResponse[None],
    dependencies=[Depends(require_account_type(AccountType.ADMIN))],
)
async def admin_webauthn_register_verify(
    payload: WebAuthnRegisterVerifyRequest,
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[None]:
    await AuthService(db).webauthn_register_verify(session, payload.credential)
    return success()


@portal_router.post("/v1/portal/login", response_model=LoginApiResponse)
async def portal_login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> LoginApiResponse:
    """门户端登录入口，仅允许门户用户体系访问。"""
    await verify_captcha(payload.captcha_id, payload.captcha_value)
    password = await decrypt_password(payload.password_key_id, payload.password)
    outcome = await AuthService(db).login(
        LoginPayload(
            account=payload.account,
            password=password or "",
            account_type=AccountType.PORTAL,
            identity_type=payload.identity_type,
            remember_me=payload.remember_me,
            client_ip=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            device_label=_device_label(request.headers.get("user-agent")),
        )
    )
    assert outcome.session is not None
    session = outcome.session
    set_session_cookie(response, session.token, remember_me=payload.remember_me)
    return success(
        LoginResponse(
            token=session.token,
            account_id=session.account_id,
            account_type=AccountType(str(session.account_type)),
            password_expired=session.password_expired,
        )
    )


@portal_router.post("/v1/portal/register", response_model=RegisterApiResponse)
async def portal_register(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> RegisterApiResponse:
    """门户端注册入口，创建门户账户主体和门户资料。"""
    if not settings.auth.portal_register_enabled:
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
    clear_session_cookie(response)
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
    session: Annotated[SessionPayload, Depends(get_current_session)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CancelAccountApiResponse:
    """统一账号注销接口，只注销当前登录账号。"""
    await AuthService(db).cancel_current_account(payload, session)
    return success(CancelAccountResponse(success=True))
