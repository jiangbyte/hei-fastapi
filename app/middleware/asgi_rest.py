""" Author: Charlie

标准 SecurityHeaders / AuthWhitelist / RateLimit / OperationAudit 中间件（纯 ASGI）。
"""
from __future__ import annotations

import logging
import re
import time
import uuid

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.exceptions.business import AuthenticationError
from app.core.network.client_ip import get_client_ip
from app.core.response.errors import asgi_error_response
from app.core.security.auth_whitelist import is_auth_whitelisted
from app.core.security.session_auth import get_request_session, resolve_request_session
from app.core.security.session_token import extract_session_token
from app.deps.context import account_id_ctx, account_type_ctx, client_ip_ctx
from app.platform.audit.queue import OperationAuditEvent, operation_audit_queue
from app.platform.cache.redis import get_redis
from app.platform.module.router import API_ROOT_PREFIX

logger = logging.getLogger(__name__)

RATE_LIMIT_RULES: list[tuple[re.Pattern[str], int, int, str]] = [
    (re.compile(r"^/api/v\d+/(admin|portal)/login"), 10, 60, "ip"),
    (re.compile(r"^/api/v\d+/portal/register"), 5, 60, "ip"),
    (re.compile(r"^/api/v\d+/(admin|portal)/(forgot-password|reset-password)"), 5, 60, "ip"),
    (re.compile(r"^/api/v\d+/(admin|portal)/captcha"), 30, 60, "ip"),
    (re.compile(r"^/api/v\d+/"), 120, 60, "mix"),
]

RATE_LIMIT_EXEMPT: list[re.Pattern[str]] = [
    re.compile(r"^/api/v\d+/internal/health"),
    re.compile(r"^/(docs|redoc|openapi\.json)"),
]

AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
AUDIT_PATH_RE = re.compile(
    r"^/api/v\d+/(?P<account_type>admin|portal)/"
    r"(?P<module_path>[a-z][a-z0-9/_-]*)"
    r"(?P<action>/[^?]*)?"
)
SKIP_AUDIT_PATH_PATTERNS = (
    "/captcha",
    "/password-key",
    "/login",
    "/login/mfa",
    "/register",
    "/forgot-password",
    "/reset-password",
    "/cancel",
    "/me",
)

SECURITY_HEADERS = {
    b"strict-transport-security": b"max-age=31536000; includeSubDomains",
    b"x-content-type-options": b"nosniff",
    b"x-frame-options": b"DENY",
    b"content-security-policy": (
        b"default-src 'self'; "
        b"script-src 'self'; "
        b"style-src 'self' 'unsafe-inline'; "
        b"object-src 'none'; "
        b"img-src 'self' data: blob:; "
        b"font-src 'self' data:; "
        b"connect-src 'self'; "
        b"frame-ancestors 'none'"
    ),
    b"referrer-policy": b"strict-origin-when-cross-origin",
    b"permissions-policy": (b"camera=(), microphone=(), geolocation=(), interest-cohort=()"),
}


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers") or [])
                existing = {name.lower() for name, _ in headers}
                for name, value in SECURITY_HEADERS.items():
                    if name not in existing:
                        headers.append((name, value))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)


class AuthWhitelistMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method") or ""
        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or ""
        if not path.startswith(API_ROOT_PREFIX):
            await self.app(scope, receive, send)
            return

        if is_auth_whitelisted(path):
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        try:
            await resolve_request_session(request, required=True)
        except AuthenticationError as exc:
            await asgi_error_response(scope, receive, send, status_code=401, message=str(exc))
            return
        await self.app(scope, receive, send)


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method") or ""
        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or ""
        for exempt in RATE_LIMIT_EXEMPT:
            if exempt.search(path):
                await self.app(scope, receive, send)
                return

        redis = get_redis()
        if redis is None:
            sensitive = any(
                keyword in path
                for keyword in ("/login", "/register", "forgot-password", "reset-password")
            )
            if sensitive:
                await asgi_error_response(
                    scope, receive, send, status_code=503, message="限流服务暂不可用"
                )
                return
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        for pattern, limit, window_sec, scope_name in RATE_LIMIT_RULES:
            if not pattern.search(path):
                continue
            key = await self._build_key(request, pattern.pattern, scope_name)
            if key is None:
                break
            try:
                count = await self._increment_and_check(redis, key, limit, window_sec)
                if count > limit:
                    logger.warning(
                        "Rate limit exceeded: %s (count=%d, limit=%d)", key, count, limit
                    )
                    await asgi_error_response(
                        scope,
                        receive,
                        send,
                        status_code=429,
                        message="请求过于频繁，请稍后再试",
                        headers={"Retry-After": str(window_sec)},
                    )
                    return
            except Exception:
                logger.debug("Rate limit check failed for %s", key, exc_info=True)
            break

        await self.app(scope, receive, send)

    async def _build_key(self, request: Request, pattern: str, scope: str) -> str | None:
        ip = client_ip_ctx.get() or get_client_ip(request) or "unknown"
        if scope == "ip":
            return f"rl:ip:{ip}:{pattern}"

        uid = account_id_ctx.get() or await self._resolve_account_id(request)
        if scope == "user":
            if not uid:
                return None
            return f"rl:user:{uid}:{pattern}"

        if uid:
            return f"rl:user:{uid}:{pattern}"
        return f"rl:ip:{ip}:{pattern}"

    async def _resolve_account_id(self, request: Request) -> str | None:
        cached = get_request_session(request)
        if cached is not None:
            return cached.account_id
        token = extract_session_token(request)
        if not token:
            return None
        try:
            session = await resolve_request_session(
                request, required=False, touch=False, bind_context=False
            )
            return session.account_id if session else None
        except Exception:
            logger.debug("Rate limit session resolve failed", exc_info=True)
            return None

    async def _increment_and_check(self, redis, key: str, limit: int, window_sec: int) -> int:
        now = time.time()
        window_start = now - window_sec
        member = f"{now:.6f}:{uuid.uuid4().hex[:8]}"
        pipe = redis.pipeline()
        pipe.zadd(key, {member: now})
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.expire(key, window_sec)
        results = await pipe.execute()
        return int(results[2])


class OperationAuditMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        status_code = 500
        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                status_code = int(message.get("status") or 500)
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            try:
                request = Request(scope, receive)
                audit_info = _match_audit_target(request)
                if audit_info is not None:
                    resource_type, action = audit_info
                    from app.deps.context import (
                        request_id_ctx,
                        user_agent_ctx,
                    )

                    operation_audit_queue.enqueue(
                        OperationAuditEvent(
                            resource_type=resource_type,
                            action=action,
                            method=request.method,
                            path=request.url.path,
                            status_code=status_code if response_started else 500,
                            account_id=account_id_ctx.get(),
                            account_type=account_type_ctx.get(),
                            request_id=request_id_ctx.get(),
                            ip=client_ip_ctx.get(),
                            user_agent=user_agent_ctx.get(),
                        )
                    )
            except Exception:
                pass


def _should_skip_path(path: str) -> bool:
    path_lower = path.lower()
    for pattern in SKIP_AUDIT_PATH_PATTERNS:
        if path_lower.endswith(pattern):
            return True
    return False


def _extract_resource_type(module_path: str) -> str:
    parts = module_path.strip("/").split("/")
    resource = parts[-1] if parts else module_path
    resource = re.sub(r"[0-9a-f]{8,}", "", resource).strip("-_")
    return resource if resource else module_path.replace("/", "_")


def _extract_action(action_str: str | None, method: str) -> str:
    if not action_str:
        return method.lower()
    action = action_str.strip("/").split("/", 1)[0]
    return action.replace("-", "_") if action else method.lower()


def _match_audit_target(request: Request) -> tuple[str, str] | None:
    if request.method.upper() not in AUDIT_METHODS:
        return None
    path = request.url.path
    if _should_skip_path(path):
        return None
    match = AUDIT_PATH_RE.match(path)
    if not match:
        if any(seg in path.split("/") for seg in ("logout",)):
            return ("account", "logout")
        return None

    module_path = match.group("module_path")
    action_str = match.group("action")
    resource_type = _extract_resource_type(module_path)
    action = _extract_action(action_str, request.method)
    return resource_type, action
