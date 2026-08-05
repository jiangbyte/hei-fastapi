"""Rate-limiting middleware — sliding-window per IP and per user using Redis.

等保 requirement: restrict login attempts and sensitive API abuse.

"""
from __future__ import annotations

import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.network.client_ip import get_client_ip
from app.core.security.session import session_store
from app.deps.context import account_id_ctx, client_ip_ctx
from app.platform.cache.redis import get_redis

logger = logging.getLogger(__name__)

# (path_pattern, requests_per_window, window_seconds, scope)
# scope: "ip" = per-IP, "user" = per-authenticated-user, "mix" = user if auth else IP
RATE_LIMIT_RULES: list[tuple[re.Pattern[str], int, int, str]] = [
    (re.compile(r"^/api/v\d+/(admin|portal)/login"), 10, 60, "ip"),
    (re.compile(r"^/api/v\d+/portal/register"), 5, 60, "ip"),
    (re.compile(r"^/api/v\d+/(admin|portal)/(forgot-password|reset-password)"), 5, 60, "ip"),
    (re.compile(r"^/api/v\d+/(admin|portal)/captcha"), 30, 60, "ip"),
    (re.compile(r"^/api/v\d+/"), 120, 60, "mix"),
]

# 不计入限流（健康检查 / WebSocket / 文档）
RATE_LIMIT_EXEMPT: list[re.Pattern[str]] = [
    re.compile(r"^/api/v\d+/internal/health"),
    re.compile(r"/ws(?:$|\?)"),
    re.compile(r"^/(docs|redoc|openapi\.json)"),
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter backed by Redis."""

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        for exempt in RATE_LIMIT_EXEMPT:
            if exempt.search(path):
                return await call_next(request)

        redis = get_redis()
        if redis is None:
            return await call_next(request)

        for pattern, limit, window_sec, scope in RATE_LIMIT_RULES:
            if not pattern.search(path):
                continue

            key = await self._build_key(request, pattern.pattern, scope)
            if key is None:
                break

            try:
                count = await self._increment_and_check(redis, key, limit, window_sec)
                if count > limit:
                    logger.warning("Rate limit exceeded: %s (count=%d, limit=%d)", key, count, limit)
                    return JSONResponse(
                        status_code=429,
                        content={"code": 429, "message": "请求过于频繁，请稍后再试", "data": None},
                        headers={"Retry-After": str(window_sec)},
                    )
            except Exception:
                logger.debug("Rate limit check failed for %s", key, exc_info=True)
            break

        return await call_next(request)

    async def _build_key(self, request: Request, pattern: str, scope: str) -> str | None:
        ip = client_ip_ctx.get() or get_client_ip(request) or "unknown"
        if scope == "ip":
            return f"rl:ip:{ip}:{pattern}"

        uid = account_id_ctx.get() or await self._resolve_account_id(request)
        if scope == "user":
            if not uid:
                return None
            return f"rl:user:{uid}:{pattern}"

        # mix
        if uid:
            return f"rl:user:{uid}:{pattern}"
        return f"rl:ip:{ip}:{pattern}"

    async def _resolve_account_id(self, request: Request) -> str | None:
        """中间件早于 Depends，从 Authorization 轻量解析会话账户。"""
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.strip():
            return None
        try:
            session = await session_store.get(authorization.strip())
            return session.account_id if session else None
        except Exception:
            logger.debug("Rate limit session resolve failed", exc_info=True)
            return None

    async def _increment_and_check(
        self, redis, key: str, limit: int, window_sec: int
    ) -> int:
        """Sliding-window counter using Redis sorted set."""
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
