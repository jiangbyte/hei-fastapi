""" Author: Charlie

sys_config 增加复杂配置字段，并将邮件/短信模板成对键合并为 JSON 行。
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e3f4a5b6c7d8"
down_revision: str | Sequence[str] | None = "d2e3f4a5b6c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PAIR_RE = re.compile(
    r"^(MAIL_TEMPLATE|SMS_TEMPLATE)_(ADMIN|PORTAL)_(.+)_(SUBJECT|BODY|CODE|CONTENT)$"
)

_SCENE_LABELS = {
    "REGISTER_SUCCESS": "注册成功",
    "LOGIN_CODE": "登录验证码",
    "CHANGE_PASSWORD_CODE": "修改密码验证码",
    "RESET_PASSWORD_CODE": "重置密码验证码",
    "RESET_PASSWORD_SUCCESS": "重置密码成功",
    "PASSWORD_EXPIRING": "密码即将过期",
    "BIND_EMAIL_CODE": "绑定邮箱验证码",
    "CHANGE_EMAIL_CODE": "修改邮箱验证码",
    "BIND_PHONE_CODE": "绑定手机验证码",
    "CHANGE_PHONE_CODE": "修改手机验证码",
}


def upgrade() -> None:
    op.add_column(
        "sys_config",
        sa.Column(
            "value_type",
            sa.String(length=32),
            nullable=False,
            server_default="STRING",
            comment="值类型: STRING|JSON|BOOL|NUMBER",
        ),
    )
    op.add_column(
        "sys_config",
        sa.Column("label", sa.String(length=128), nullable=True, comment="展示名"),
    )
    op.add_column(
        "sys_config",
        sa.Column("scope", sa.String(length=32), nullable=True, comment="作用域账户类型"),
    )
    op.add_column(
        "sys_config",
        sa.Column("scene", sa.String(length=64), nullable=True, comment="场景编码"),
    )
    op.add_column(
        "sys_config",
        sa.Column(
            "is_builtin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否内置（不可删除）",
        ),
    )
    op.create_index(
        "idx_sys_config_category_scope_scene",
        "sys_config",
        ["category", "scope", "scene"],
        unique=False,
    )

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, config_key, config_value, category, remark, sort_code, "
            "ext_json, created_at, created_by, updated_at, updated_by "
            "FROM sys_config WHERE category IN ('MAIL_TEMPLATE', 'SMS_TEMPLATE')"
        )
    ).mappings().all()

    groups: dict[tuple[str, str, str], dict] = {}
    delete_ids: list[str] = []
    for row in rows:
        match = _PAIR_RE.match(row["config_key"] or "")
        if not match:
            continue
        prefix, scope, scene, field = match.groups()
        key = (prefix, scope, scene)
        bucket = groups.setdefault(
            key,
            {
                "fields": {},
                "sort_code": row["sort_code"] or 0,
                "created_at": row["created_at"],
                "created_by": row["created_by"],
                "updated_at": row["updated_at"],
                "updated_by": row["updated_by"],
                "ext_json": row["ext_json"] or {},
            },
        )
        bucket["fields"][field] = row["config_value"] or ""
        bucket["sort_code"] = min(bucket["sort_code"], row["sort_code"] or 0)
        delete_ids.append(row["id"])

    if delete_ids:
        conn.execute(
            sa.text("DELETE FROM sys_config WHERE id IN :ids").bindparams(
                sa.bindparam("ids", expanding=True)
            ),
            {"ids": delete_ids},
        )

    for idx, ((prefix, scope, scene), bucket) in enumerate(groups.items(), start=1):
        fields = bucket["fields"]
        if prefix == "MAIL_TEMPLATE":
            payload = {
                "subject": fields.get("SUBJECT", ""),
                "body": fields.get("BODY", ""),
            }
            category = "MAIL_TEMPLATE"
            id_prefix = "cfg_mt"
        else:
            payload = {
                "code": fields.get("CODE", ""),
                "content": fields.get("CONTENT", ""),
            }
            category = "SMS_TEMPLATE"
            id_prefix = "cfg_st"
        config_key = f"{prefix}_{scope}_{scene}"
        label = _SCENE_LABELS.get(scene, scene)
        conn.execute(
            sa.text(
                """
                INSERT INTO sys_config (
                    id, config_key, config_value, category, remark, sort_code,
                    value_type, label, scope, scene, is_builtin, ext_json,
                    created_at, created_by, updated_at, updated_by
                ) VALUES (
                    :id, :config_key, :config_value, :category, :remark, :sort_code,
                    'JSON', :label, :scope, :scene, true, CAST(:ext_json AS json),
                    :created_at, :created_by, :updated_at, :updated_by
                )
                """
            ),
            {
                "id": f"{id_prefix}_{scope.lower()}_{idx:03d}",
                "config_key": config_key,
                "config_value": json.dumps(payload, ensure_ascii=False),
                "category": category,
                "remark": f"{scope} {scene}",
                "sort_code": bucket["sort_code"],
                "label": label,
                "scope": scope,
                "scene": scene,
                "ext_json": json.dumps(bucket["ext_json"] or {}),
                "created_at": bucket["created_at"],
                "created_by": bucket["created_by"],
                "updated_at": bucket["updated_at"],
                "updated_by": bucket["updated_by"],
            },
        )

    op.alter_column("sys_config", "value_type", server_default=None)
    op.alter_column("sys_config", "is_builtin", server_default=None)


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, config_key, config_value, category, remark, sort_code, "
            "label, scope, scene, ext_json, created_at, created_by, updated_at, updated_by "
            "FROM sys_config WHERE value_type = 'JSON' "
            "AND category IN ('MAIL_TEMPLATE', 'SMS_TEMPLATE')"
        )
    ).mappings().all()

    delete_ids: list[str] = []
    for row in rows:
        scope = row["scope"]
        scene = row["scene"]
        if not scope or not scene:
            continue
        try:
            payload = json.loads(row["config_value"] or "{}")
        except json.JSONDecodeError:
            payload = {}
        delete_ids.append(row["id"])
        if row["category"] == "MAIL_TEMPLATE":
            pairs = [
                ("SUBJECT", payload.get("subject", "")),
                ("BODY", payload.get("body", "")),
            ]
            prefix = "MAIL_TEMPLATE"
        else:
            pairs = [
                ("CODE", payload.get("code", "")),
                ("CONTENT", payload.get("content", "")),
            ]
            prefix = "SMS_TEMPLATE"
        for idx, (field, value) in enumerate(pairs):
            conn.execute(
                sa.text(
                    """
                    INSERT INTO sys_config (
                        id, config_key, config_value, category, remark, sort_code,
                        value_type, label, scope, scene, is_builtin, ext_json,
                        created_at, created_by, updated_at, updated_by
                    ) VALUES (
                        :id, :config_key, :config_value, :category, :remark, :sort_code,
                        'STRING', NULL, NULL, NULL, false, CAST(:ext_json AS json),
                        :created_at, :created_by, :updated_at, :updated_by
                    )
                    """
                ),
                {
                    "id": f"{row['id']}_{field.lower()}"[:64],
                    "config_key": f"{prefix}_{scope}_{scene}_{field}",
                    "config_value": value,
                    "category": row["category"],
                    "remark": row["remark"],
                    "sort_code": (row["sort_code"] or 0) + idx,
                    "ext_json": json.dumps(row["ext_json"] or {}),
                    "created_at": row["created_at"],
                    "created_by": row["created_by"],
                    "updated_at": row["updated_at"],
                    "updated_by": row["updated_by"],
                },
            )

    if delete_ids:
        conn.execute(
            sa.text("DELETE FROM sys_config WHERE id IN :ids").bindparams(
                sa.bindparam("ids", expanding=True)
            ),
            {"ids": delete_ids},
        )

    op.drop_index("idx_sys_config_category_scope_scene", table_name="sys_config")
    op.drop_column("sys_config", "is_builtin")
    op.drop_column("sys_config", "scene")
    op.drop_column("sys_config", "scope")
    op.drop_column("sys_config", "label")
    op.drop_column("sys_config", "value_type")
