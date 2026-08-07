""" Author: Charlie

TOTP MFA 辅助函数。
"""
import pyotp

from app.modules.auth.mfa import (
    consume_backup_code,
    generate_backup_codes,
    hash_backup_codes,
    verify_totp,
)


def test_verify_totp_window():
    secret = pyotp.random_base32()
    code = pyotp.TOTP(secret).now()
    assert verify_totp(secret, code)


def test_backup_code_consume_once():
    codes = generate_backup_codes(2)
    stored = hash_backup_codes(codes)
    updated = consume_backup_code(stored, codes[0])
    assert updated is not None
    assert consume_backup_code(updated, codes[0]) is None
    assert consume_backup_code(updated, codes[1]) is not None
