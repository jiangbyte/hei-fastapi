""" Author: Charlie

文件引擎（DEFAULT_FILE_ENGINE）与 StorageProvider / sys_config 键前缀映射。
"""

from __future__ import annotations

from app.core.config.enums import StorageProvider

# DEFAULT_FILE_ENGINE 取值 → provider
FILE_ENGINE_TO_PROVIDER: dict[str, StorageProvider] = {
    "LOCAL": StorageProvider.LOCAL,
    "MINIO": StorageProvider.MINIO,
    "RUSTFS": StorageProvider.RUSTFS,
    "ALIYUN": StorageProvider.OSS,
    "TENCENT": StorageProvider.S3,
}

PROVIDER_TO_FILE_ENGINE: dict[str, str] = {
    StorageProvider.LOCAL.value: "LOCAL",
    StorageProvider.MINIO.value: "MINIO",
    StorageProvider.RUSTFS.value: "RUSTFS",
    StorageProvider.OSS.value: "ALIYUN",
    StorageProvider.S3.value: "TENCENT",
}

# provider → sys_config 键前缀（STORAGE_{ENGINE}_*）
PROVIDER_TO_KEY_PREFIX: dict[StorageProvider, str] = {
    StorageProvider.LOCAL: "STORAGE_LOCAL",
    StorageProvider.MINIO: "STORAGE_MINIO",
    StorageProvider.RUSTFS: "STORAGE_RUSTFS",
    StorageProvider.OSS: "STORAGE_ALIYUN",
    StorageProvider.S3: "STORAGE_TENCENT",
}

PROVIDER_DISPLAY_NAMES: dict[StorageProvider, str] = {
    StorageProvider.LOCAL: "本地文件",
    StorageProvider.MINIO: "MinIO",
    StorageProvider.RUSTFS: "RustFS",
    StorageProvider.OSS: "阿里云 OSS",
    StorageProvider.S3: "腾讯云 COS",
}


def engine_to_provider(engine: str | None) -> StorageProvider | None:
    if not engine:
        return None
    return FILE_ENGINE_TO_PROVIDER.get(str(engine).strip().upper())


def provider_to_engine(provider: StorageProvider | str) -> str | None:
    value = provider.value if isinstance(provider, StorageProvider) else str(provider)
    return PROVIDER_TO_FILE_ENGINE.get(value)


def config_key(provider: StorageProvider, field_suffix: str) -> str:
    return f"{PROVIDER_TO_KEY_PREFIX[provider]}_{field_suffix}"
