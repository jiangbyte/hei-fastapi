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

from app.core.config.enums import AccountType, account_type_url_segment
from app.core.exceptions.business import AuthenticationError
from app.core.network.client_ip import get_client_ip
from app.core.response.errors import asgi_error_response
from app.core.security.auth_whitelist import is_auth_whitelisted
from app.core.security.session_auth import get_request_session, resolve_request_session
from app.core.security.session_token import extract_session_token
from app.deps.context import account_id_ctx, account_type_ctx, client_ip_ctx
from app.platform.audit.queue import OperationAuditEvent, operation_audit_queue
from app.platform.cache.redis import get_redis
from app.platform.module.paths import API_ROOT_PREFIX

logger = logging.getLogger(__name__)

# 与 permission_registry 一致：路径段随 AccountType 枚举自动扩展
_ACCOUNT_TYPE_PATH_ALTS = "|".join(account_type_url_segment(item) for item in AccountType)

# 限流规则：(路径正则, 次数上限, 时间窗秒, 作用域)。
RATE_LIMIT_RULES: list[tuple[re.Pattern[str], int, int, str]] = [
    (re.compile(rf"^/api/v\d+/({_ACCOUNT_TYPE_PATH_ALTS})/login"), 10, 60, "ip"),
    (re.compile(rf"^/api/v\d+/({_ACCOUNT_TYPE_PATH_ALTS})/register"), 5, 60, "ip"),
    (
        re.compile(
            rf"^/api/v\d+/({_ACCOUNT_TYPE_PATH_ALTS})/(forgot-password|reset-password)"
        ),
        5,
        60,
        "ip",
    ),
    (re.compile(rf"^/api/v\d+/({_ACCOUNT_TYPE_PATH_ALTS})/captcha"), 30, 60, "ip"),
    (re.compile(r"^/api/v\d+/"), 120, 60, "mix"),
]

# 免限流路径。
RATE_LIMIT_EXEMPT: list[re.Pattern[str]] = [
    re.compile(r"^/api/v\d+/internal/health"),
    re.compile(r"^/(docs|redoc|openapi\.json)"),
]

# 需要审计的写操作 HTTP 方法。
AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# 解析审计目标路径的正则：捕获账户类型、模块路径与动作。
AUDIT_PATH_RE = re.compile(
    rf"^/api/v\d+/(?P<account_type>{_ACCOUNT_TYPE_PATH_ALTS})/"
    r"(?P<module_path>[a-z][a-z0-9/_-]*)"
    r"(?P<action>/[^?]*)?"
)
# 审计跳过的路径后缀。
SKIP_AUDIT_PATH_PATTERNS = (
    "/captcha",
    "/password-key",
    "/login",
    "/register",
    "/forgot-password",
    "/reset-password",
    "/cancel",
    "/me",
)

# 注入到响应中的安全头。
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
    """安全响应头中间件：为 HTTP 响应补充缺失的安全头。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """在响应起始消息中补齐缺失的安全头。"""
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
    """认证白名单中间件：白名单外路径强制解析会话，未认证返回 401。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """对白名单外的 API 路径强制要求会话，否则返回 401。"""
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
    """限流中间件：基于 Redis 按规则对敏感端点限流。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """匹配限流规则并在超限时返回 429。"""
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
        """根据限流作用域构造 Redis 键（ip / user / mix）。"""
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
        """从缓存或 token 解析账户 ID（不触碰会话）。"""
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
        """用 ZSET 滑动窗口计数并返回当前计数。"""
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
    """操作审计中间件：对写操作匹配资源/动作并投递审计事件。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """包裹下游应用，请求结束后投递审计事件。"""
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
    """判断路径是否命中审计跳过清单。"""
    path_lower = path.lower()
    for pattern in SKIP_AUDIT_PATH_PATTERNS:
        if path_lower.endswith(pattern):
            return True
    return False


def _extract_resource_type(module_path: str) -> str:
    """从模块路径推导资源类型，剔除 UUID 段。"""
    parts = module_path.strip("/").split("/")
    resource = parts[-1] if parts else module_path
    resource = re.sub(r"[0-9a-f]{8,}", "", resource).strip("-_")
    return resource if resource else module_path.replace("/", "_")


def _extract_action(action_str: str | None, method: str) -> str:
    """从动作串或 HTTP 方法推导审计动作名。"""
    if not action_str:
        return method.lower()
    action = action_str.strip("/").split("/", 1)[0]
    return action.replace("-", "_") if action else method.lower()


def _match_audit_target(request: Request) -> tuple[str, str] | None:
    """匹配请求的审计目标（资源类型, 动作），不匹配返回 None。"""
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
