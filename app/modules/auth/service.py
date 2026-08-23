""" Author: Charlie

认证应用服务门面：按登录、注册、绑定、重置、生命周期拆分 mixin，对外仍暴露 AuthService。
"""

from app.modules.auth.base import AuthServiceBase
from app.modules.auth.base import _audit_record as _audit_record
from app.modules.auth.base import session_expires_in as session_expires_in
from app.modules.auth.bind_service import BindCodeMixin
from app.modules.auth.lifecycle_service import LifecycleMixin
from app.modules.auth.login_service import LoginMixin
from app.modules.auth.password_reset_service import PasswordResetMixin
from app.modules.auth.register_service import RegisterMixin


class AuthService(
    LoginMixin,
    RegisterMixin,
    BindCodeMixin,
    PasswordResetMixin,
    LifecycleMixin,
    AuthServiceBase,
):
    """认证服务门面，保持既有调用方 `AuthService(db)` 不变。"""


__all__ = ["AuthService", "session_expires_in", "_audit_record"]
