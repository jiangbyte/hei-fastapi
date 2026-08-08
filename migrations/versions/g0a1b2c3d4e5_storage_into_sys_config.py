""" Author: Charlie

将 sys_storage_config 迁入 sys_config（STORAGE_* / DEFAULT_FILE_ENGINE），
并把 sys_file.storage_config_id 从雪花 ID 改为稳定 provider，最后删除专用表。
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "g0a1b2c3d4e5"
down_revision: str | Sequence[str] | None = "f9a0b1c2d3e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 8, tzinfo=UTC)
_LOG = logging.getLogger("alembic.runtime.migration")

_PROVIDER_TO_ENGINE = {
    "local": "LOCAL",
    "minio": "MINIO",
    "oss": "ALIYUN",
    "s3": "TENCENT",
}

_KNOWN_PROVIDERS = frozenset(_PROVIDER_TO_ENGINE)

_SEED_META: dict[str, tuple[str, str, int]] = {
    # config_key: (id, remark, sort_code)
    "DEFAULT_FILE_ENGINE": ("cfg_sys_01", "默认文件引擎", 1),
    "STORAGE_LOCAL_LOCAL_ROOT": ("cfg_sto_local_01", "LINUX 本地存储根目录", 10),
    "STORAGE_LOCAL_WINDOWS_ROOT": ("cfg_sto_local_02", "WINDOWS 本地存储根目录", 11),
    "STORAGE_LOCAL_PUBLIC_PATH": ("cfg_sto_local_03", "本地公开访问路径", 12),
    "STORAGE_LOCAL_BASE_URL": ("cfg_sto_local_04", "本地自定义基础 URL", 13),
    "STORAGE_MINIO_BUCKET": ("cfg_sto_minio_01", "MinIO 存储桶", 20),
    "STORAGE_MINIO_ENDPOINT": ("cfg_sto_minio_02", "MinIO 端点", 21),
    "STORAGE_MINIO_ACCESS_KEY": ("cfg_sto_minio_03", "MinIO Access Key", 22),
    "STORAGE_MINIO_SECRET_KEY": ("cfg_sto_minio_04", "MinIO Secret Key", 23),
    "STORAGE_MINIO_REGION": ("cfg_sto_minio_05", "MinIO Region", 24),
    "STORAGE_MINIO_USE_SSL": ("cfg_sto_minio_06", "MinIO 是否 SSL", 25),
    "STORAGE_MINIO_BASE_URL": ("cfg_sto_minio_07", "MinIO 自定义基础 URL", 26),
    "STORAGE_MINIO_PUBLIC_PATH": ("cfg_sto_minio_08", "MinIO 公开访问路径", 27),
    "STORAGE_ALIYUN_BUCKET": ("cfg_sto_aliyun_01", "阿里云 OSS 存储桶", 30),
    "STORAGE_ALIYUN_ENDPOINT": ("cfg_sto_aliyun_02", "阿里云 OSS 端点", 31),
    "STORAGE_ALIYUN_ACCESS_KEY": ("cfg_sto_aliyun_03", "阿里云 OSS AccessKeyId", 32),
    "STORAGE_ALIYUN_SECRET_KEY": ("cfg_sto_aliyun_04", "阿里云 OSS AccessKeySecret", 33),
    "STORAGE_ALIYUN_REGION": ("cfg_sto_aliyun_05", "阿里云 OSS Region", 34),
    "STORAGE_ALIYUN_USE_SSL": ("cfg_sto_aliyun_06", "阿里云 OSS 是否 SSL", 35),
    "STORAGE_ALIYUN_BASE_URL": ("cfg_sto_aliyun_07", "阿里云 OSS 自定义基础 URL", 36),
    "STORAGE_ALIYUN_PUBLIC_PATH": ("cfg_sto_aliyun_08", "阿里云 OSS 公开访问路径", 37),
    "STORAGE_TENCENT_BUCKET": ("cfg_sto_tencent_01", "腾讯云 COS 存储桶", 40),
    "STORAGE_TENCENT_ENDPOINT": ("cfg_sto_tencent_02", "腾讯云 COS 端点", 41),
    "STORAGE_TENCENT_ACCESS_KEY": ("cfg_sto_tencent_03", "腾讯云 COS SecretId", 42),
    "STORAGE_TENCENT_SECRET_KEY": ("cfg_sto_tencent_04", "腾讯云 COS SecretKey", 43),
    "STORAGE_TENCENT_REGION": ("cfg_sto_tencent_05", "腾讯云 COS Region", 44),
    "STORAGE_TENCENT_USE_SSL": ("cfg_sto_tencent_06", "腾讯云 COS 是否 SSL", 45),
    "STORAGE_TENCENT_BASE_URL": ("cfg_sto_tencent_07", "腾讯云 COS 自定义基础 URL", 46),
    "STORAGE_TENCENT_PUBLIC_PATH": ("cfg_sto_tencent_08", "腾讯云 COS 公开访问路径", 47),
}


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT id, name, provider, bucket, endpoint, access_key, secret_key, region,
                   use_ssl, base_url, public_path, local_root, windows_root, is_default,
                   sort_code
            FROM sys_storage_config
            ORDER BY is_default DESC, sort_code ASC, name ASC
            """
        )
    ).mappings().all()

    by_provider: dict[str, dict] = {}
    default_provider: str | None = None
    for row in rows:
        provider = str(row["provider"] or "").lower()
        if provider not in _KNOWN_PROVIDERS:
            _LOG.warning("skip unknown storage provider %r (id=%s)", provider, row["id"])
            continue
        if provider not in by_provider:
            by_provider[provider] = dict(row)
        if row["is_default"] and default_provider is None:
            default_provider = provider

    if default_provider is None and by_provider:
        # 无 is_default 时取排序第一行对应 provider
        first = next(iter(by_provider))
        default_provider = first

    from app.platform.config.crypto import (
        decrypt_storage_value,
        encrypt_config_value,
    )

    kv: dict[str, str] = {}
    if default_provider:
        kv["DEFAULT_FILE_ENGINE"] = _PROVIDER_TO_ENGINE[default_provider]

    for provider, row in by_provider.items():
        engine = _PROVIDER_TO_ENGINE[provider]
        prefix = f"STORAGE_{engine}"
        if provider == "local":
            kv[f"{prefix}_LOCAL_ROOT"] = row["local_root"] or ".runtime/storage"
            kv[f"{prefix}_WINDOWS_ROOT"] = row["windows_root"] or ""
            kv[f"{prefix}_PUBLIC_PATH"] = row["public_path"] or "/api/v1/files"
            kv[f"{prefix}_BASE_URL"] = row["base_url"] or ""
            continue
        access = decrypt_storage_value("access_key", row["access_key"]) or ""
        secret = decrypt_storage_value("secret_key", row["secret_key"]) or ""
        kv[f"{prefix}_BUCKET"] = row["bucket"] or ""
        kv[f"{prefix}_ENDPOINT"] = row["endpoint"] or ""
        kv[f"{prefix}_ACCESS_KEY"] = encrypt_config_value(f"{prefix}_ACCESS_KEY", access) or ""
        kv[f"{prefix}_SECRET_KEY"] = encrypt_config_value(f"{prefix}_SECRET_KEY", secret) or ""
        kv[f"{prefix}_REGION"] = row["region"] or ""
        kv[f"{prefix}_USE_SSL"] = "TRUE" if row["use_ssl"] else "FALSE"
        kv[f"{prefix}_BASE_URL"] = row["base_url"] or ""
        kv[f"{prefix}_PUBLIC_PATH"] = row["public_path"] or "/api/v1/files"

    # 无表数据时仍保证 DEFAULT_FILE_ENGINE 存在且 category=STORAGE
    if "DEFAULT_FILE_ENGINE" not in kv:
        existing = conn.execute(
            sa.text("SELECT config_value FROM sys_config WHERE config_key = 'DEFAULT_FILE_ENGINE'")
        ).scalar()
        kv["DEFAULT_FILE_ENGINE"] = (existing or "LOCAL").upper()

    for config_key, config_value in kv.items():
        _upsert_config(conn, config_key, config_value)

    # 修正历史 set-default 写入的 category=SYS
    conn.execute(
        sa.text(
            """
            UPDATE sys_config
            SET category = 'STORAGE', updated_at = :now
            WHERE config_key = 'DEFAULT_FILE_ENGINE' AND COALESCE(category, '') <> 'STORAGE'
            """
        ),
        {"now": _NOW},
    )

    # 按反规范化 provider 回写 storage_config_id
    result = conn.execute(
        sa.text(
            """
            UPDATE sys_file
            SET storage_config_id = storage_provider,
                updated_at = :now
            WHERE storage_provider IS NOT NULL
              AND storage_provider <> ''
              AND storage_config_id IS DISTINCT FROM storage_provider
            """
        ),
        {"now": _NOW},
    )
    _LOG.info("remapped sys_file.storage_config_id for %s rows", result.rowcount)

    leftover = conn.execute(
        sa.text(
            """
            SELECT id, storage_config_id, storage_provider
            FROM sys_file
            WHERE storage_config_id IS NULL
               OR storage_config_id = ''
               OR storage_config_id NOT IN ('local', 'minio', 'oss', 's3')
            """
        )
    ).mappings().all()
    for row in leftover:
        _LOG.warning(
            "sys_file id=%s still has non-provider storage_config_id=%r provider=%r",
            row["id"],
            row["storage_config_id"],
            row["storage_provider"],
        )

    op.drop_table("sys_storage_config")


