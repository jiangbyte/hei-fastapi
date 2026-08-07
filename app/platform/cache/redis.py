""" Author: Charlie """

import logging
import socket

from redis.asyncio import Redis

from app.core.config.settings import settings

logger = logging.getLogger(__name__)

redis_client: Redis | None = None


def _keepalive_options() -> dict[int, int]:
    """尽力配置 TCP keepalive 选项（Linux/BSD；Windows 可能忽略）。"""
    opts: dict[int, int] = {}
    if hasattr(socket, "TCP_KEEPIDLE"):
        opts[socket.TCP_KEEPIDLE] = 60
    if hasattr(socket, "TCP_KEEPINTVL"):
        opts[socket.TCP_KEEPINTVL] = 10
    if hasattr(socket, "TCP_KEEPCNT"):
        opts[socket.TCP_KEEPCNT] = 3
    return opts


async def init_redis() -> None:
    global redis_client
    if redis_client is not None:
        return
    # 通过 redis-py 连接参数对齐 Redisson keepAlive 意图。
    kwargs: dict = {
        "decode_responses": False,
        "max_connections": settings.redis.max_connections,
        "socket_keepalive": True,
    }
    keepalive = _keepalive_options()
    if keepalive:
        kwargs["socket_keepalive_options"] = keepalive
    redis_client = Redis.from_url(settings.redis.url, **kwargs)
    await redis_client.ping()
    logger.info("Redis connected (socket_keepalive=True)")


def get_redis() -> Redis | None:
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None
