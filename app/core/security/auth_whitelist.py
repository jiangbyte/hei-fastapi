""" Author: Charlie

统一鉴权白名单：内置模式 + settings.auth.auth_whitelist。
"""
from __future__ import annotations

import fnmatch
import logging
from functools import lru_cache

from app.core.config.settings import settings

logger = logging.getLogger(__name__)

# 完整请求路径（含 /api）。支持 fnmatch 通配符 (* ? [])。
BUILTIN_AUTH_WHITELIST: tuple[str, ...] = (
    "/",
    "/docs",
    "/docs/*",
    "/redoc",
    "/openapi.json",
    "/metrics",
    "/api/v1/admin/captcha",
    "/api/v1/admin/password-key",
    "/api/v1/admin/login",
    "/api/v1/admin/login/mfa",
    "/api/v1/admin/forgot-password",
    "/api/v1/admin/reset-password",
    "/api/v1/portal/captcha",
    "/api/v1/portal/password-key",
    "/api/v1/portal/login",
    "/api/v1/portal/register",
    "/api/v1/portal/forgot-password",
    "/api/v1/portal/reset-password",
    "/api/v1/internal/health",
    "/api/v1/internal/health/*",
    "/api/v1/files",
    "/api/v1/files/*",
    "/api/v1/portal/sys/banners/list",
    "/api/v1/portal/sys/banners/interaction",
    "/api/v1/portal/sys/dicts/tree",
    "/api/v1/portal/sys/resources/current",
    "/api/v1/portal/message/announcements/list",
)


@lru_cache(maxsize=1)
def get_auth_whitelist_patterns() -> tuple[str, ...]:
    configured = tuple(
        pattern.strip() for pattern in settings.auth.auth_whitelist if pattern and pattern.strip()
    )
    patterns = BUILTIN_AUTH_WHITELIST + configured
    logger.info(
        "Auth whitelist loaded: %d built-in, %d configured, %d total",
        len(BUILTIN_AUTH_WHITELIST),
        len(configured),
        len(patterns),
    )
    return patterns


def clear_auth_whitelist_cache() -> None:
    get_auth_whitelist_patterns.cache_clear()


def is_auth_whitelisted(path: str) -> bool:
    normalized = path.rstrip("/") or "/"
    candidates = {path, normalized}
    if path != normalized:
        candidates.add(normalized)
    for pattern in get_auth_whitelist_patterns():
        for candidate in candidates:
            if fnmatch.fnmatchcase(candidate, pattern):
                return True
            # 允许无尾斜杠的模式匹配目录式路径
            if pattern.endswith("/*") and fnmatch.fnmatchcase(candidate, pattern[:-2]):
                return True
    return False
