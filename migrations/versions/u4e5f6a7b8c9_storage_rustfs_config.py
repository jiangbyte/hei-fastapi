""" Author: Charlie

文件存储：新增 RustFS（S3 兼容）sys_config 种子键。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "u4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "t3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 9, tzinfo=UTC)

# id, key, value, remark, sort_code, value_type
_ROWS: list[tuple[str, str, str, str, int, str]] = [
    ("cfg_sto_rustfs_01", "STORAGE_RUSTFS_BUCKET", "defaultbucket", "RustFS 存储桶", 40, "STRING"),
    ("cfg_sto_rustfs_02", "STORAGE_RUSTFS_ENDPOINT", "http://127.0.0.1:9002", "RustFS S3 API 端点", 41, "STRING"),
    ("cfg_sto_rustfs_03", "STORAGE_RUSTFS_ACCESS_KEY", "admin", "RustFS Access Key", 42, "STRING"),
    ("cfg_sto_rustfs_04", "STORAGE_RUSTFS_SECRET_KEY", "123456789", "RustFS Secret Key", 43, "STRING"),
    ("cfg_sto_rustfs_05", "STORAGE_RUSTFS_REGION", "us-east-1", "RustFS Region", 44, "STRING"),
    ("cfg_sto_rustfs_06", "STORAGE_RUSTFS_USE_SSL", "FALSE", "RustFS 是否 SSL", 45, "BOOL"),
    ("cfg_sto_rustfs_07", "STORAGE_RUSTFS_BASE_URL", "", "RustFS 自定义基础 URL", 46, "STRING"),
    ("cfg_sto_rustfs_08", "STORAGE_RUSTFS_PUBLIC_PATH", "/api/v1/files", "RustFS 公开访问路径", 47, "STRING"),
]

_KEYS = [row[1] for row in _ROWS]


def upgrade() -> None:
    conn = op.get_bind()
    for row_id, key, value, remark, sort_code, value_type in _ROWS:
        exists = conn.execute(
            sa.text("SELECT 1 FROM sys_config WHERE config_key = :key LIMIT 1"),
            {"key": key},
        ).scalar()
        if exists:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO sys_config (
                    id, config_key, config_value, category, remark, sort_code,
                    ext_json, value_type, label, scope, scene, is_builtin,
                    created_at, created_by, updated_at, updated_by
                ) VALUES (
                    :id, :key, :value, 'STORAGE', :remark, :sort_code,
                    CAST('{}' AS json), :value_type, NULL, NULL, NULL, TRUE,
                    :now, NULL, :now, NULL
                )
                """
            ),
            {
                "id": row_id,
                "key": key,
                "value": value,
                "remark": remark,
                "sort_code": sort_code,
                "value_type": value_type,
                "now": _NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM sys_config WHERE config_key = ANY(:keys)"),
        {"keys": list(_KEYS)},
    )
    # 若默认引擎已切到 RUSTFS，回退到 MINIO，避免启动校验失败
    conn.execute(
        sa.text(
            """
            UPDATE sys_config
            SET config_value = 'MINIO', updated_at = :now
            WHERE config_key = 'DEFAULT_FILE_ENGINE'
              AND UPPER(TRIM(config_value)) = 'RUSTFS'
            """
        ),
        {"now": _NOW},
    )
