"""WebSocket handler - auth, heartbeat, event routing."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import AuthenticationError
from app.core.security.session import session_store as redis_session_store
from app.platform.db.session import get_session_factory
from app.modules.message.terminal.repository import MsgTerminalRepository
from app.modules.message.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton manager — Redis 在进程启动后由 ConnectionManager 懒加载绑定
manager = ConnectionManager(redis_client=None)

HEARTBEAT_INTERVAL = 30  # server sends pong every 30s
HEARTBEAT_TIMEOUT = 90   # disconnect if no message for 90s


async def auth_token(token: str) -> tuple[str, str, str] | None:
    """Validate token, return (account_type, account_id, terminal_id) or None."""
    try:
        session = await redis_session_store.get(token.strip())
        if session is None:
            return None
        account_type = str(session.account_type)
        account_id = session.account_id
        return (account_type, account_id, token[:12])
    except Exception:
        return None


@router.websocket("/message/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint. Token is required in query string."""
    auth_result = await auth_token(token)
    if auth_result is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    account_type, account_id, terminal_id = auth_result
    await manager.connect(account_type, account_id, terminal_id, websocket)

    try:
        await _handle_messages(websocket, account_type, account_id, terminal_id)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(account_type, account_id, terminal_id)
        await _set_offline(account_type, account_id, terminal_id)


async def _handle_messages(websocket: WebSocket, account_type: str, account_id: str, terminal_id: str) -> None:
    """Main loop: read incoming WS messages with heartbeat timeout."""
    last_activity = datetime.now(timezone.utc)

    async def heartbeat():
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            elapsed = (datetime.now(timezone.utc) - last_activity).total_seconds()
            if elapsed > HEARTBEAT_TIMEOUT:
                logger.info("WS heartbeat timeout for %s/%s terminal=%s", account_type, account_id, terminal_id)
                await websocket.close(code=4000)
                return
            try:
                await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                return

    hb_task = asyncio.create_task(heartbeat())

    try:
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=HEARTBEAT_TIMEOUT)
            last_activity = datetime.now(timezone.utc)
            try:
                msg = json.loads(data)
                await _process_message(msg, account_type, account_id, terminal_id)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "data": {"message": "Invalid JSON"}}))
    except asyncio.TimeoutError:
        logger.info("WS timeout for %s/%s terminal=%s", account_type, account_id, terminal_id)
    finally:
        hb_task.cancel()


async def _process_message(msg: dict, account_type: str, account_id: str, terminal_id: str) -> None:
    """Route incoming WS messages to handlers."""
    msg_type = msg.get("type", "")

    if msg_type == "ping":
        await manager.touch_online(account_type, account_id)
        await manager.send_to_user(account_type, account_id, {"type": "pong"})

    elif msg_type == "read_conversation":
        conversation_id = msg.get("data", {}).get("conversation_id")
        last_read_message_id = msg.get("data", {}).get("last_read_message_id")
        if conversation_id and last_read_message_id:
            from app.platform.db.session import get_session_factory
            async with get_session_factory()() as db:
                from app.modules.message.message.repository import MessageRepository
                repo = MessageRepository(db)
                await repo.mark_read(conversation_id, account_type, account_id, last_read_message_id, terminal_id)
                # 同时重置会话成员的未读计数
                from app.modules.message.conversation.repository import MsgConversationRepository
                await MsgConversationRepository(db).reset_unread(conversation_id, account_type, account_id)
                await db.commit()

    elif msg_type == "typing_start":
        conversation_id = msg.get("data", {}).get("conversation_id")
        if conversation_id:
            _broadcast_typing(conversation_id, account_type, account_id, terminal_id, True)

    elif msg_type == "typing_end":
        conversation_id = msg.get("data", {}).get("conversation_id")
        if conversation_id:
            _broadcast_typing(conversation_id, account_type, account_id, terminal_id, False)

    elif msg_type == "pull_offline":
        await _send_offline_messages(account_type, account_id)


async def _broadcast_typing(conversation_id: str, account_type: str, account_id: str,
                            terminal_id: str, is_typing: bool) -> None:
    """Broadcast typing status to all members of the conversation (local + cross-worker via Redis)."""
    from app.platform.db.session import get_session_factory
    async with get_session_factory()() as db:
        from app.modules.message.conversation.repository import MsgConversationRepository
        members = await MsgConversationRepository(db).list_members(conversation_id)
        for member in members:
            if member.account_type == account_type and member.account_id == account_id:
                continue
            await manager.route_to_user(member.account_type, member.account_id, {
                "type": "typing",
                "data": {
                    "conversation_id": conversation_id,
                    "account_type": account_type,
                    "account_id": account_id,
                    "is_typing": is_typing,
                },
            })


async def _send_offline_messages(account_type: str, account_id: str) -> None:
    """Pull and deliver pending offline messages for this user."""
    from app.platform.db.session import get_session_factory
    try:
        async with get_session_factory()() as db:
            from sqlalchemy import select
            from app.modules.message.message.model import MsgMessage
            from app.modules.message.offline.model import MsgOfflineQueue

            stmt = select(MsgOfflineQueue).where(
                MsgOfflineQueue.target_account_type == account_type,
                MsgOfflineQueue.target_account_id == account_id,
                MsgOfflineQueue.status == "PENDING",
            ).order_by(MsgOfflineQueue.created_at.asc()).limit(100)

            items = list((await db.execute(stmt)).scalars().all())
            if not items:
                return

            messages: list[dict] = []
            for item in items:
                if item.event_type == "NEW_MESSAGE":
                    msg = await db.get(MsgMessage, item.message_id)
                    if msg and not msg.is_revoked:
                        # event_payload 格式: {"type": "new_message", "data": {完整消息schema}}
                        # 提取 data 作为消息体直接返回给前端
                        event_data = (item.event_payload or {}).get("data") or {}
                        event_data["__offline_message_id"] = item.id
                        messages.append(event_data)

            if messages:
                await manager.send_to_user(account_type, account_id, {
                    "type": "offline_messages",
                    "data": {"messages": messages},
                })

            # Mark delivered
            now = datetime.now(timezone.utc)
            for item in items:
                item.status = "DELIVERED"
                item.delivered_at = now
            await db.commit()
    except Exception:
        logger.warning(
            "pull_offline failed for %s/%s (table missing or DB error)",
            account_type,
            account_id,
            exc_info=True,
        )


async def _set_offline(account_type: str, account_id: str, terminal_id: str) -> None:
    """Update terminal to offline when WS disconnects."""
    from app.platform.db.session import get_session_factory
    async with get_session_factory()() as db:
        repo = MsgTerminalRepository(db)
        terminal = await repo.find_by_device(account_type, account_id, "WEB", terminal_id)
        if terminal:
            await repo.set_online(terminal.id, False)
            await db.commit()


async def on_new_message(account_type: str, account_id: str, message: dict) -> None:
    """Called by message service to notify a user's WS connections across all workers."""
    await manager.route_to_user(account_type, account_id, message)