def downgrade() -> None:
    op.create_table(
        "sys_storage_config",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="配置名称"),
        sa.Column(
            "provider",
            sa.String(length=32),
            nullable=False,
            comment="存储服务商：local/minio/s3/oss",
        ),
        sa.Column("bucket", sa.String(length=255), nullable=True, comment="存储桶"),
        sa.Column("endpoint", sa.String(length=500), nullable=True, comment="服务端点"),
        sa.Column("access_key", sa.String(length=255), nullable=True, comment="访问密钥 ID"),
        sa.Column("secret_key", sa.String(length=255), nullable=True, comment="访问密钥 Secret"),
        sa.Column("region", sa.String(length=100), nullable=True, comment="区域"),
        sa.Column("use_ssl", sa.Boolean(), nullable=False, comment="是否使用 SSL 连接"),
        sa.Column("base_url", sa.String(length=500), nullable=True, comment="自定义基础 URL"),
        sa.Column("public_path", sa.String(length=255), nullable=False, comment="公开访问路径"),
        sa.Column("local_root", sa.String(length=500), nullable=False, comment="本地存储根目录"),
        sa.Column("windows_root", sa.String(length=500), nullable=True, comment="WINDOWS 本地存储根目录"),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, comment="是否为当前启用的默认配置（互斥）"
        ),
        sa.Column("remark", sa.String(length=255), nullable=True, comment="备注"),
        sa.Column("sort_code", sa.Integer(), nullable=False, comment="排序码"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建人"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True, comment="更新人"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sys_storage_config")),
    )
    # 数据不回填；仅恢复表结构以便降级启动


