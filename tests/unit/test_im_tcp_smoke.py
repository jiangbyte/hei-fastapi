""" Author: Charlie

TCP 冒烟：进程内 ImRealtimeServer 的 AUTH -> PING -> PUSH ACK 路径。
"""
from __future__ import annotations

import asyncio

import pytest

from app.modules.message.im.config import ImSettings
from app.modules.message.im.protocol import (
    FrameBuffer,
    ImCmd,
    PushEvent,
    encode_frame,
    encode_json_body,
)
from app.modules.message.im.registry import ImSessionRegistry
from app.modules.message.im.server import ImRealtimeServer


@pytest.mark.asyncio
async def test_tcp_auth_ping_push_ack(monkeypatch):
    settings = ImSettings(
        enabled=True,
        ws_host="127.0.0.1",
        ws_port=0,  # 未使用 — 已 patch start
        tcp_host="127.0.0.1",
        tcp_port=0,
        auth_timeout_seconds=5,
        idle_seconds=30,
    )

    # 隔离 registry
    import app.modules.message.im.ack as ack_mod
    import app.modules.message.im.handler as handler_mod
    import app.modules.message.im.registry as registry_mod
    import app.modules.message.im.router as router_mod
    import app.modules.message.im.server as server_mod

    test_registry = ImSessionRegistry()
    monkeypatch.setattr(registry_mod, "registry", test_registry)
    monkeypatch.setattr(server_mod, "registry", test_registry)
    monkeypatch.setattr(handler_mod, "registry", test_registry)
    monkeypatch.setattr(router_mod, "registry", test_registry)

    async def fake_auth(token: str):
        if token == "good-token":
            return ("PORTAL", "user-1")
        return None

    monkeypatch.setattr(handler_mod, "auth_token", fake_auth)
    monkeypatch.setattr("app.modules.message.im.auth.auth_token", fake_auth)

    server = ImRealtimeServer()
    monkeypatch.setattr(server, "_settings", lambda: settings)

    # 仅启动 TCP（跳过 WS，避免 CI 中端口/websockets 复杂度）
    async def start_tcp_only():
        ack_mod.ack_tracker.start()
        await server._start_tcp(settings)
        server._started = True

    await start_tcp_only()
    assert server._tcp_server is not None
    sockets = server._tcp_server.sockets
    assert sockets
    port = sockets[0].getsockname()[1]

    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    try:
        auth = encode_frame(
            ImCmd.AUTH,
            body=encode_json_body(
                {"token": "good-token", "terminal_id": "tcp-smoke-1", "channel": "portal"}
            ),
        )
        writer.write(auth)
        await writer.drain()

        # 读取 AUTH_OK
        buf = FrameBuffer()
        ok = None
        for _ in range(20):
            chunk = await asyncio.wait_for(reader.read(4096), timeout=2)
            assert chunk
            for frame in buf.feed(chunk):
                if frame[0] == ImCmd.AUTH_OK:
                    ok = frame
                    break
            if ok:
                break
        assert ok is not None

        # PING 应返回 PONG
        writer.write(encode_frame(ImCmd.PING, seq=9))
        await writer.drain()
        pong = None
        for _ in range(20):
            chunk = await asyncio.wait_for(reader.read(4096), timeout=2)
            for frame in buf.feed(chunk):
                if frame[0] == ImCmd.PONG:
                    pong = frame
                    break
            if pong:
                break
        assert pong is not None
        assert pong[3] == 9  # ack 回显 seq

        # 经 router 服务端 PUSH（使用 patched registry）
        router = router_mod.ImRouter()
        monkeypatch.setattr(router, "_settings", lambda: settings)
        await router.push(
            "PORTAL",
            "user-1",
            PushEvent.MESSAGE,
            {"id": "m1", "content": "hi"},
            enqueue_offline_if_absent=False,
        )

        push = None
        for _ in range(20):
            chunk = await asyncio.wait_for(reader.read(4096), timeout=2)
            for frame in buf.feed(chunk):
                if frame[0] == ImCmd.PUSH:
                    push = frame
                    break
            if push:
                break
        assert push is not None
        seq = push[2]
        writer.write(encode_frame(ImCmd.ACK, body=encode_json_body({"seq": seq}), ack=seq))
        await writer.drain()
        await asyncio.sleep(0.05)
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        await server.stop()
