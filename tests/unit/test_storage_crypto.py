""" Author: Charlie

存储密钥加密须对 AK/SK 列使用 Fernet。
"""
import pytest
from cryptography.fernet import Fernet

from app.core.config import crypto as crypto_mod
from app.core.config.settings import settings
from app.core.secrets.backend import clear_secrets_backend_cache


@pytest.fixture()
def fernet_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setattr(settings.app, "config_crypto_key", key)
    monkeypatch.setattr(settings.secrets, "backend", "fernet")
    clear_secrets_backend_cache()
    yield key
    clear_secrets_backend_cache()


def test_storage_encrypt_decrypt_roundtrip(fernet_key):
    plain = "AKIA_TEST_SECRET"
    enc = crypto_mod.encrypt_storage_value("secret_key", plain)
    assert enc is not None
    assert enc != plain
    assert crypto_mod.decrypt_storage_value("secret_key", enc) == plain


def test_storage_encrypt_requires_crypto_key(monkeypatch):
    clear_secrets_backend_cache()
    monkeypatch.setattr(settings.app, "config_crypto_key", "")
    monkeypatch.setattr(settings.secrets, "backend", "fernet")
    with pytest.raises(RuntimeError, match="config_crypto_key"):
        crypto_mod.encrypt_storage_value("access_key", "plain")
    clear_secrets_backend_cache()


def test_non_sensitive_storage_column_passthrough(fernet_key):
    assert crypto_mod.encrypt_storage_value("bucket", "my-bucket") == "my-bucket"
