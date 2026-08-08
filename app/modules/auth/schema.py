""" Author: Charlie """

from typing import Annotated, Literal

from pydantic import BeforeValidator, Field

from app.core.config.enums import AccountType
from app.core.response.schema import ApiResponse
from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireBool
from app.core.security.transport import CaptchaMixin, PasswordKeyMixin
from app.modules.iam.enums import AccountIdentityType


def _empty_as_none(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value


OptionalStr = Annotated[str | None, BeforeValidator(_empty_as_none)]


class CaptchaFormatQuery(ApiSchema):
    image_format: str = Field(default="svg", alias="format", pattern="^(svg|png)$")


class LoginRequest(CaptchaMixin):
    account: str = Field(min_length=3, max_length=128)
    password: OptionalStr = Field(default=None, min_length=1, max_length=512)
    password_key_id: OptionalStr = Field(default=None, max_length=64)
    identity_type: AccountIdentityType = AccountIdentityType.ACCOUNT
    login_mode: Literal["PASSWORD", "OTP"] = "PASSWORD"
    otp_code: OptionalStr = Field(default=None, min_length=4, max_length=16)
    remember_me: WireBool = True


class LoginPayload(ApiSchema):
    """登录服务载荷，包含目标账户类型。"""

    account: str
    password: str | None = None
    account_type: AccountType
    identity_type: AccountIdentityType = AccountIdentityType.ACCOUNT
    login_mode: str = "PASSWORD"
    otp_code: str | None = None
    remember_me: WireBool = True
    client_ip: str | None = None
    user_agent: str | None = None
    device_label: str | None = None


class LoginResponse(ApiSchema):
    token: str | None = None
    account_id: str | None = None
    account_type: AccountType | None = None
    password_expired: WireBool = False
    password_expiry_warning_days: int | None = None


class SendLoginCodeRequest(CaptchaMixin):
    target: str = Field(min_length=3, max_length=128)
    channel: Literal["EMAIL", "PHONE"]


class AuthOptionsResponse(ApiSchema):
    account_type: AccountType
    allow_account: WireBool = True
    allow_email: WireBool = True
    allow_phone: WireBool = True
    allow_otp: WireBool = True
    register_enabled: WireBool = False
    register_require_phone: WireBool = False
    register_require_email: WireBool = False
    password_change_verify_method: str = "OLD_PASSWORD"
    copyright_text: str = ""
    copyright_url: str = ""


class RegisterRequest(CaptchaMixin, PasswordKeyMixin):
    account: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=512)
    name: str | None = Field(default=None, max_length=64)
    nickname: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)


class ForgotPasswordRequest(CaptchaMixin):
    email: str = Field(min_length=3, max_length=128)


class ResetPasswordRequest(CaptchaMixin, PasswordKeyMixin):
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
AuthOptionsApiResponse = ApiResponse[AuthOptionsResponse]
