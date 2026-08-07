""" Author: Charlie

ImSessionRegistry kick 与本地 fanout。
"""
import pytest

from app.modules.message.im.connection import SessionContext
from app.modules.message.im.protocol import ImCmd, encode_json_body
from app.modules.message.im.registry import ImSessionRegistry


class FakeConn:
    def __init__(self):
        self.frames = []
        self.closed = False

    async def send_frame(self, cmd, *, body=b"", seq=0, ack=0, flags=0):
        self.frames.append((cmd, body, seq, ack))

    async def close(self, code=0, reason=""):
        self.closed = True


@pytest.mark.asyncio
async def test_same_terminal_kick():
    reg = ImSessionRegistry()
    c1 = FakeConn()
    c2 = FakeConn()
    s1 = SessionContext(
        account_type="ADMIN",
        account_id="a1",
        terminal_id="web-1",
        channel="ADMIN",
        transport="ws",
        conn=c1,
    )
    s2 = SessionContext(
        account_type="ADMIN",
        account_id="a1",
        terminal_id="web-1",
        channel="ADMIN",
        transport="tcp",
        conn=c2,
    )
    await reg.register(s1)
    await reg.register(s2)
    assert c1.closed is True
    assert any(f[0] == ImCmd.KICK for f in c1.frames)
    assert reg.list_user_sessions("ADMIN", "a1")[0].conn is c2


@pytest.mark.asyncio
async def test_send_to_user_local():
    reg = ImSessionRegistry()
    c1 = FakeConn()
    c2 = FakeConn()
    await reg.register(
        SessionContext(
            account_type="PORTAL",
            account_id="u1",
            terminal_id="t1",
            channel="PORTAL",
            transport="ws",
            conn=c1,
        )
    )
    await reg.register(
        SessionContext(
            account_type="PORTAL",
            account_id="u1",
            terminal_id="t2",
            channel="PORTAL",
            transport="tcp",
            conn=c2,
        )
    )
    body = encode_json_body({"ok": True})
    n = await reg.send_to_user_local("PORTAL", "u1", ImCmd.PUSH, body, seq=3)
    assert n == 2
    assert c1.frames[-1][0] == ImCmd.PUSH
    assert c2.frames[-1][2] == 3
