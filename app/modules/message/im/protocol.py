""" Author: Charlie

IM 二进制协议：帧布局、cmd 与 push-event 枚举。
"""
from __future__ import annotations

import struct
from enum import IntEnum
from typing import Any

import orjson

MAGIC = 0x4849  # "HI"
VERSION = 1
HEADER_SIZE = 26  # magic(2)+ver(1)+cmd(2)+flags(1)+seq(8)+ack(8)+len(4)
HEADER_STRUCT = struct.Struct(">HBHBQQI")
MAX_FRAME_BODY = 1024 * 1024


class ImCmd(IntEnum):
    AUTH = 1
    AUTH_OK = 2
    AUTH_FAIL = 3
    PING = 4
    PONG = 5
    ACK = 6
    KICK = 7
    PUSH = 8
    PULL_OFFLINE = 9
    OFFLINE_BATCH = 10
    READ_CONVERSATION = 11
    TYPING = 12


class PushEvent(IntEnum):
    MESSAGE = 1
    NOTIFICATION = 2
    FRIEND_REQUEST = 3
    GROUP_JOIN_REQUEST = 4
    GROUP_JOIN_HANDLED = 5
    MESSAGE_REVOKED = 6


class FrameDecodeError(ValueError):
    pass


def encode_frame(
    cmd: ImCmd | int,
    *,
    body: bytes = b"",
    seq: int = 0,
    ack: int = 0,
    flags: int = 0,
    ver: int = VERSION,
) -> bytes:
    if len(body) > MAX_FRAME_BODY:
        raise ValueError("frame body too large")
    header = HEADER_STRUCT.pack(MAGIC, ver, int(cmd), flags & 0xFF, seq, ack, len(body))
    return header + body


def encode_json_body(payload: dict[str, Any] | list[Any]) -> bytes:
    return orjson.dumps(payload)


def decode_json_body(body: bytes) -> Any:
    if not body:
        return {}
    return orjson.loads(body)


def try_parse_header(buffer: bytes) -> tuple[int, int, int, int, int, int] | None:
    """返回 (cmd, flags, seq, ack, body_len, total_frame_len)，不完整时返回 None。"""
    if len(buffer) < HEADER_SIZE:
        return None
    magic, ver, cmd, flags, seq, ack, body_len = HEADER_STRUCT.unpack_from(buffer, 0)
    if magic != MAGIC:
        raise FrameDecodeError(f"invalid magic: 0x{magic:04x}")
    if ver != VERSION:
        raise FrameDecodeError(f"unsupported version: {ver}")
    if body_len > MAX_FRAME_BODY:
        raise FrameDecodeError("body length exceeds limit")
    total = HEADER_SIZE + body_len
    if len(buffer) < total:
        return None
    return cmd, flags, seq, ack, body_len, total


def decode_frame(data: bytes) -> tuple[ImCmd, int, int, int, bytes]:
    parsed = try_parse_header(data)
    if parsed is None:
        raise FrameDecodeError("incomplete frame")
    cmd, flags, seq, ack, body_len, total = parsed
    if len(data) != total:
        # WS 仅允许精确帧；TCP 流使用 try_parse + slice
        if len(data) < total:
            raise FrameDecodeError("incomplete frame")
    body = data[HEADER_SIZE : HEADER_SIZE + body_len]
    try:
        return ImCmd(cmd), flags, seq, ack, body
    except ValueError as exc:
        raise FrameDecodeError(f"unknown cmd: {cmd}") from exc


class FrameBuffer:
    """累积 TCP 字节并产出完整帧。"""

    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, data: bytes) -> list[tuple[ImCmd, int, int, int, bytes]]:
        self._buf.extend(data)
        frames: list[tuple[ImCmd, int, int, int, bytes]] = []
        while True:
            parsed = try_parse_header(self._buf)
            if parsed is None:
                break
            cmd_i, flags, seq, ack, body_len, total = parsed
            raw = bytes(self._buf[:total])
            del self._buf[:total]
            try:
                cmd = ImCmd(cmd_i)
            except ValueError as exc:
                raise FrameDecodeError(f"unknown cmd: {cmd_i}") from exc
            body = raw[HEADER_SIZE : HEADER_SIZE + body_len]
            frames.append((cmd, flags, seq, ack, body))
        return frames
