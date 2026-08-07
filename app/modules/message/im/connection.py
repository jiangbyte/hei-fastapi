""" Author: Charlie

WS Binary 与 TCP 的实时连接抽象。
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Protocol

from app.modules.message.im.protocol import ImCmd, encode_frame


class RealtimeConnection(Protocol):
    async def send_frame(
        self,
        cmd: ImCmd | int,
        *,
        body: bytes = b"",
        seq: int = 0,
        ack: int = 0,
        flags: int = 0,
    ) -> None: ...

    async def close(self, code: int = 0, reason: str = "") -> None: ...


@dataclass(slots=True)
class SessionContext:
    account_type: str
    account_id: str
    terminal_id: str
    channel: str  # ADMIN | PORTAL
    transport: str  # ws | tcp
    conn: RealtimeConnection
    last_active: float = 0.0
    authed: bool = True
    outbound_seq: int = 0
    last_client_seq: int = 0
    pending_acks: dict[int, bytes] = field(default_factory=dict)


class WebSocketBinaryConnection:
    def __init__(self, websocket) -> None:
        self._ws = websocket
        self._lock = asyncio.Lock()

    async def send_frame(
        self,
        cmd: ImCmd | int,
        *,
        body: bytes = b"",
        seq: int = 0,
        ack: int = 0,
        flags: int = 0,
    ) -> None:
        payload = encode_frame(cmd, body=body, seq=seq, ack=ack, flags=flags)
        async with self._lock:
            await self._ws.send(payload)

    async def close(self, code: int = 0, reason: str = "") -> None:
        try:
            await self._ws.close(code=code or 1000, reason=reason or "")
        except Exception:
            pass


class TcpBinaryConnection:
    def __init__(self, writer: asyncio.StreamWriter) -> None:
        self._writer = writer
        self._lock = asyncio.Lock()

    async def send_frame(
        self,
        cmd: ImCmd | int,
        *,
        body: bytes = b"",
        seq: int = 0,
        ack: int = 0,
        flags: int = 0,
    ) -> None:
        payload = encode_frame(cmd, body=body, seq=seq, ack=ack, flags=flags)
        async with self._lock:
            self._writer.write(payload)
            await self._writer.drain()

    async def close(self, code: int = 0, reason: str = "") -> None:
        try:
            self._writer.close()
            await self._writer.wait_closed()
        except Exception:
            pass
