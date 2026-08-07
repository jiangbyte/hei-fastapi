""" Author: Charlie

出站 ACK 窗口，有限重试后回退至离线。
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from app.modules.message.im.config import ImSettings
from app.modules.message.im.connection import SessionContext
from app.modules.message.im.protocol import ImCmd
from app.platform.module.config_loader import get_module_config

logger = logging.getLogger(__name__)

OfflineCallback = Callable[[SessionContext, int, bytes], Awaitable[None]]


@dataclass(slots=True)
class _Pending:
    body: bytes
    attempts: int = 0
    next_retry_at: float = 0.0


@dataclass
class ImAckTracker:
    """按会话追踪未 ACK 的 PUSH seq；重试后调用离线回调。"""

    on_give_up: OfflineCallback | None = None
    _pending: dict[str, dict[int, _Pending]] = field(default_factory=dict)
    _task: asyncio.Task | None = None

    def _settings(self) -> ImSettings:
        cfg = get_module_config("message.im")
        return cfg if isinstance(cfg, ImSettings) else ImSettings()

    @staticmethod
    def _key(session: SessionContext) -> str:
        return f"{session.account_type}:{session.account_id}:{session.terminal_id}"

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._retry_loop(), name="im-ack-retry")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._pending.clear()

    def track(self, session: SessionContext, seq: int, body: bytes) -> None:
        if seq <= 0:
            return
        cfg = self._settings()
        key = self._key(session)
        bucket = self._pending.setdefault(key, {})
        # 超出窗口时丢弃最旧项
        while len(bucket) >= cfg.ack_window:
            oldest = min(bucket.keys())
            bucket.pop(oldest, None)
        bucket[seq] = _Pending(
            body=body, attempts=0, next_retry_at=time.monotonic() + cfg.ack_retry_seconds
        )
        session.pending_acks[seq] = body

    def ack(self, session: SessionContext, ack_seq: int) -> None:
        if ack_seq <= 0:
            return
        key = self._key(session)
        bucket = self._pending.get(key, {})
        # 累积 ACK：丢弃所有 seq <= ack_seq
        for seq in list(bucket.keys()):
            if seq <= ack_seq:
                bucket.pop(seq, None)
                session.pending_acks.pop(seq, None)
        if not bucket:
            self._pending.pop(key, None)

    def clear_session(self, session: SessionContext) -> None:
        key = self._key(session)
        self._pending.pop(key, None)
        session.pending_acks.clear()

    async def _retry_loop(self) -> None:
        from app.modules.message.im.registry import registry

        while True:
            try:
                await asyncio.sleep(0.5)
                cfg = self._settings()
                now = time.monotonic()
                for key, bucket in list(self._pending.items()):
                    parts = key.split(":", 2)
                    if len(parts) != 3:
                        continue
                    account_type, account_id, terminal_id = parts
                    session = registry.get_session(account_type, account_id, terminal_id)
                    if session is None:
                        self._pending.pop(key, None)
                        continue
                    for seq, pending in list(bucket.items()):
                        if pending.next_retry_at > now:
                            continue
                        if pending.attempts >= cfg.ack_max_retries:
                            bucket.pop(seq, None)
                            session.pending_acks.pop(seq, None)
                            if self.on_give_up is not None:
                                try:
                                    await self.on_give_up(session, seq, pending.body)
                                except Exception:
                                    logger.warning("ack offline callback failed", exc_info=True)
                            continue
                        pending.attempts += 1
                        pending.next_retry_at = now + cfg.ack_retry_seconds
                        try:
                            await session.conn.send_frame(ImCmd.PUSH, body=pending.body, seq=seq)
                        except Exception:
                            logger.debug("ack retry send failed", exc_info=True)
                    if not bucket:
                        self._pending.pop(key, None)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("im ack retry loop error")


ack_tracker = ImAckTracker()
