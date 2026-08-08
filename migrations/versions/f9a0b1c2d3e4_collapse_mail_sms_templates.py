""" Author: Charlie

邮件/短信模板不再按账户类型拆分：
MAIL_TEMPLATE_{ADMIN|PORTAL}_{SCENE} → MAIL_TEMPLATE_{SCENE}
SMS_TEMPLATE_{ADMIN|PORTAL}_{SCENE} → SMS_TEMPLATE_{SCENE}
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "f9a0b1c2d3e4"
down_revision: str | Sequence[str] | None = "e8f9a0b1c2d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 8, tzinfo=UTC)


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT id, config_key, config_value, category, remark, sort_code, value_type,
                   label, scope, scene, is_builtin, ext_json, created_at, created_by,
                   updated_at, updated_by
            FROM sys_config
            WHERE category IN ('MAIL_TEMPLATE', 'SMS_TEMPLATE')
            ORDER BY category, scene, scope NULLS LAST, updated_at DESC NULLS LAST, id
            """
        )
    ).mappings().all()

    keep_by_scene: dict[tuple[str, str], dict] = {}
    drop_ids: list[str] = []
    for row in rows:
        scene = row["scene"] or _scene_from_key(row["config_key"], row["category"])
        if not scene:
            continue
        key = (row["category"], scene)
        if key not in keep_by_scene:
            keep_by_scene[key] = dict(row)
            keep_by_scene[key]["scene"] = scene
        else:
            # 优先保留 ADMIN；否则已按 updated_at DESC 取第一条
            current = keep_by_scene[key]
            if current.get("scope") != "ADMIN" and row.get("scope") == "ADMIN":
                drop_ids.append(str(current["id"]))
                keep_by_scene[key] = dict(row)
                keep_by_scene[key]["scene"] = scene
            else:
                drop_ids.append(str(row["id"]))

    for drop_id in drop_ids:
        conn.execute(sa.text("DELETE FROM sys_config WHERE id = :id"), {"id": drop_id})

    for (category, scene), row in keep_by_scene.items():
        new_key = f"{category}_{scene}"
        conn.execute(
            sa.text(
                """
                UPDATE sys_config
                SET config_key = :config_key,
                    scope = NULL,
                    scene = :scene,
                    remark = :remark,
                    updated_at = :now
                WHERE id = :id
                """
            ),
            {
                "id": row["id"],
                "config_key": new_key,
                "scene": scene,
                "remark": scene,
                "now": _NOW,
            },
        )


def downgrade() -> None:
    """将全局模板克隆回 ADMIN / PORTAL（内容相同）。"""
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT id, config_key, config_value, category, sort_code, value_type,
                   label, scene, is_builtin, ext_json
            FROM sys_config
            WHERE category IN ('MAIL_TEMPLATE', 'SMS_TEMPLATE')
              AND (scope IS NULL OR scope = '')
            """
        )
    ).mappings().all()

    for row in rows:
        scene = row["scene"] or _scene_from_key(row["config_key"], row["category"])
        if not scene:
            continue
        # 当前行改为 ADMIN
        conn.execute(
            sa.text(
                """
                UPDATE sys_config
                SET config_key = :config_key,
                    scope = 'ADMIN',
                    scene = :scene,
                    remark = :remark
                WHERE id = :id
                """
            ),
            {
                "id": row["id"],
                "config_key": f"{row['category']}_ADMIN_{scene}",
                "scene": scene,
                "remark": f"ADMIN {scene}",
            },
        )
        # 克隆 PORTAL
        portal_id = f"{row['id']}_portal"
        exists = conn.execute(
            sa.text("SELECT 1 FROM sys_config WHERE id = :id OR config_key = :key LIMIT 1"),
            {"id": portal_id, "key": f"{row['category']}_PORTAL_{scene}"},
        ).scalar()
        if exists:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO sys_config (
                    id, config_key, config_value, category, remark, sort_code, value_type,
                    label, scope, scene, is_builtin, ext_json, created_at, created_by,
                    updated_at, updated_by
                ) VALUES (
                    :id, :config_key, :config_value, :category, :remark, :sort_code, :value_type,
                    :label, 'PORTAL', :scene, :is_builtin, :ext_json, :now, NULL, :now, NULL
                )
                """
            ),
            {
                "id": portal_id,
                "config_key": f"{row['category']}_PORTAL_{scene}",
                "config_value": row["config_value"],
                "category": row["category"],
                "remark": f"PORTAL {scene}",
                "sort_code": int(row["sort_code"] or 0) + 100,
                "value_type": row["value_type"] or "JSON",
                "label": row["label"],
                "scene": scene,
                "is_builtin": bool(row["is_builtin"]),
                "ext_json": row["ext_json"] if row["ext_json"] is not None else {},
                "now": _NOW,
            },
        )


def _scene_from_key(config_key: str, category: str) -> str | None:
    prefix = f"{category}_"
    if not config_key.startswith(prefix):
        return None
    rest = config_key[len(prefix) :]
    for scope in ("ADMIN_", "PORTAL_"):
        if rest.startswith(scope):
            return rest[len(scope) :] or None
    return rest or None
