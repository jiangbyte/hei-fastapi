""" Author: Charlie

IM 短时 AUTH 票据（Redis）。
"""
from __future__ import annotations

import logging
import secrets

import orjson

from app.core.config.settings import settings
from app.core.security.session import session_store as redis_session_store
from app.platform.cache.redis import get_redis

logger = logging.getLogger(__name__)

_TICKET_PREFIX = "im:ticket:"
_TICKET_TOKEN_PREFIX = "imt_"


async def issue_im_ticket(*, account_type: str, account_id: str) -> tuple[str, int]:
    """签发一次性 IM AUTH 票据，返回 (ticket, ttl_seconds)。"""
    ttl = max(30, int(settings.auth.im_ticket_ttl_seconds))
    ticket = f"{_TICKET_TOKEN_PREFIX}{secrets.token_urlsafe(24)}"
    payload = orjson.dumps(
        {
            "account_type": str(account_type),
            "account_id": str(account_id),
        }
    )
    redis = get_redis()
    if redis is None:
        raise RuntimeError("Redis is required to issue IM tickets")
    await redis.setex(f"{_TICKET_PREFIX}{ticket}", ttl, payload)
    return ticket, ttl


async def auth_token(token: str) -> tuple[str, str] | None:
    """校验 session token 或 IM 票据，返回 (account_type, account_id)。"""
    raw = (token or "").strip()
    if not raw:
        return None
    if raw.startswith(_TICKET_TOKEN_PREFIX):
        return await _consume_ticket(raw)
    try:
        session = await redis_session_store.get(raw)
        if session is None:
            return None
        return (str(session.account_type), session.account_id)
    except Exception:
        return None


async def _consume_ticket(ticket: str) -> tuple[str, str] | None:
    redis = get_redis()
    if redis is None:
        return None
    key = f"{_TICKET_PREFIX}{ticket}"
    try:
        # 可用时使用 GETDEL，否则 GET + DELETE。
        raw = None
        if hasattr(redis, "getdel"):
            raw = await redis.getdel(key)
        else:
            raw = await redis.get(key)
            if raw is not None:
                await redis.delete(key)
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode()
        data = orjson.loads(raw)
        account_type = str(data.get("account_type") or "")
        account_id = str(data.get("account_id") or "")
        if not account_type or not account_id:
            return None
        return (account_type, account_id)
    except Exception:
        logger.debug("IM ticket consume failed", exc_info=True)
        return None


def normalize_channel(raw: str | None, account_type: str | None = None) -> str:
    value = (raw or account_type or "").strip().upper()
    if value in {"ADMIN", "PORTAL"}:
        return value
    return "PORTAL"
