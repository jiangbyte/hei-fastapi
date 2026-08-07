""" Author: Charlie """

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass

import orjson

from app.core.config.settings import settings
from app.platform.events import emit

logger = logging.getLogger(__name__)

_REDIS_SPILL_KEY = "audit:operation:spill"


@dataclass(frozen=True, slots=True)
class OperationAuditEvent:
    resource_type: str
    action: str
    method: str
    path: str
    status_code: int
    account_id: str | None
    account_type: str | None
    request_id: str | None
    ip: str | None
    user_agent: str | None


class OperationAuditQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[OperationAuditEvent] | None = None
        self._worker: asyncio.Task[None] | None = None
        self._spill_worker: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._worker and not self._worker.done():
                return
            self._queue = asyncio.Queue(maxsize=settings.audit.operation_queue_size)
            self._worker = asyncio.create_task(self._run(), name="operation-audit-writer")
            self._spill_worker = asyncio.create_task(
                self._drain_spill(), name="operation-audit-spill"
            )

    async def stop(self) -> None:
        async with self._lock:
            queue = self._queue
            worker = self._worker
            spill = self._spill_worker
            self._queue = None
            self._worker = None
            self._spill_worker = None
        if spill is not None:
            spill.cancel()
            try:
                await spill
            except asyncio.CancelledError:
                pass
        if queue is None or worker is None:
            return

        try:
            await asyncio.wait_for(
                queue.join(),
                timeout=settings.audit.operation_shutdown_timeout_seconds,
            )
        except TimeoutError:
            logger.warning("Timed out waiting for operation audit queue to drain")

        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass

    def enqueue(self, event: OperationAuditEvent) -> bool:
        queue = self._queue
        if queue is None:
            logger.debug("Operation audit queue is not started; dropping event")
            return False
        try:
            queue.put_nowait(event)
            return True
        except asyncio.QueueFull:
            logger.warning("Operation audit queue is full; spilling to durable outbox")
            try:
                asyncio.get_running_loop().create_task(self._spill_durable(event))
            except RuntimeError:
                pass
            return False

    async def _spill_durable(self, event: OperationAuditEvent) -> None:
        """优先写入 DB outbox；DB 失败时回退到 Redis 列表。"""
        if await _write_outbox(event):
            return
        from app.platform.cache.redis import get_redis

        redis = get_redis()
        if redis is None:
            logger.warning("Audit spill failed: outbox and Redis unavailable")
            return
        try:
            await redis.rpush(_REDIS_SPILL_KEY, orjson.dumps(asdict(event)))
            await redis.ltrim(_REDIS_SPILL_KEY, -10000, -1)
        except Exception:
            logger.warning("Failed to spill audit event to Redis", exc_info=True)

    async def _drain_spill(self) -> None:
        from app.platform.cache.redis import get_redis

        while True:
            try:
                await asyncio.sleep(2)
                queue = self._queue
                if queue is None:
                    continue
                await _drain_outbox_into(queue)
                redis = get_redis()
                if redis is None:
                    continue
                while True:
                    raw = await redis.lpop(_REDIS_SPILL_KEY)
                    if not raw:
                        break
                    try:
                        data = orjson.loads(raw)
                        event = OperationAuditEvent(**data)
                        await queue.put(event)
                    except Exception:
                        logger.warning("Invalid spilled audit payload", exc_info=True)
                        break
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug("Audit spill drain error", exc_info=True)

    async def _run(self) -> None:
        queue = self._queue
        if queue is None:
            return
        while True:
            event = await queue.get()
            try:
                await _record_operation_audit(event)
            except Exception:
                logger.exception("Failed to write operation audit log")
            finally:
                queue.task_done()


async def _record_operation_audit(event: OperationAuditEvent) -> None:
    """持久化审计事件 — 通过事件总线分发，模块自行订阅处理。"""
    await emit("on_audit_event", event=event)


async def _write_outbox(event: OperationAuditEvent) -> bool:
    try:
        from app.modules.sys.audit.outbox import enqueue_outbox

        await enqueue_outbox(event)
        return True
    except Exception:
        logger.warning("Failed to write audit outbox", exc_info=True)
        return False


async def _drain_outbox_into(queue: asyncio.Queue[OperationAuditEvent]) -> None:
    try:
        from app.modules.sys.audit.outbox import claim_pending_outbox

        events = await claim_pending_outbox(limit=50)
        for event, mark_done in events:
            try:
                await queue.put(event)
                await mark_done()
            except Exception:
                logger.warning("Failed to re-queue outbox audit event", exc_info=True)
                break
    except Exception:
        logger.debug("Audit outbox drain error", exc_info=True)


operation_audit_queue = OperationAuditQueue()


async def start_operation_audit_queue() -> None:
    await operation_audit_queue.start()


async def stop_operation_audit_queue() -> None:
    await operation_audit_queue.stop()
