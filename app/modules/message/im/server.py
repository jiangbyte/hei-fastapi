""" Author: Charlie

进程内双通道 IM 实时服务（WS Binary + TCP）。
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from urllib.parse import parse_qs, urlparse

from app.modules.message.im.ack import ack_tracker
from app.modules.message.im.config import ImSettings
from app.modules.message.im.connection import (
    SessionContext,
    TcpBinaryConnection,
    WebSocketBinaryConnection,
)
from app.modules.message.im.handler import (
    authenticate_connection,
    authenticate_from_auth_frame,
    handle_authed_frame,
)
from app.modules.message.im.protocol import FrameBuffer, FrameDecodeError, ImCmd, decode_frame
from app.modules.message.im.registry import registry
from app.platform.module.config_loader import get_module_config

logger = logging.getLogger(__name__)


class ImRealtimeServer:
    """在共享 asyncio 循环上启停 WS:18080 与 TCP:18081。"""

    _LOCK_KEY = "im:gateway:bind_lock"
    _LOCK_TTL = 30

    def __init__(self) -> None:
        self._ws_server = None
        self._tcp_server: asyncio.AbstractServer | None = None
        self._idle_task: asyncio.Task | None = None
        self._lock_task: asyncio.Task | None = None
        self._started = False
        self._is_leader = False
        self._lock_token = uuid.uuid4().hex

    def _settings(self) -> ImSettings:
        cfg = get_module_config("message.im")
        return cfg if isinstance(cfg, ImSettings) else ImSettings()

    async def _try_become_leader(self) -> bool:
        """仅一个 gunicorn worker 可绑定 IM 端口（Redis NX 锁）。"""
        from app.platform.cache.redis import get_redis

        redis = get_redis()
        if redis is None:
            # 单进程/无 Redis：允许绑定（开发/测试）。
            self._is_leader = True
            return True
        try:
            ok = await redis.set(
                self._LOCK_KEY,
                self._lock_token,
                nx=True,
                ex=self._LOCK_TTL,
            )
            self._is_leader = bool(ok)
            return self._is_leader
        except Exception:
            logger.warning("IM bind lock failed; skipping gateway bind", exc_info=True)
            return False

    async def _renew_leader_lock(self) -> None:
        from app.platform.cache.redis import get_redis

        while True:
            await asyncio.sleep(self._LOCK_TTL // 3)
            redis = get_redis()
            if redis is None or not self._is_leader:
                continue
            try:
                current = await redis.get(self._LOCK_KEY)
                token = current.decode() if isinstance(current, (bytes, bytearray)) else current
                if token != self._lock_token:
                    logger.error("IM bind lock lost; gateway may become stale")
                    continue
                await redis.expire(self._LOCK_KEY, self._LOCK_TTL)
            except Exception:
                logger.debug("IM lock renew failed", exc_info=True)

    async def _release_leader_lock(self) -> None:
        from app.platform.cache.redis import get_redis

        redis = get_redis()
        if redis is None or not self._is_leader:
            return
        try:
            current = await redis.get(self._LOCK_KEY)
            token = current.decode() if isinstance(current, (bytes, bytearray)) else current
            if token == self._lock_token:
                await redis.delete(self._LOCK_KEY)
        except Exception:
            logger.debug("IM lock release failed", exc_info=True)
        self._is_leader = False

    async def start(self) -> None:
        if self._started:
            return
        settings = self._settings()
        if not settings.enabled:
            logger.info("IM realtime server disabled")
            return

        if not await self._try_become_leader():
            logger.info(
                "IM realtime bind skipped (another worker holds %s); "
                "this process still fans out via Redis pub/sub",
                self._LOCK_KEY,
            )
            # 若仍有会话存在，仍启动 ACK 追踪器以处理本地推送。
            ack_tracker.start()
            self._started = True
            return

        async def _on_give_up(session: SessionContext, seq: int, body: bytes) -> None:
            from app.modules.message.im.protocol import PushEvent, decode_json_body
            from app.modules.message.im.router import im_router

            data = decode_json_body(body) if body else {}
            event_i = int(data.get("event") or 0)
            payload = data.get("payload") or {}
            try:
                event = PushEvent(event_i)
            except ValueError:
                return
            await im_router.enqueue_offline(
                account_type=session.account_type,
                account_id=session.account_id,
                event=event,
                payload=payload if isinstance(payload, dict) else {},
                message_id=str(payload.get("id") or ""),
                conversation_id=str(payload.get("conversation_id") or ""),
            )

        ack_tracker.on_give_up = _on_give_up
        ack_tracker.start()

        await self._start_ws(settings)
        await self._start_tcp(settings)
        self._idle_task = asyncio.create_task(self._idle_watch(settings), name="im-idle")
        self._lock_task = asyncio.create_task(self._renew_leader_lock(), name="im-lock")
        self._started = True
        logger.info(
            "IM realtime started ws=%s:%s tcp=%s:%s (leader)",
            settings.ws_host,
            settings.ws_port,
            settings.tcp_host,
            settings.tcp_port,
        )

    async def stop(self) -> None:
        if self._lock_task is not None:
            self._lock_task.cancel()
            try:
                await self._lock_task
            except asyncio.CancelledError:
                pass
            self._lock_task = None
        if self._idle_task is not None:
            self._idle_task.cancel()
            try:
                await self._idle_task
            except asyncio.CancelledError:
                pass
            self._idle_task = None
        await ack_tracker.stop()
        if self._ws_server is not None:
            self._ws_server.close()
            await self._ws_server.wait_closed()
            self._ws_server = None
        if self._tcp_server is not None:
            self._tcp_server.close()
            await self._tcp_server.wait_closed()
            self._tcp_server = None
        await self._release_leader_lock()
        await registry.shutdown()
        self._started = False
        logger.info("IM realtime stopped")

    async def _start_ws(self, settings: ImSettings) -> None:
        from websockets.asyncio.server import serve

        async def ws_handler(websocket) -> None:
            path = getattr(websocket, "request", None)
            raw_path = path.path if path is not None else getattr(websocket, "path", "/")
            parsed = urlparse(raw_path)
            if parsed.path.rstrip("/") != settings.path.rstrip("/"):
                await websocket.close(1008, "invalid path")
                return
            qs = parse_qs(parsed.query)
            token = (qs.get("token") or [None])[0]
            terminal_id = (qs.get("terminal_id") or qs.get("terminalId") or [None])[0]
            channel = (qs.get("channel") or [None])[0]

            conn = WebSocketBinaryConnection(websocket)
            session: SessionContext | None = None
            try:
                if token and terminal_id:
                    session = await authenticate_connection(
                        conn,
                        token=token,
                        terminal_id=terminal_id,
                        channel=channel,
                        transport="ws",
                    )
                else:
                    # 等待 AUTH 帧
                    session = await self._wait_auth_ws(websocket, conn, settings)
                if session is None:
                    return
                await self._ws_loop(websocket, session, settings)
            finally:
                if session is not None:
                    ack_tracker.clear_session(session)
                    await registry.unregister(
                        session.account_type, session.account_id, session.terminal_id
                    )

        self._ws_server = await serve(
            ws_handler,
            settings.ws_host,
            settings.ws_port,
            max_size=settings.max_frame_bytes,
            ping_interval=None,
            ping_timeout=None,
        )

    async def _wait_auth_ws(self, websocket, conn, settings: ImSettings) -> SessionContext | None:
        try:
            raw = await asyncio.wait_for(websocket.recv(), timeout=settings.auth_timeout_seconds)
        except (TimeoutError, Exception):
            await conn.close(4001, "auth timeout")
            return None
        if isinstance(raw, str):
            await conn.close(1003, "binary required")
            return None
        try:
            cmd, _flags, _seq, _ack, body = decode_frame(raw)
        except FrameDecodeError:
            await conn.close(1002, "bad frame")
            return None
        if cmd != ImCmd.AUTH:
            await conn.close(4001, "auth required")
            return None
        return await authenticate_from_auth_frame(conn, body, transport="ws")

    async def _ws_loop(self, websocket, session: SessionContext, settings: ImSettings) -> None:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.recv(), timeout=settings.idle_seconds)
            except TimeoutError:
                logger.info(
                    "IM WS idle kick %s/%s terminal=%s",
                    session.account_type,
                    session.account_id,
                    session.terminal_id,
                )
                await session.conn.close(4000, "idle")
                return
            if isinstance(raw, str):
                continue
            try:
                cmd, flags, seq, ack, body = decode_frame(raw)
            except FrameDecodeError:
                await session.conn.close(1002, "bad frame")
                return
            await handle_authed_frame(session, cmd, flags, seq, ack, body)

    async def _start_tcp(self, settings: ImSettings) -> None:
        async def tcp_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            conn = TcpBinaryConnection(writer)
            session: SessionContext | None = None
            buf = FrameBuffer()
            try:
                # 首帧必须为 AUTH
                session = await self._wait_auth_tcp(reader, writer, conn, buf, settings)
                if session is None:
                    return
                while True:
                    try:
                        chunk = await asyncio.wait_for(
                            reader.read(65536), timeout=settings.idle_seconds
                        )
                    except TimeoutError:
                        await session.conn.close()
                        return
                    if not chunk:
                        return
                    try:
                        frames = buf.feed(chunk)
                    except FrameDecodeError:
                        await session.conn.close()
                        return
                    for cmd, flags, seq, ack, body in frames:
                        await handle_authed_frame(session, cmd, flags, seq, ack, body)
            finally:
                if session is not None:
                    ack_tracker.clear_session(session)
                    await registry.unregister(
                        session.account_type, session.account_id, session.terminal_id
                    )
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

        self._tcp_server = await asyncio.start_server(
            tcp_handler, settings.tcp_host, settings.tcp_port
        )

    async def _wait_auth_tcp(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        conn: TcpBinaryConnection,
        buf: FrameBuffer,
        settings: ImSettings,
    ) -> SessionContext | None:
        deadline = time.monotonic() + settings.auth_timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                await conn.close()
                return None
            try:
                chunk = await asyncio.wait_for(reader.read(65536), timeout=remaining)
            except TimeoutError:
                await conn.close()
                return None
            if not chunk:
                return None
            try:
                frames = buf.feed(chunk)
            except FrameDecodeError:
                await conn.close()
                return None
            if not frames:
                continue
            cmd, _flags, _seq, _ack, body = frames[0]
            if cmd != ImCmd.AUTH:
                await conn.close()
                return None
            # AUTH 后的额外帧在认证循环前被忽略 — 不应发生
            return await authenticate_from_auth_frame(conn, body, transport="tcp")

    async def _idle_watch(self, settings: ImSettings) -> None:
        while True:
            await asyncio.sleep(15)
            time.monotonic()
            # 软检查 — 硬空闲由 recv 超时强制
            stats = registry.connection_stats()
            logger.debug("IM connections %s", stats)


im_server = ImRealtimeServer()


async def start_im_realtime() -> None:
    await im_server.start()


async def stop_im_realtime() -> None:
    await im_server.stop()
