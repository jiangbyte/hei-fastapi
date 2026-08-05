"""WebSocket connection manager.

Handles per-instance WS connections and uses Redis Pub/Sub for cross-instance routing.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections. Singleton per process instance.
    Uses Redis Pub/Sub for cross-instance message routing.
    """

    def __init__(self, redis_client=None):
        # { account_type: { account_id: { terminal_id: WebSocket } } }
        self._connections: dict[str, dict[str, dict[str, WebSocket]]] = {}
        self._redis = redis_client
        self._pubsub = None
        self._pubsub_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._instance_id = str(uuid.uuid4())[:8]  # unique per-process

    # 在线标记 TTL：崩溃残留实例 ID 会过期；正常连接靠 heartbeat 续期
    _ONLINE_TTL_SECONDS = 120

    @staticmethod
    def _online_key(account_type: str, account_id: str) -> str:
        return f"ws:online:{account_type}:{account_id}"

    async def touch_online(self, account_type: str, account_id: str) -> None:
        """标记本实例上该用户在线，并刷新 TTL，避免 worker 崩溃后假在线。"""
        await self._ensure_pubsub()
        if self._redis is None:
            return
        try:
            key = self._online_key(account_type, account_id)
            await self._redis.sadd(key, self._instance_id)
            await self._redis.expire(key, self._ONLINE_TTL_SECONDS)
        except Exception:
            logger.warning("Failed to mark WS online in Redis for %s/%s", account_type, account_id, exc_info=True)

    async def connect(self, account_type: str, account_id: str, terminal_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.setdefault(account_type, {}).setdefault(account_id, {})[terminal_id] = ws
        num = self._count_account_connections(account_type, account_id)
        logger.info("WS connect: %s/%s terminal=%s, total=%d connections for user", account_type, account_id, terminal_id, num)
        await self._ensure_pubsub()
        if self._redis is None:
            logger.warning("Redis not available — cross-worker WS routing disabled")
        else:
            await self.touch_online(account_type, account_id)

    async def disconnect(self, account_type: str, account_id: str, terminal_id: str) -> None:
        async with self._lock:
            by_account = self._connections.get(account_type, {}).get(account_id, {})
            by_account.pop(terminal_id, None)
            if not by_account:
                self._connections.get(account_type, {}).pop(account_id, None)
        num = self._count_account_connections(account_type, account_id)
        logger.info("WS disconnect: %s/%s terminal=%s, remaining=%d", account_type, account_id, terminal_id, num)
        # 本进程已无该用户连接时，从全局在线集合移除本实例
        if num == 0 and self._redis is not None:
            try:
                key = self._online_key(account_type, account_id)
                await self._redis.srem(key, self._instance_id)
                if not await self._redis.scard(key):
                    await self._redis.delete(key)
            except Exception:
                logger.warning("Failed to clear WS online in Redis for %s/%s", account_type, account_id, exc_info=True)
        # Stop pubsub if no connections left on this instance
        if not self._connections:
            await self._stop_pubsub()

    def _count_account_connections(self, account_type: str, account_id: str) -> int:
        return len(self._connections.get(account_type, {}).get(account_id, {}))

    def is_online(self, account_type: str, account_id: str) -> bool:
        return self._count_account_connections(account_type, account_id) > 0

    async def is_globally_online(self, account_type: str, account_id: str) -> bool:
        """本机或任一 worker 是否在线（Redis 集合）。"""
        if self.is_online(account_type, account_id):
            return True
        await self._ensure_pubsub()
        if self._redis is None:
            return False
        try:
            count = await self._redis.scard(self._online_key(account_type, account_id))
            return int(count or 0) > 0
        except Exception:
            return False

    def has_redis(self) -> bool:
        """Whether Redis is available for cross-worker routing."""
        return self._redis is not None

    async def send_to_user(self, account_type: str, account_id: str, message: dict) -> None:
        """Send a JSON message to all WS connections of a user on this instance."""
        connections = self._connections.get(account_type, {}).get(account_id, {})
        payload = json.dumps(message, ensure_ascii=False, default=str)
        for terminal_id, ws in list(connections.items()):
            try:
                await ws.send_text(payload)
            except Exception:
                logger.warning("WS send failed to %s/%s terminal=%s, removing", account_type, account_id, terminal_id)
                await self.disconnect(account_type, account_id, terminal_id)

    async def route_to_user(self, account_type: str, account_id: str, message: dict) -> None:
        """Route message to user: local delivery + cross-worker via Redis Pub/Sub."""
        # Local delivery first
        await self.send_to_user(account_type, account_id, message)
        # Cross-worker via Redis（懒加载，避免启动时序导致 _redis 一直为 None）
        if self._redis is None:
            await self._ensure_pubsub()
        if self._redis:
            try:
                channel = f"ws:user:{account_type}:{account_id}"
                # Tag the message with originating instance_id so cross-worker
                # listeners on the same process can skip it (local already delivered).
                out = {**message, "_origin_instance": self._instance_id}
                payload = json.dumps(out, ensure_ascii=False, default=str)
                await self._redis.publish(channel, payload)
            except Exception:
                logger.warning("Redis publish failed for %s/%s", account_type, account_id, exc_info=True)

    def get_online_users(self) -> list[tuple[str, str]]:
        """Return list of (account_type, account_id) connected on this instance."""
        result = []
        for account_type, by_account in self._connections.items():
            for account_id in by_account:
                result.append((account_type, account_id))
        return result

    def connection_stats(self) -> dict:
        """Return connection statistics for health checking."""
        total = sum(
            len(terminals)
            for by_account in self._connections.values()
            for terminals in by_account.values()
        )
        return {
            "total_connections": total,
            "redis_available": self._redis is not None,
            "pubsub_active": self._pubsub_task is not None,
        }

    async def broadcast_instance(self, message: dict) -> None:
        """Broadcast to ALL connections on this instance."""
        payload = json.dumps(message, ensure_ascii=False, default=str)
        for account_type, by_account in list(self._connections.items()):
            for account_id, terminals in list(by_account.items()):
                for terminal_id, ws in list(terminals.items()):
                    try:
                        await ws.send_text(payload)
                    except Exception:
                        await self.disconnect(account_type, account_id, terminal_id)

    # ── Redis Pub/Sub ────────────────────────────────────────────────────────

    async def _ensure_pubsub(self) -> None:
        """Start Redis pubsub listener if redis is available and not already running."""
        if self._pubsub_task is not None:
            return
        # Lazy-init: Redis might not have been ready at ConnectionManager init time
        if self._redis is None:
            from app.platform.cache.redis import get_redis
            self._redis = get_redis()
        if self._redis is None:
            return
        self._pubsub = self._redis.pubsub()
        await self._pubsub.psubscribe("ws:user:*")
        self._pubsub_task = asyncio.create_task(self._pubsub_listen())
        logger.info("Redis Pub/Sub listener started")

    async def _stop_pubsub(self) -> None:
        if self._pubsub_task:
            self._pubsub_task.cancel()
            self._pubsub_task = None
        if self._pubsub:
            try:
                await self._pubsub.punsubscribe()
            except Exception:
                pass
            self._pubsub = None
        logger.info("Redis Pub/Sub listener stopped")

    async def _pubsub_listen(self) -> None:
        """Listen for cross-worker messages and deliver locally.
        Self-healing: crashes restart after a delay.
        """
        # Keep a reference to the original pubsub object so re-entry is safe
        pubsub = self._pubsub
        if pubsub is None:
            return
        while True:
            try:
                while True:
                    try:
                        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=10)
                    except asyncio.TimeoutError:
                        # Timeout — send heartbeat ping to keep connection alive
                        try:
                            await pubsub.ping()
                        except Exception:
                            await asyncio.sleep(1)
                        continue
                    except Exception as e:
                        # Re-raise socket errors for the outer handler
                        raise e
                    
                    if msg is None:
                        continue
                    
                    if msg["type"] != "pmessage":
                        continue
                    # channel format: ws:user:{account_type}:{account_id}
                    channel = (msg.get("channel") or b"").decode()
                    parts = channel.split(":")
                    if len(parts) != 4:
                        continue
                    _, _, account_type, account_id = parts
                    try:
                        data = json.loads(msg["data"])
                        # Skip if this message originated from the same instance
                        # (already delivered locally in route_to_user)
                        if data.get("_origin_instance") == self._instance_id:
                            continue
                        # Only deliver if recipient has connections on this worker
                        if self._count_account_connections(account_type, account_id) == 0:
                            continue
                        data.pop("_origin_instance", None)
                        await self.send_to_user(account_type, account_id, data)
                    except Exception:
                        pass
            except asyncio.CancelledError:
                return
            except Exception as e:
                # If _stop_pubsub already cleaned us up, exit without restarting
                if self._pubsub_task is not asyncio.current_task():
                    return
                # TimeoutError = idle connection dropped by Redis server, retry fast.
                # Other errors = actual failure, back off longer.
                is_timeout = isinstance(e, asyncio.TimeoutError) or type(e).__name__ == 'TimeoutError'
                delay = 1 if is_timeout else 5
                if not is_timeout:
                    logger.warning("Redis pubsub listener crashed, restarting in %ds", delay, exc_info=True)
                else:
                    logger.warning("Redis pubsub idle timeout, reconnecting in %ds", delay)
                await asyncio.sleep(delay)
                try:
                    # Re-subscribe — the old pubsub object may be in a bad state
                    readis = self._redis
                    if readis is None:
                        from app.platform.cache.redis import get_redis
                        readis = get_redis()
                    if readis is None:
                        return
                    pubsub = readis.pubsub()
                    await pubsub.psubscribe("ws:user:*")
                    self._pubsub = pubsub
                except Exception:
                    logger.error("Failed to restart pubsub listener", exc_info=True)
                    return
