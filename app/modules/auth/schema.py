from pydantic import Field

from app.core.config.enums import AccountType
from app.core.response.schema import ApiResponse
from app.core.schema.base import ApiSchema
from app.core.security.transport import CaptchaMixin, PasswordKeyMixin
from app.modules.iam.enums import AccountIdentityType


class CaptchaFormatQuery(ApiSchema):
    image_format: str = Field(default="svg", alias="format", pattern="^(svg|png)$")


class LoginRequest(CaptchaMixin, PasswordKeyMixin):
    account: str = Field(min_length=3, max_length=128)
    password: str = Field(min_length=1, max_length=512)
    identity_type: AccountIdentityType = AccountIdentityType.ACCOUNT
    remember_me: bool = True


class LoginPayload(ApiSchema):
    """登录服务载荷，包含目标账户类型。"""

    account: str
    password: str
    account_type: AccountType
    identity_type: AccountIdentityType = AccountIdentityType.ACCOUNT
    remember_me: bool = True
    client_ip: str | None = None
    user_agent: str | None = None
    device_label: str | None = None


class LoginResponse(ApiSchema):
    token: str
    account_id: str
    account_type: AccountType
    password_expired: bool = False


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
    success: bool = True


class CancelAccountRequest(ApiSchema):
    cancel_reason: str | None = Field(default=None, max_length=500)


class CancelAccountResponse(ApiSchema):
    success: bool = True


LoginApiResponse = ApiResponse[LoginResponse]
RegisterApiResponse = ApiResponse[RegisterResponse]
LogoutApiResponse = ApiResponse[LogoutResponse]
CancelAccountApiResponse = ApiResponse[CancelAccountResponse]
