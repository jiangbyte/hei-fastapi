""" Author: Charlie

IM 二进制协议编解码单元测试。
"""
import pytest

from app.modules.message.im.protocol import (
    MAGIC,
    FrameBuffer,
    FrameDecodeError,
    ImCmd,
    PushEvent,
    decode_frame,
    encode_frame,
    encode_json_body,
    try_parse_header,
)


def test_encode_decode_roundtrip():
    body = encode_json_body({"event": int(PushEvent.MESSAGE), "payload": {"id": "1"}})
    raw = encode_frame(ImCmd.PUSH, body=body, seq=42, ack=7)
    cmd, flags, seq, ack, out = decode_frame(raw)
    assert cmd == ImCmd.PUSH
    assert seq == 42
    assert ack == 7
    assert out == body
    assert raw[:2] == MAGIC.to_bytes(2, "big")


def test_frame_buffer_tcp_stream():
    f1 = encode_frame(ImCmd.PING, seq=1)
    f2 = encode_frame(ImCmd.AUTH, body=encode_json_body({"token": "t", "terminal_id": "web-1"}))
    stream = f1 + f2
    buf = FrameBuffer()
    # 在 header 中间切分
    frames = buf.feed(stream[:10])
    assert frames == []
    frames = buf.feed(stream[10:])
    assert len(frames) == 2
    assert frames[0][0] == ImCmd.PING
    assert frames[1][0] == ImCmd.AUTH


def test_bad_magic():
    raw = bytearray(encode_frame(ImCmd.PING))
    raw[0] = 0
    with pytest.raises(FrameDecodeError):
        try_parse_header(bytes(raw))
