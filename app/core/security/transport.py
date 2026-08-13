""" Author: Charlie

认证传输层安全：图形验证码与一次性 RSA 密码传输密钥。

密码在客户端用公钥加密后经 HTTP 传输，服务端用临时私钥解密，
避免明文密码出现在日志与链路上。
"""

import base64
import html
import secrets
import struct
import zlib
from uuid import uuid4

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from pydantic import Field

from app.core.config.settings import settings
from app.core.exceptions.business import BusinessError
from app.core.response.schema import ApiResponse
from app.core.schema.base import ApiSchema
from app.core.security.password import hash_password, verify_password
from app.platform.cache.keys import captcha_key, password_crypto_key
from app.platform.cache.redis import get_redis


class CaptchaResponse(ApiSchema):
    """图形验证码响应：验证码 ID 与图片内容。"""

    captcha_id: str
    image_base64: str
    image_type: str = "image/svg+xml"


class PasswordKeyResponse(ApiSchema):
    """一次性密码传输密钥响应：密钥 ID 与公钥。"""

    key_id: str
    public_key: str


class CaptchaMixin(ApiSchema):
    """需要携带图形验证码的请求参数。"""

    captcha_id: str = Field(min_length=1, max_length=64)
    captcha_value: str = Field(min_length=1, max_length=16)


class PasswordKeyMixin(ApiSchema):
    """需要携带密码传输密钥 ID 的请求参数。"""

    password_key_id: str = Field(min_length=1, max_length=64)


CaptchaApiResponse = ApiResponse[CaptchaResponse]
PasswordKeyApiResponse = ApiResponse[PasswordKeyResponse]

# 去除易混淆字符（0/O、1/I/L）的验证码字母表。
CAPTCHA_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


async def create_captcha(image_format: str = "svg") -> CaptchaResponse:
    """生成图形验证码，并将明文哈希后写入 Redis。"""
    value = "".join(secrets.choice(CAPTCHA_ALPHABET) for _ in range(4))
    captcha_id = uuid4().hex
    redis = _required_redis("Redis is required for captcha")
    await redis.setex(
        captcha_key(captcha_id),
        settings.auth.captcha_ttl_seconds,
        hash_password(value.lower()),
    )
    if image_format == "png":
        return CaptchaResponse(
            captcha_id=captcha_id,
            image_base64=_captcha_png_base64(value),
            image_type="image/png",
        )
    return CaptchaResponse(captcha_id=captcha_id, image_base64=_captcha_svg_base64(value))


async def verify_captcha(captcha_id: str, captcha_value: str) -> None:
    """校验并一次性消费验证码（无论对错都删除，防止重放）。"""
    redis = _required_redis("Redis is required for captcha")
    key = captcha_key(captcha_id)
    raw = await redis.get(key)
    await redis.delete(key)
    raw_text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    if not raw_text or not verify_password(captcha_value.strip().lower(), str(raw_text)):
        raise BusinessError("Invalid or expired captcha")


async def create_password_key() -> PasswordKeyResponse:
    """生成一次性 RSA 密钥对，私钥存入 Redis，公钥下发给客户端。"""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_der = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    key_id = uuid4().hex
    redis = _required_redis("Redis is required for password encryption")
    await redis.setex(
        password_crypto_key(key_id),
        settings.auth.password_crypto_key_ttl_seconds,
        private_pem,
    )
    return PasswordKeyResponse(
        key_id=key_id,
        public_key=base64.b64encode(public_der).decode("ascii"),
    )


async def decrypt_passwords(
    password_key_id: str,
    *encrypted_values: str | None,
) -> list[str | None]:
    """用一次性私钥批量解密传输层加密的密码，解密后即删除私钥。"""
    redis = _required_redis("Redis is required for password encryption")
    key = password_crypto_key(password_key_id)
    raw = await redis.get(key)
    raw_text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    if not raw_text:
        raise BusinessError("Invalid or expired password encryption key")
    try:
        private_key = serialization.load_pem_private_key(
            str(raw_text).encode("utf-8"),
            password=None,
        )
        result: list[str | None] = []
        for value in encrypted_values:
            result.append(_decrypt_password(private_key, value) if value else None)
        return result
    finally:
        await redis.delete(key)


async def decrypt_password(password_key_id: str, encrypted_value: str | None) -> str:
    """解密单个传输层加密密码（缺失时返回空字符串）。"""
    return (await decrypt_passwords(password_key_id, encrypted_value))[0] or ""


