""" Author: Charlie

从 HttpOnly Cookie（优先）或原始请求头（原生客户端）提取会话 token。
"""
from __future__ import annotations

from fastapi import Response
from starlette.requests import Request

from app.core.config.settings import settings


def _raw_header_token(request: Request) -> str | None:
    """从配置请求头读取不透明会话 token；拒绝 HTTP Bearer 方案。"""
    header_name = (settings.auth.token_name or "Authorization").strip() or "Authorization"
    raw = request.headers.get(header_name)
    if not raw or not raw.strip():
        return None
    token = raw.strip()
    # 旧版/浏览器 ``Authorization: Bearer <jwt>`` 不用于 HEI 会话。
    if token.lower().startswith("bearer "):
        return None
    return token


def extract_session_token(request: Request, authorization: str | None = None) -> str | None:
    """优先会话 Cookie；否则回退到原始 Authorization（或 token_name）头。

    ``authorization`` 参数为调用方兼容保留；Bearer 方案会被忽略。建议仅传 ``request``。
    """
    if settings.auth.session_cookie_enabled:
        cookie = request.cookies.get(settings.auth.session_cookie_name)
        if cookie and cookie.strip():
            return cookie.strip()

    if authorization and authorization.strip():
        token = authorization.strip()
        if not token.lower().startswith("bearer "):
            return token

    return _raw_header_token(request)


def set_session_cookie(
    response: Response,
    token: str,
    *,
    remember_me: bool = True,
) -> None:
    if not settings.auth.session_cookie_enabled:
        return
    max_age = (
        settings.auth.token_ttl_seconds if remember_me else settings.auth.token_ttl_short_seconds
    )
    same_site = settings.auth.session_cookie_samesite.lower()
    if same_site not in {"lax", "strict", "none"}:
        same_site = "lax"
    response.set_cookie(
        key=settings.auth.session_cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.auth.session_cookie_secure or same_site == "none",
        samesite=same_site,  # type: ignore[arg-type]
        path=settings.auth.session_cookie_path,
    )


def clear_session_cookie(response: Response) -> None:
    if not settings.auth.session_cookie_enabled:
        return
    response.delete_cookie(
        key=settings.auth.session_cookie_name,
        path=settings.auth.session_cookie_path,
    )
