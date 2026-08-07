""" Author: Charlie

签名文件 URL HMAC 辅助函数。
"""
import time

from app.platform.storage.signed_url import sign_object_access, verify_object_access


def test_sign_verify_ok():
    expires, sig = sign_object_access("uploads/a.png", ttl_seconds=120)
    assert verify_object_access("uploads/a.png", expires, sig) is True


def test_sign_verify_rejects_tamper():
    expires, sig = sign_object_access("uploads/a.png", ttl_seconds=120)
    assert verify_object_access("uploads/b.png", expires, sig) is False
    assert verify_object_access("uploads/a.png", expires, sig + "x") is False


def test_sign_verify_rejects_expired():
    expires, sig = sign_object_access("uploads/a.png", expires_at=int(time.time()) - 10)
    assert verify_object_access("uploads/a.png", expires, sig) is False
