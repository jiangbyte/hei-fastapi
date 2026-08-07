""" Author: Charlie

业务推送路由：本地注册表 + Redis 扇出 + 离线队列。
"""
from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from app.modules.message.im.ack import ack_tracker
from app.modules.message.im.config import ImSettings
from app.modules.message.im.protocol import ImCmd, PushEvent, encode_json_body
from app.modules.message.im.registry import registry
from app.modules.message.offline.model import MsgOfflineQueue
from app.platform.db.session import get_session_factory
from app.platform.module.config_loader import get_module_config

logger = logging.getLogger(__name__)


class ImRouter:
    """向在线用户推送业务事件；必要时写入离线队列。"""

    def _settings(self) -> ImSettings:
        cfg = get_module_config("message.im")
        return cfg if isinstance(cfg, ImSettings) else ImSettings()

    async def push(
        self,
        account_type: str,
        account_id: str,
        event: PushEvent,
        payload: dict[str, Any],
        *,
        message_id: str | None = None,
        conversation_id: str | None = None,
        enqueue_offline_if_absent: bool = True,
    ) -> None:
        seq = await registry.next_seq()
        body = encode_json_body({"event": int(event), "payload": payload})

        sessions = registry.list_user_sessions(account_type, account_id)
        for session in sessions:
            try:
                await session.conn.send_frame(ImCmd.PUSH, body=body, seq=seq)
                ack_tracker.track(session, seq, body)
            except Exception:
                logger.debug("local push failed", exc_info=True)

        if await registry.has_remote_instances(account_type, account_id):
            await registry.publish_raw(
                account_type,
                account_id,
                {
                    "cmd": int(ImCmd.PUSH),
                    "seq": seq,
                    "body": body.decode("latin1"),
                    "origin": registry.instance_id,
                },
            )

        if not enqueue_offline_if_absent:
            return

        online = await registry.is_globally_online(account_type, account_id)
        if online:
            return

        await self.enqueue_offline(
            account_type=account_type,
            account_id=account_id,
            event=event,
            payload=payload,
            message_id=message_id or "",
            conversation_id=conversation_id or "",
        )

    async def push_many(
        self,
        targets: list[tuple[str, str]],
        event: PushEvent,
        payload: dict[str, Any],
        *,
        message_id: str | None = None,
        conversation_id: str | None = None,
        skip: tuple[str, str] | None = None,
        enqueue_offline_if_absent: bool = True,
    ) -> None:
        cfg = self._settings()
        sem = asyncio.Semaphore(cfg.fanout_concurrency)

        async def _one(account_type: str, account_id: str) -> None:
            if skip and (account_type, account_id) == skip:
                return
            async with sem:
                await self.push(
                    account_type,
                    account_id,
                    event,
                    payload,
                    message_id=message_id,
                    conversation_id=conversation_id,
                    enqueue_offline_if_absent=enqueue_offline_if_absent,
                )

        await asyncio.gather(
            *[_one(t, i) for t, i in targets],
            return_exceptions=True,
        )

    async def enqueue_offline(
        self,
        *,
        account_type: str,
        account_id: str,
        event: PushEvent,
        payload: dict[str, Any],
        message_id: str = "",
        conversation_id: str = "",
    ) -> None:
        try:
            async with get_session_factory()() as db:
                row = MsgOfflineQueue(
                    message_id=message_id or "0",
                    conversation_id=conversation_id or "0",
                    target_account_type=account_type,
                    target_account_id=account_id,
                    event_type=event.name,
                    event_payload={"event": int(event), "payload": payload},
                    status="PENDING",
                    created_at=datetime.now(UTC),
                )
                db.add(row)
                await db.commit()
        except Exception:
            logger.warning(
                "offline enqueue failed for %s/%s",
                account_type,
                account_id,
                exc_info=True,
            )


im_router = ImRouter()
