""" Author: Charlie """

from typing import Any

from pydantic import Field

from app.core.config.enums import AccountType
from app.core.response.schema import ApiResponse
from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireBool, WireInt
from app.core.security.transport import CaptchaMixin, PasswordKeyMixin
from app.modules.iam.enums import AccountIdentityType


class CaptchaFormatQuery(ApiSchema):
    image_format: str = Field(default="svg", alias="format", pattern="^(svg|png)$")


class LoginRequest(CaptchaMixin, PasswordKeyMixin):
    account: str = Field(min_length=3, max_length=128)
    password: str = Field(min_length=1, max_length=512)
    identity_type: AccountIdentityType = AccountIdentityType.ACCOUNT
    remember_me: WireBool = True


class LoginPayload(ApiSchema):
    """登录服务载荷，包含目标账户类型。"""

    account: str
    password: str
    account_type: AccountType
    identity_type: AccountIdentityType = AccountIdentityType.ACCOUNT
    remember_me: WireBool = True
    client_ip: str | None = None
    user_agent: str | None = None
    device_label: str | None = None


class LoginResponse(ApiSchema):
    token: str | None = None
    account_id: str | None = None
    account_type: AccountType | None = None
    password_expired: WireBool = False
    mfa_required: WireBool = False
    challenge_id: str | None = None
    webauthn_options: dict[str, Any] | None = None


class MfaLoginRequest(ApiSchema):
    challenge_id: str = Field(min_length=16, max_length=64)
    code: str | None = Field(default=None, min_length=4, max_length=32)
    webauthn_credential: dict[str, Any] | None = None


class MfaSetupResponse(ApiSchema):
    secret: str
    otpauth_uri: str


class MfaConfirmRequest(ApiSchema):
    code: str = Field(min_length=6, max_length=8)


class MfaConfirmResponse(ApiSchema):
    backup_codes: list[str]


class MfaDisableRequest(PasswordKeyMixin):
    password: str = Field(min_length=1, max_length=512)
    # 启用 TOTP 时必填；仅 WebAuthn 账户可选（密码即可）。
    code: str | None = Field(default=None, min_length=4, max_length=32)


class MfaStatusResponse(ApiSchema):
    enabled: WireBool
    totp_enabled: WireBool = False
    required: WireBool
    enabled_at: str | None = None
    webauthn_count: WireInt = 0


class WebAuthnRegisterVerifyRequest(ApiSchema):
    credential: dict[str, Any]


class RegisterRequest(CaptchaMixin, PasswordKeyMixin):
    account: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=512)
    name: str | None = Field(default=None, max_length=64)
    nickname: str | None = Field(default=None, max_length=64)
    email: str = Field(min_length=3, max_length=128)


class ForgotPasswordRequest(CaptchaMixin):
    email: str = Field(min_length=3, max_length=128)


class ResetPasswordRequest(CaptchaMixin, PasswordKeyMixin):
    email: str = Field(min_length=3, max_length=128)
    token: str = Field(min_length=16, max_length=256)
    password: str = Field(min_length=1, max_length=512)


class RegisterResponse(ApiSchema):
    account_id: str
    account: str
    account_type: AccountType


class LogoutResponse(ApiSchema):
    success: WireBool = True


class CancelAccountRequest(ApiSchema):
    cancel_reason: str | None = Field(default=None, max_length=500)


class CancelAccountResponse(ApiSchema):
    success: WireBool = True


LoginApiResponse = ApiResponse[LoginResponse]
RegisterApiResponse = ApiResponse[RegisterResponse]
LogoutApiResponse = ApiResponse[LogoutResponse]
CancelAccountApiResponse = ApiResponse[CancelAccountResponse]
MfaSetupApiResponse = ApiResponse[MfaSetupResponse]
MfaConfirmApiResponse = ApiResponse[MfaConfirmResponse]
MfaStatusApiResponse = ApiResponse[MfaStatusResponse]