def _decrypt_password(private_key, encrypted_value: str) -> str:
    """用 RSA-OAEP 解密单个密文，失败转为统一业务错误。"""
    try:
        ciphertext = base64.b64decode(encrypted_value)
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return plaintext.decode("utf-8")
    except Exception as exc:
        raise BusinessError("Invalid encrypted password") from exc


def _captcha_svg_base64(value: str) -> str:
    """渲染带噪点与随机旋转的 SVG 验证码并编码为 base64。"""
    escaped = html.escape(value)
    noise = "\n".join(
        f'<line x1="{secrets.randbelow(140)}" y1="{secrets.randbelow(44)}" '
        f'x2="{secrets.randbelow(140)}" y2="{secrets.randbelow(44)}" '
        f'stroke="#94a3b8" stroke-width="1" opacity="0.45" />'
        for _ in range(6)
    )
    text_nodes = "\n".join(
        f'<text x="{22 + index * 26}" y="{29 + secrets.randbelow(5)}" '
        f'font-size="24" font-family="Arial, sans-serif" font-weight="700" '
        f'fill="#0f172a" transform="rotate({secrets.randbelow(21) - 10} {22 + index * 26} 25)">'
        f"{html.escape(char)}</text>"
        for index, char in enumerate(escaped)
    )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="140" height="44" '
        'viewBox="0 0 140 44">'
        '<rect width="140" height="44" rx="6" fill="#f8fafc"/>'
        f"{noise}{text_nodes}"
        "</svg>"
    )
    return base64.b64encode(svg.encode("utf-8")).decode("ascii")


# 每个字符的 7x5 点阵字模，用于 PNG 验证码的逐像素绘制。
CAPTCHA_GLYPHS: dict[str, tuple[str, ...]] = {
    "2": ("11110", "00001", "00001", "11110", "10000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("10001", "10001", "10001", "11111", "00001", "00001", "00001"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01111", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "11110"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10011", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "01010", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}


def _captcha_png_base64(value: str) -> str:
    """手工构造 PNG（IHDR/IDAT/IEND）验证码并编码为 base64。"""
    width = 140
    height = 44
    pixels = bytearray([248, 250, 252] * width * height)

    for _ in range(6):
        _draw_line(
            pixels,
            width,
            height,
            secrets.randbelow(width),
            secrets.randbelow(height),
            secrets.randbelow(width),
            secrets.randbelow(height),
            (148, 163, 184),
        )

    for index, char in enumerate(value):
        _draw_glyph(
            pixels,
            width,
            height,
            char,
            18 + index * 28 + secrets.randbelow(3),
            8 + secrets.randbelow(4),
            4,
            (15, 23, 42),
        )

    raw = b"".join(
        b"\x00" + bytes(pixels[row * width * 3 : (row + 1) * width * 3]) for row in range(height)
    )
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw, 9))
        + _png_chunk(b"IEND", b"")
    )
    return base64.b64encode(png).decode("ascii")


def _draw_glyph(
    pixels: bytearray,
    width: int,
    height: int,
    char: str,
    x: int,
    y: int,
    scale: int,
    color: tuple[int, int, int],
) -> None:
    """在像素缓冲上按比例绘制单个字符字模。"""
    glyph = CAPTCHA_GLYPHS.get(char)
    if not glyph:
        return
    for row_index, row in enumerate(glyph):
        for column_index, enabled in enumerate(row):
            if enabled != "1":
                continue
            for dy in range(scale):
                for dx in range(scale):
                    _set_pixel(
                        pixels,
                        width,
                        height,
                        x + column_index * scale + dx,
                        y + row_index * scale + dy,
                        color,
                    )


def _draw_line(
    pixels: bytearray,
    width: int,
    height: int,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: tuple[int, int, int],
) -> None:
    """用 Bresenham 直线算法在像素缓冲上绘制噪点线段。"""
    dx = abs(x2 - x1)
    dy = -abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    error = dx + dy
    while True:
        _set_pixel(pixels, width, height, x1, y1, color)
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * error
        if e2 >= dy:
            error += dy
            x1 += sx
        if e2 <= dx:
            error += dx
            y1 += sy


def _set_pixel(
    pixels: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    color: tuple[int, int, int],
) -> None:
    """越界安全地在像素缓冲上写入单个 RGB 像素。"""
    if x < 0 or x >= width or y < 0 or y >= height:
        return
    offset = (y * width + x) * 3
    pixels[offset : offset + 3] = bytes(color)


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """构造带长度与 CRC32 校验的 PNG chunk。"""
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def _required_redis(message: str):
    """获取 Redis 客户端，未初始化时抛出统一业务错误。"""
    redis = get_redis()
    if redis is None:
        raise BusinessError(message)
    return redis
