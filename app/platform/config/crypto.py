""" Author: Charlie """

from app.platform.secrets.backend import decrypt_plaintext, encrypt_plaintext

_sensitive_keys = {
    "auth.default_password",
    "audit_alert.webhook_secret",
    "mail.password",
}

_storage_sensitive_columns = {
    "access_key",
    "secret_key",
}


def is_sensitive(config_key: str) -> bool:
    return config_key in _sensitive_keys


def encrypt_config_value(config_key: str, value: str | None) -> str | None:
    if not value or not is_sensitive(config_key):
        return value
    return encrypt_plaintext(value)


def decrypt_config_value(config_key: str, value: str | None) -> str | None:
    if not value:
        return value
    decrypted = decrypt_plaintext(value)
    # 明文行或密钥错误：非破坏性读取时原样返回。
    return decrypted if decrypted is not None else value


def is_storage_sensitive(column_name: str) -> bool:
    return column_name in _storage_sensitive_columns


def encrypt_storage_value(column_name: str, value: str | None) -> str | None:
    """加密存储 AK/SK。需要 secrets 后端（Fernet 环境变量或 Vault）。"""
    if not value or not is_storage_sensitive(column_name):
        return value
    return encrypt_plaintext(value)


def decrypt_storage_value(column_name: str, value: str | None) -> str | None:
    if not value:
        return value
    if not is_storage_sensitive(column_name):
        return value
    decrypted = decrypt_plaintext(value)
    # 轮换前仍为明文行：原样返回。
    return decrypted if decrypted is not None else value


def encrypt_secret(value: str) -> str:
    """加密任意密钥（如 MFA TOTP 种子）。"""
    return encrypt_plaintext(value)


def decrypt_secret(value: str) -> str | None:
    return decrypt_plaintext(value)
