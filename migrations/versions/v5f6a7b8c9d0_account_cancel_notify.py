""" Author: Charlie

账号注销：保留期通知联系方式字段 + 邮件/短信模板 + 保留天数配置。
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "v5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "u4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 9, tzinfo=UTC)

_MAIL_CANCELLED = {
    "subject": "{{app_name}} 账号注销确认",
    "body": (
        "您好，您的账号已申请注销。\n\n"
        "我们将在 {{retention_days}} 天内保留账号数据；到期且期间未再登录使用后，"
        "系统将彻底删除账号及相关数据。\n\n"
        "预计清理时间：{{purge_at}}\n"
        "如非本人操作，请尽快联系管理员。"
    ),
}

_MAIL_PURGED = {
    "subject": "{{app_name}} 账号已彻底删除",
    "body": (
        "您好，您此前注销的账号已完成保留期清理，账号及相关个人数据已彻底删除。\n\n"
        "清理时间：{{purged_at}}\n"
        "感谢您曾使用 {{app_name}}。"
    ),
}

_SMS_CANCELLED = {
    "code": "",
    "content": "账号已申请注销，将于{{retention_days}}天后彻底删除。",
}

_SMS_PURGED = {
    "code": "",
    "content": "您的账号已完成注销清理并彻底删除。",
}

_CONFIG_ROWS: list[tuple[str, str, str, str, str, int, str, str | None]] = [
    (
        "cfg_acct_cancel_ret_01",
        "ACCOUNT_CANCEL_RETENTION_DAYS",
        "15",
        "OTHER",
        "注销账号保留天数",
        10,
        "INT",
        None,
    ),
    (
        "cfg_mail_acct_cancel_01",
        "MAIL_TEMPLATE_ACCOUNT_CANCELLED",
        json.dumps(_MAIL_CANCELLED, ensure_ascii=False),
        "MAIL_TEMPLATE",
        "账号注销确认邮件模板",
        20,
        "JSON",
        "ACCOUNT_CANCELLED",
    ),
    (
        "cfg_mail_acct_purge_01",
        "MAIL_TEMPLATE_ACCOUNT_PURGED",
        json.dumps(_MAIL_PURGED, ensure_ascii=False),
        "MAIL_TEMPLATE",
        "账号彻底删除邮件模板",
        21,
        "JSON",
        "ACCOUNT_PURGED",
    ),
    (
        "cfg_sms_acct_cancel_01",
        "SMS_TEMPLATE_ACCOUNT_CANCELLED",
        json.dumps(_SMS_CANCELLED, ensure_ascii=False),
        "SMS_TEMPLATE",
        "账号注销确认短信模板",
        20,
        "JSON",
        "ACCOUNT_CANCELLED",
    ),
    (
        "cfg_sms_acct_purge_01",
        "SMS_TEMPLATE_ACCOUNT_PURGED",
        json.dumps(_SMS_PURGED, ensure_ascii=False),
        "SMS_TEMPLATE",
        "账号彻底删除短信模板",
        21,
        "JSON",
        "ACCOUNT_PURGED",
    ),
]


def upgrade() -> None:
    op.add_column(
        "sys_account",
        sa.Column("cancel_notify_email", sa.String(length=128), nullable=True, comment="注销通知邮箱"),
    )
    op.add_column(
        "sys_account",
        sa.Column("cancel_notify_phone", sa.String(length=32), nullable=True, comment="注销通知手机号"),
    )

    conn = op.get_bind()
    for row_id, key, value, category, remark, sort_code, value_type, scene in _CONFIG_ROWS:
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
                    CAST('{}' AS json), :value_type, :label, NULL, :scene, TRUE,
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
                "label": remark,
                "scene": scene,
                "now": _NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    keys = [row[1] for row in _CONFIG_ROWS]
    conn.execute(
        sa.text("DELETE FROM sys_config WHERE config_key = ANY(:keys)"),
        {"keys": keys},
    )
    op.drop_column("sys_account", "cancel_notify_phone")
    op.drop_column("sys_account", "cancel_notify_email")