def _upsert_config(conn, config_key: str, config_value: str) -> None:
    meta = _SEED_META.get(config_key)
    row_id = meta[0] if meta else f"cfg_sto_mig_{config_key.lower()}"
    remark = meta[1] if meta else config_key
    sort_code = meta[2] if meta else 0
    existing = conn.execute(
        sa.text("SELECT id FROM sys_config WHERE config_key = :key"),
        {"key": config_key},
    ).scalar()
    if existing:
        conn.execute(
            sa.text(
                """
                UPDATE sys_config
                SET config_value = :value,
                    category = 'STORAGE',
                    remark = COALESCE(NULLIF(remark, ''), :remark),
                    updated_at = :now
                WHERE config_key = :key
                """
            ),
            {
                "key": config_key,
                "value": config_value,
                "remark": remark,
                "now": _NOW,
            },
        )
        return
    conn.execute(
        sa.text(
            """
            INSERT INTO sys_config (
                id, config_key, config_value, category, remark, sort_code,
                value_type, label, scope, scene, is_builtin, ext_json,
                created_at, created_by, updated_at, updated_by
            ) VALUES (
                :id, :key, :value, 'STORAGE', :remark, :sort_code,
                'STRING', NULL, NULL, NULL, TRUE, CAST('{}' AS json),
                :now, NULL, :now, NULL
            )
            """
        ),
        {
            "id": row_id,
            "key": config_key,
            "value": config_value,
            "remark": remark,
            "sort_code": sort_code,
            "now": _NOW,
        },
    )
