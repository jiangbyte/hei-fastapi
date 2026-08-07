""" Author: Charlie

WS Binary 与 TCP 共用的 IM 帧处理器。
"""
from __future__ import annotations

import logging
import time
from datetime import UTC
from typing import Any

from app.modules.message.im.ack import ack_tracker
from app.modules.message.im.auth import auth_token, normalize_channel
from app.modules.message.im.connection import RealtimeConnection, SessionContext
from app.modules.message.im.protocol import (
    ImCmd,
    decode_json_body,
    encode_json_body,
)
from app.modules.message.im.registry import registry
from app.platform.db.session import get_session_factory

logger = logging.getLogger(__name__)


async def handle_authed_frame(
    session: SessionContext,
    cmd: ImCmd,
    flags: int,
    seq: int,
    ack: int,
    body: bytes,
) -> None:
    session.last_active = time.monotonic()
    if seq > 0:
        session.last_client_seq = max(session.last_client_seq, seq)
    if ack > 0:
        ack_tracker.ack(session, ack)

    await registry.touch_online(session.account_type, session.account_id)

    if cmd == ImCmd.PING:
        await session.conn.send_frame(ImCmd.PONG, ack=seq)
        return

    if cmd == ImCmd.ACK:
        payload = decode_json_body(body) if body else {}
        ack_seq = int(payload.get("seq") or ack or 0)
        if ack_seq:
            ack_tracker.ack(session, ack_seq)
        return

    if cmd == ImCmd.PONG:
        return

    if cmd == ImCmd.PULL_OFFLINE:
        await _pull_offline(session)
        return

    if cmd == ImCmd.READ_CONVERSATION:
        await _read_conversation(session, body)
        return

    if cmd == ImCmd.TYPING:
        await _typing(session, body)
        return

    logger.debug("ignored cmd=%s from %s/%s", cmd, session.account_type, session.account_id)


async def authenticate_connection(
    conn: RealtimeConnection,
    *,
    token: str | None,
    terminal_id: str | None,
    channel: str | None,
    transport: str,
) -> SessionContext | None:
    if not token or not terminal_id:
        await conn.send_frame(
            ImCmd.AUTH_FAIL,
            body=encode_json_body({"reason": "token_and_terminal_required"}),
        )
        await conn.close(4001, "auth required")
        return None

    result = await auth_token(token)
    if result is None:
        await conn.send_frame(
            ImCmd.AUTH_FAIL,
            body=encode_json_body({"reason": "invalid_token"}),
        )
        await conn.close(4001, "invalid token")
        return None

    account_type, account_id = result
    ch = normalize_channel(channel, account_type)
    session = SessionContext(
        account_type=account_type,
        account_id=account_id,
        terminal_id=terminal_id.strip(),
        channel=ch,
        transport=transport,
        conn=conn,
        last_active=time.monotonic(),
        authed=True,
    )
    await registry.register(session)
    await conn.send_frame(
        ImCmd.AUTH_OK,
        body=encode_json_body(
            {
                "account_type": account_type,
                "account_id": account_id,
                "terminal_id": session.terminal_id,
                "channel": ch,
            }
        ),
    )
    return session


async def authenticate_from_auth_frame(
    conn: RealtimeConnection,
    body: bytes,
    *,
    transport: str,
) -> SessionContext | None:
    data = decode_json_body(body) if body else {}
    if not isinstance(data, dict):
        data = {}
    return await authenticate_connection(
        conn,
        token=str(data.get("token") or ""),
        terminal_id=str(data.get("terminal_id") or data.get("terminalId") or ""),
        channel=str(data.get("channel") or data.get("account_channel") or ""),
        transport=transport,
    )


async def _pull_offline(session: SessionContext) -> None:
    from datetime import datetime

    from sqlalchemy import select

    from app.modules.message.offline.model import MsgOfflineQueue

    try:
        async with get_session_factory()() as db:
            stmt = (
                select(MsgOfflineQueue)
                .where(
                    MsgOfflineQueue.target_account_type == session.account_type,
                    MsgOfflineQueue.target_account_id == session.account_id,
                    MsgOfflineQueue.status == "PENDING",
                )
                .order_by(MsgOfflineQueue.created_at.asc())
                .limit(100)
            )
            items = list((await db.execute(stmt)).scalars().all())
            batch: list[dict[str, Any]] = []
            for item in items:
                payload = item.event_payload or {}
                entry = {
                    "event": payload.get("event"),
                    "payload": payload.get("payload") or payload,
                    "offline_id": item.id,
                }
                batch.append(entry)
            if batch:
                await session.conn.send_frame(
                    ImCmd.OFFLINE_BATCH,
                    body=encode_json_body({"items": batch}),
                )
            now = datetime.now(UTC)
            for item in items:
                item.status = "DELIVERED"
                item.delivered_at = now
            await db.commit()
    except Exception:
        logger.warning(
            "pull_offline failed for %s/%s",
            session.account_type,
            session.account_id,
            exc_info=True,
        )


async def _read_conversation(session: SessionContext, body: bytes) -> None:
    data = decode_json_body(body) if body else {}
    conversation_id = data.get("conversation_id")
    last_read_message_id = data.get("last_read_message_id")
    if not conversation_id or not last_read_message_id:
        return
    try:
        async with get_session_factory()() as db:
            from app.modules.message.conversation.repository import MsgConversationRepository
            from app.modules.message.message.repository import MessageRepository

            await MessageRepository(db).mark_read(
                conversation_id,
                session.account_type,
                session.account_id,
                last_read_message_id,
                session.terminal_id,
            )
            await MsgConversationRepository(db).reset_unread(
                conversation_id, session.account_type, session.account_id
            )
            await db.commit()
    except Exception:
        logger.warning("read_conversation failed", exc_info=True)


async def _typing(session: SessionContext, body: bytes) -> None:
    data = decode_json_body(body) if body else {}
    conversation_id = data.get("conversation_id")
    is_typing = bool(data.get("is_typing", True))
    if not conversation_id:
        return
    try:
        async with get_session_factory()() as db:
            from app.modules.message.conversation.repository import MsgConversationRepository

            members = await MsgConversationRepository(db).list_members(conversation_id)
        payload = {
            "conversation_id": conversation_id,
            "account_type": session.account_type,
            "account_id": session.account_id,
            "terminal_id": session.terminal_id,
            "is_typing": is_typing,
        }
        typing_body = encode_json_body(payload)
        for member in members:
            if (
                member.account_type == session.account_type
                and member.account_id == session.account_id
            ):
                continue
            await registry.send_to_user_local(
                member.account_type,
                member.account_id,
                ImCmd.TYPING,
                typing_body,
            )
            if await registry.has_remote_instances(member.account_type, member.account_id):
                await registry.publish_raw(
                    member.account_type,
                    member.account_id,
                    {
                        "cmd": int(ImCmd.TYPING),
                        "seq": 0,
                        "body": typing_body.decode("latin1"),
                        "origin": registry.instance_id,
                    },
                )
    except Exception:
        logger.warning("typing fanout failed", exc_info=True)
