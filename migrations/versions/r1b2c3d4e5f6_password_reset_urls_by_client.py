""" Author: Charlie

补齐 ADMIN / PORTAL 密码重置页 URL（不覆盖已有值）。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "r1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "q0a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 8, tzinfo=UTC)

_SEED_ROWS: tuple[tuple[str, str, str, str, str, int, str, str, str | None, str | None], ...] = (
    (
        "cfg_3c98bcca99e448cd",
        "AUTH_PASSWORD_RESET_URL_ADMIN",
        "http://localhost:5173/auth/forgot-password",
        "AUTH_TOKEN",
        "ADMIN 密码重置页完整 URL",
        3,
        "STRING",
        "ADMIN 密码重置页完整 URL",
        "ADMIN",
        None,
    ),
    (
        "cfg_cd29b96922a8b478",
        "AUTH_PASSWORD_RESET_URL_PORTAL",
        "http://localhost:5174/auth/forgot-password",
        "AUTH_TOKEN",
        "PORTAL 密码重置页完整 URL",
        4,
        "STRING",
        "PORTAL 密码重置页完整 URL",
        "PORTAL",
        None,
    ),
)


def upgrade() -> None:
    conn = op.get_bind()
    for row_id, key, value, category, remark, sort_code, value_type, label, scope, scene in _SEED_ROWS:
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
                    :id, :key, :value, :category, :remark, :sort_code,
                    CAST('{}' AS json), :value_type, :label, :scope, :scene, true,
                    :now, NULL, :now, NULL
                )
                """
            ),
            {
                "id": row_id,
                "key": key,
                "value": value,
                "category": category,
                "remark": remark,
                "sort_code": sort_code,
                "value_type": value_type,
                "label": label,
                "scope": scope,
                "scene": scene,
                "now": _NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for _, key, *_ in _SEED_ROWS:
        conn.execute(
            sa.text("DELETE FROM sys_config WHERE config_key = :key"),
            {"key": key},
        )
