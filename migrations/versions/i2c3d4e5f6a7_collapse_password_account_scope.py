""" Author: Charlie

密码策略不再按账户类型拆分：
PASSWORD_{ADMIN|PORTAL}_{FIELD} → PASSWORD_{FIELD}
优先保留 ADMIN；已有扁平键则用 ADMIN 覆盖（与管理端配置源一致）。
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "i2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "h1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 8, tzinfo=UTC)

_FIELDS = (
    "CHANGE_VERIFY_METHOD",
    "MIN_LENGTH",
    "MAX_LENGTH",
    "COMPLEXITY",
    "MAX_CONSECUTIVE_CHARS",
    "FORBID_USER_INFO",
    "FORBID_HISTORICAL",
    "HISTORY_CHECK_COUNT",
    "FORBID_WEAK_LIST",
    "VALIDITY_DAYS",
    "EXPIRY_WARNING_DAYS",
)

_SEED_META: dict[str, tuple[str, str, int]] = {
    "PASSWORD_CHANGE_VERIFY_METHOD": ("cfg_pwd_02", "修改密码验证方式", 10),
    "PASSWORD_MIN_LENGTH": ("cfg_pwd_rt_01", "密码最小长度", 11),
    "PASSWORD_MAX_LENGTH": ("cfg_pwd_rt_02", "密码最大长度", 12),
    "PASSWORD_COMPLEXITY": ("cfg_pwd_rt_14", "密码复杂度", 13),
    "PASSWORD_MAX_CONSECUTIVE_CHARS": ("cfg_pwd_rt_10", "连续相同字符上限", 14),
    "PASSWORD_FORBID_USER_INFO": ("cfg_pwd_rt_11", "密码不能包含用户信息", 15),
    "PASSWORD_FORBID_HISTORICAL": ("cfg_pwd_rt_12", "密码不能使用历史密码", 16),
    "PASSWORD_HISTORY_CHECK_COUNT": ("cfg_pwd_rt_08", "历史密码检查个数", 17),
    "PASSWORD_FORBID_WEAK_LIST": ("cfg_pwd_rt_09", "不能使用弱密码库", 18),
    "PASSWORD_VALIDITY_DAYS": ("cfg_pwd_rt_07", "密码有效期天数", 19),
    "PASSWORD_EXPIRY_WARNING_DAYS": ("cfg_pwd_rt_13", "密码过期提前提醒天数", 20),
}


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT id, config_key, config_value, category, remark, sort_code,
                   value_type, label, scope, scene, is_builtin, ext_json
            FROM sys_config
            WHERE config_key LIKE 'PASSWORD\\_ADMIN\\_%' ESCAPE '\\'
               OR config_key LIKE 'PASSWORD\\_PORTAL\\_%' ESCAPE '\\'
            """
        )
    ).mappings().all()

    by_key: dict[str, dict] = {}
    drop_ids: list[str] = []
    for row in rows:
        drop_ids.append(str(row["id"]))
        field = _field_from_scoped_key(row["config_key"])
        if not field:
            continue
        flat_key = f"PASSWORD_{field}"
        scope = "ADMIN" if row["config_key"].startswith("PASSWORD_ADMIN_") else "PORTAL"
        current = by_key.get(flat_key)
        if current is None:
            by_key[flat_key] = {"value": row["config_value"], "scope": scope}
            continue
        # ADMIN 优先
        if current["scope"] != "ADMIN" and scope == "ADMIN":
            by_key[flat_key] = {"value": row["config_value"], "scope": scope}

    for flat_key, payload in by_key.items():
        _upsert_config(conn, flat_key, payload["value"] or "")

    for drop_id in drop_ids:
        conn.execute(sa.text("DELETE FROM sys_config WHERE id = :id"), {"id": drop_id})


def downgrade() -> None:
    conn = op.get_bind()
    for field in _FIELDS:
        flat_key = f"PASSWORD_{field}"
        row = conn.execute(
            sa.text(
                """
                SELECT config_value, category, remark, sort_code, value_type, label,
                       is_builtin, ext_json
                FROM sys_config WHERE config_key = :key
                """
            ),
            {"key": flat_key},
        ).mappings().first()
        if not row:
            continue
        for scope in ("ADMIN", "PORTAL"):
            scoped_key = f"PASSWORD_{scope}_{field}"
            exists = conn.execute(
                sa.text("SELECT 1 FROM sys_config WHERE config_key = :key LIMIT 1"),
                {"key": scoped_key},
            ).scalar()
            if exists:
                continue
            meta = _SEED_META.get(flat_key)
            row_id = f"cfg_pwd_{scope.lower()}_{field.lower()}"
            sort_base = meta[2] if meta else 10
            conn.execute(
                sa.text(
                    """
                    INSERT INTO sys_config (
                        id, config_key, config_value, category, remark, sort_code,
                        value_type, label, scope, scene, is_builtin, ext_json,
                        created_at, created_by, updated_at, updated_by
                    ) VALUES (
                        :id, :key, :value, 'AUTH_PASSWORD', :remark, :sort_code,
                        :value_type, :label, :scope, NULL, :is_builtin, :ext_json,
                        :now, NULL, :now, NULL
                    )
                    """
                ),
                {
                    "id": row_id,
                    "key": scoped_key,
                    "value": row["config_value"],
                    "remark": f"{scope} {field}",
                    "sort_code": sort_base + (0 if scope == "ADMIN" else 100),
                    "value_type": row["value_type"] or "STRING",
                    "label": row["label"],
                    "scope": scope,
                    "is_builtin": bool(row["is_builtin"]),
                    "ext_json": row["ext_json"] if row["ext_json"] is not None else {},
                    "now": _NOW,
                },
            )
        # CHANGE_VERIFY_METHOD 原先无扁平运行时键，降级后删除扁平键
        if field == "CHANGE_VERIFY_METHOD":
            conn.execute(
                sa.text("DELETE FROM sys_config WHERE config_key = :key"),
                {"key": flat_key},
            )


def _field_from_scoped_key(config_key: str) -> str | None:
    for prefix in ("PASSWORD_ADMIN_", "PASSWORD_PORTAL_"):
        if config_key.startswith(prefix):
            return config_key[len(prefix) :] or None
    return None


def _upsert_config(conn, config_key: str, config_value: str) -> None:
    meta = _SEED_META.get(config_key)
    remark = meta[1] if meta else config_key
    sort_code = meta[2] if meta else 0
    row_id = meta[0] if meta else f"cfg_pwd_mig_{config_key.lower()}"
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
                    category = 'AUTH_PASSWORD',
                    remark = COALESCE(NULLIF(remark, ''), :remark),
                    scope = NULL,
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
                :id, :key, :value, 'AUTH_PASSWORD', :remark, :sort_code,
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
