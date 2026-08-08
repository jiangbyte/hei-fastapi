""" Author: Charlie

审计告警增加通知渠道开关：复用邮件 / 消息推送 / 自定义 Webhook。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "a5b6c7d8e9f0"
down_revision: str | Sequence[str] | None = "f4a5b6c7d8e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 8, tzinfo=UTC)

_ROWS = [
    ("cfg_aa_n01", "AUDIT_ALERT_NOTIFY_EMAIL", "TRUE", "复用邮件引擎发送告警", 2),
    ("cfg_aa_n02", "AUDIT_ALERT_NOTIFY_PUSH", "TRUE", "复用消息推送发送告警", 3),
    ("cfg_aa_n03", "AUDIT_ALERT_NOTIFY_CUSTOM_WEBHOOK", "FALSE", "启用自定义 Webhook", 4),
]


def upgrade() -> None:
    conn = op.get_bind()
    for row_id, key, value, remark, sort_code in _ROWS:
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
                    :id, :key, :value, 'AUDIT_ALERT', :remark, :sort_code,
                    CAST('{}' AS json), 'BOOL', NULL, NULL, NULL, false,
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
                "now": _NOW,
            },
        )

    # 已有自定义 Webhook URL 时，默认打开自定义渠道，避免升级后丢通知
    conn.execute(
        sa.text(
            """
            UPDATE sys_config
            SET config_value = 'TRUE'
            WHERE config_key = 'AUDIT_ALERT_NOTIFY_CUSTOM_WEBHOOK'
              AND EXISTS (
                SELECT 1 FROM sys_config w
                WHERE w.config_key = 'AUDIT_ALERT_WEBHOOK_URL'
                  AND COALESCE(TRIM(w.config_value), '') <> ''
              )
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM sys_config WHERE config_key IN "
            "('AUDIT_ALERT_NOTIFY_EMAIL', 'AUDIT_ALERT_NOTIFY_PUSH', "
            "'AUDIT_ALERT_NOTIFY_CUSTOM_WEBHOOK')"
        )
    )
