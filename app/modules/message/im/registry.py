""" Author: Charlie

会话注册表 + Redis 在线/pubsub 路由。
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid

import orjson

from app.modules.message.im.connection import SessionContext
from app.modules.message.im.protocol import ImCmd, encode_json_body
from app.platform.cache.redis import get_redis

logger = logging.getLogger(__name__)


class ImSessionRegistry:
    """进程内会话，Redis 在线状态与按用户 pub/sub。"""

    _ONLINE_TTL = 120

    def __init__(self) -> None:
        # 连接索引：channel -> account_id -> terminal_id -> SessionContext
        self._sessions: dict[str, dict[str, dict[str, SessionContext]]] = {}
        self._lock = asyncio.Lock()
        self._instance_id = uuid.uuid4().hex[:8]
        self._pubsub = None
        self._pubsub_task: asyncio.Task | None = None
        self._subscribed: set[str] = set()
        self._seq = 0

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @staticmethod
    def _online_key(account_type: str, account_id: str) -> str:
        return f"im:online:{account_type}:{account_id}"

    @staticmethod
    def _user_channel(account_type: str, account_id: str) -> str:
        return f"im:user:{account_type}:{account_id}"

    def connection_stats(self) -> dict[str, int]:
        ws = tcp = 0
        for by_account in self._sessions.values():
            for by_terminal in by_account.values():
                for session in by_terminal.values():
                    if session.transport == "ws":
                        ws += 1
                    else:
                        tcp += 1
        return {"ws": ws, "tcp": tcp, "total": ws + tcp}

    def _count_user(self, account_type: str, account_id: str) -> int:
        return len(self._sessions.get(account_type, {}).get(account_id, {}))

    async def next_seq(self) -> int:
        async with self._lock:
            self._seq += 1
            return self._seq

    async def register(self, session: SessionContext) -> SessionContext | None:
        """注册会话；同终端若有旧会话则返回被踢出的会话。"""
        kicked: SessionContext | None = None
        async with self._lock:
            by_account = self._sessions.setdefault(session.account_type, {}).setdefault(
                session.account_id, {}
            )
            previous = by_account.get(session.terminal_id)
            if previous is not None and previous.conn is not session.conn:
                kicked = previous
            by_account[session.terminal_id] = session
            session.last_active = time.monotonic()
            first = self._count_user(session.account_type, session.account_id) == 1
        if kicked is not None:
            try:
                await kicked.conn.send_frame(
                    ImCmd.KICK,
                    body=encode_json_body({"reason": "same_terminal"}),
                )
                await kicked.conn.close(4002, "kicked")
            except Exception:
                logger.debug("failed to kick previous terminal", exc_info=True)
        await self.touch_online(session.account_type, session.account_id)
        if first:
            await self._subscribe_user(session.account_type, session.account_id)
        return kicked

    async def unregister(self, account_type: str, account_id: str, terminal_id: str) -> None:
        async with self._lock:
            by_account = self._sessions.get(account_type, {}).get(account_id, {})
            by_account.pop(terminal_id, None)
            empty = not by_account
            if empty:
                self._sessions.get(account_type, {}).pop(account_id, None)
        if empty:
            await self._unsubscribe_user(account_type, account_id)
            redis = get_redis()
            if redis is not None:
                try:
                    key = self._online_key(account_type, account_id)
                    await redis.srem(key, self._instance_id)
                    if not await redis.scard(key):
                        await redis.delete(key)
                except Exception:
                    logger.warning("failed to clear im online", exc_info=True)

    async def touch_online(self, account_type: str, account_id: str) -> None:
        redis = get_redis()
        if redis is None:
            return
        try:
            key = self._online_key(account_type, account_id)
            await redis.sadd(key, self._instance_id)
            await redis.expire(key, self._ONLINE_TTL)
        except Exception:
            logger.warning("failed to touch im online", exc_info=True)

    async def touch_session(self, account_type: str, account_id: str, terminal_id: str) -> None:
        session = self.get_session(account_type, account_id, terminal_id)
        if session is not None:
            session.last_active = time.monotonic()
        await self.touch_online(account_type, account_id)

    def get_session(
        self, account_type: str, account_id: str, terminal_id: str
    ) -> SessionContext | None:
        return self._sessions.get(account_type, {}).get(account_id, {}).get(terminal_id)

    def list_user_sessions(self, account_type: str, account_id: str) -> list[SessionContext]:
        return list(self._sessions.get(account_type, {}).get(account_id, {}).values())

    async def is_globally_online(self, account_type: str, account_id: str) -> bool:
        if self._count_user(account_type, account_id) > 0:
            return True
        redis = get_redis()
        if redis is None:
            return False
        try:
            return bool(await redis.scard(self._online_key(account_type, account_id)))
        except Exception:
            return False

    async def batch_online(self, targets: list[tuple[str, str]]) -> set[tuple[str, str]]:
        online: set[tuple[str, str]] = set()
        missing: list[tuple[str, str]] = []
        for account_type, account_id in targets:
            if self._count_user(account_type, account_id) > 0:
                online.add((account_type, account_id))
            else:
                missing.append((account_type, account_id))
        redis = get_redis()
        if redis is None or not missing:
            return online
        try:
            pipe = redis.pipeline()
            for account_type, account_id in missing:
                pipe.scard(self._online_key(account_type, account_id))
            counts = await pipe.execute()
            for (account_type, account_id), count in zip(missing, counts, strict=False):
                if count:
                    online.add((account_type, account_id))
        except Exception:
            logger.warning("batch online check failed", exc_info=True)
        return online

    async def has_remote_instances(self, account_type: str, account_id: str) -> bool:
        redis = get_redis()
        if redis is None:
            return False
        try:
            members = await redis.smembers(self._online_key(account_type, account_id))
            decoded = {m.decode() if isinstance(m, (bytes, bytearray)) else str(m) for m in members}
            return any(mid != self._instance_id for mid in decoded)
        except Exception:
            return True

    async def send_to_user_local(
        self,
        account_type: str,
        account_id: str,
        cmd: ImCmd,
        body: bytes,
        *,
        seq: int = 0,
        ack: int = 0,
    ) -> int:
        sessions = self.list_user_sessions(account_type, account_id)
        if not sessions:
            return 0
        sent = 0
        for session in sessions:
            try:
                await session.conn.send_frame(cmd, body=body, seq=seq, ack=ack)
                sent += 1
            except Exception:
                logger.debug("local send failed", exc_info=True)
        return sent

    async def publish_raw(self, account_type: str, account_id: str, message: dict) -> None:
        redis = get_redis()
        if redis is None:
            return
        try:
            channel = self._user_channel(account_type, account_id)
            await redis.publish(channel, orjson.dumps(message))
        except Exception:
            logger.warning("im publish failed", exc_info=True)

    async def _publish(self, account_type: str, account_id: str, message: dict) -> None:
        await self.publish_raw(account_type, account_id, message)

    async def _subscribe_user(self, account_type: str, account_id: str) -> None:
        channel = self._user_channel(account_type, account_id)
        if channel in self._subscribed:
            return
        await self._ensure_pubsub()
        if self._pubsub is None:
            return
        try:
            await self._pubsub.subscribe(channel)
            self._subscribed.add(channel)
        except Exception:
            logger.warning("im subscribe failed %s", channel, exc_info=True)

    async def _unsubscribe_user(self, account_type: str, account_id: str) -> None:
        channel = self._user_channel(account_type, account_id)
        if channel not in self._subscribed or self._pubsub is None:
            return
        try:
            await self._pubsub.unsubscribe(channel)
            self._subscribed.discard(channel)
        except Exception:
            logger.warning("im unsubscribe failed %s", channel, exc_info=True)

    async def _ensure_pubsub(self) -> None:
        redis = get_redis()
        if redis is None:
            return
        if self._pubsub is not None and self._pubsub_task and not self._pubsub_task.done():
            return
        self._pubsub = redis.pubsub()
        self._pubsub_task = asyncio.create_task(self._pubsub_listen(), name="im-pubsub")

    async def _pubsub_listen(self) -> None:
        assert self._pubsub is not None
        try:
            while True:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message is None:
                    await asyncio.sleep(0.01)
                    continue
                if message.get("type") != "message":
                    continue
                data = message.get("data")
                if not data:
                    continue
                raw = data if isinstance(data, (bytes, bytearray)) else str(data).encode()
                try:
                    payload = orjson.loads(raw)
                except Exception:
                    continue
                if payload.get("origin") == self._instance_id:
                    continue
                channel = message.get("channel")
                if isinstance(channel, (bytes, bytearray)):
                    channel = channel.decode()
                # Redis 频道格式：im:user:{type}:{id}
                parts = str(channel).split(":")
                if len(parts) < 4:
                    continue
                account_type, account_id = parts[2], parts[3]
                if self._count_user(account_type, account_id) == 0:
                    continue
                cmd = ImCmd(int(payload.get("cmd", ImCmd.PUSH)))
                body = str(payload.get("body", "")).encode("latin1")
                seq = int(payload.get("seq", 0))
                await self.send_to_user_local(account_type, account_id, cmd, body, seq=seq)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("im pubsub listener crashed")
        finally:
            try:
                if self._pubsub is not None:
                    await self._pubsub.aclose()
            except Exception:
                pass
            self._pubsub = None

    async def shutdown(self) -> None:
        if self._pubsub_task is not None:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except asyncio.CancelledError:
                pass
            self._pubsub_task = None
        async with self._lock:
            sessions = [
                s
                for by_account in self._sessions.values()
                for by_terminal in by_account.values()
                for s in by_terminal.values()
            ]
            self._sessions.clear()
            self._subscribed.clear()
        for session in sessions:
            try:
                await session.conn.close()
            except Exception:
                pass


registry = ImSessionRegistry()
