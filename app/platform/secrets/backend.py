""" Author: Charlie

可插拔 secrets 后端（Fernet 环境变量密钥或 Vault 托管 Fernet 密钥）。
"""
from __future__ import annotations

from functools import lru_cache
from typing import Protocol

import httpx
from cryptography.fernet import Fernet

from app.core.config.settings import settings


class SecretsBackend(Protocol):
    def encrypt(self, plaintext: str) -> str: ...

    def decrypt(self, ciphertext: str) -> str | None: ...


class FernetEnvBackend:
    def __init__(self, key: str) -> None:
        key = (key or "").strip()
        if not key:
            raise RuntimeError("config_crypto_key is not configured")
        self._fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str | None:
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception:
            return None


class VaultKvBackend:
    """从 HashiCorp Vault KV v2 加载 Fernet 密钥；不可达时 fail-closed。"""

    def __init__(
        self,
        *,
        addr: str,
        token: str,
        mount: str,
        path: str,
        key_field: str = "fernet_key",
        timeout_seconds: float = 5.0,
    ) -> None:
        self._addr = addr.rstrip("/")
        self._token = token
        self._mount = mount.strip("/")
        self._path = path.strip("/")
        self._key_field = key_field
        self._timeout = timeout_seconds
        self._fernet: Fernet | None = None

    def _ensure_fernet(self) -> Fernet:
        if self._fernet is not None:
            return self._fernet
        url = f"{self._addr}/v1/{self._mount}/data/{self._path}"
        try:
            response = httpx.get(
                url,
                headers={"X-Vault-Token": self._token},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            data = (payload.get("data") or {}).get("data") or {}
            key = str(data.get(self._key_field) or "").strip()
        except Exception as exc:  # noqa: BLE001 — fail-closed
            raise RuntimeError(f"Vault secrets backend unavailable: {exc}") from exc
        if not key:
            raise RuntimeError(f"Vault path missing field '{self._key_field}'")
        self._fernet = Fernet(key.encode())
        return self._fernet

    def encrypt(self, plaintext: str) -> str:
        return self._ensure_fernet().encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str | None:
        try:
            return self._ensure_fernet().decrypt(ciphertext.encode()).decode()
        except Exception:
            return None


@lru_cache(maxsize=1)
def get_secrets_backend() -> SecretsBackend:
    backend = (settings.secrets.backend or "fernet").strip().lower()
    if backend == "vault":
        return VaultKvBackend(
            addr=settings.secrets.vault_addr,
            token=settings.secrets.vault_token,
            mount=settings.secrets.vault_mount,
            path=settings.secrets.vault_path,
            key_field=settings.secrets.vault_key_field,
            timeout_seconds=settings.secrets.vault_timeout_seconds,
        )
    return FernetEnvBackend(settings.app.config_crypto_key)


def clear_secrets_backend_cache() -> None:
    get_secrets_backend.cache_clear()


def encrypt_plaintext(value: str) -> str:
    return get_secrets_backend().encrypt(value)


def decrypt_plaintext(value: str) -> str | None:
    return get_secrets_backend().decrypt(value)
