""" Author: Charlie

系统菜单：登录日志、操作审计，及详情按钮的 RESOURCE_PERMISSION 绑定。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "t3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "s2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 9, tzinfo=UTC)

_RESOURCE_IDS = ("200028", "201060", "200029", "201061")
_RELATION_IDS = (
    "rel_audit_menu_login_log",
    "rel_audit_btn_login_log_detail",
    "rel_audit_menu_audit",
    "rel_audit_btn_audit_detail",
)


def upgrade() -> None:
    conn = op.get_bind()

    rows = [
        (
            "200028",
            "200003",
            "sys-login-log",
            "登录日志",
            "MENU",
            "/sys/login-log",
            "/sys/login-log/index.vue",
            "icon-park-outline:log",
            8,
            True,
            "登录成功/失败历史记录",
        ),
        (
            "201060",
            "200028",
            "sys-login-log-detail",
            "查看登录日志",
            "BUTTON",
            None,
            None,
            None,
            1,
            True,
            None,
        ),
        (
            "200029",
            "200003",
            "sys-audit",
            "操作审计",
            "MENU",
            "/sys/audit",
            "/sys/audit/index.vue",
            "icon-park-outline:audit",
            9,
            True,
            "系统操作审计日志",
        ),
        (
            "201061",
            "200029",
            "sys-audit-detail",
            "查看审计详情",
            "BUTTON",
            None,
            None,
            None,
            1,
            True,
            None,
        ),
    ]

    for row in rows:
        (
            rid,
            parent_id,
            code,
            name,
            rtype,
            path,
            component,
            icon,
            sort,
            visible,
            description,
        ) = row
        exists = conn.execute(
            sa.text("SELECT 1 FROM sys_resource WHERE id = :id"),
            {"id": rid},
        ).scalar()
        if exists:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO sys_resource (
                    id, parent_id, code, name, resource_type, module_id, path, component,
                    redirect, icon, color, href, sort, is_visible, is_cache,
                    is_affix, status, description, layout, extra,
                    created_at, created_by, updated_at, updated_by
                ) VALUES (
                    :id, :parent_id, :code, :name, :rtype, '210001', :path, :component,
                    NULL, :icon, NULL, NULL, :sort, :visible, FALSE,
                    FALSE, 'ENABLED', :description, NULL, CAST('{}' AS json),
                    :now, NULL, :now, NULL
                )
                """
            ),
            {
                "id": rid,
                "parent_id": parent_id,
                "code": code,
                "name": name,
                "rtype": rtype,
                "path": path,
                "component": component,
                "icon": icon,
                "sort": sort,
                "visible": visible,
                "description": description,
                "now": _NOW,
            },
        )

    perm_binds = [
        ("rel_audit_menu_login_log", "200028", "sys:audit:page"),
        ("rel_audit_btn_login_log_detail", "201060", "sys:audit:detail"),
        ("rel_audit_menu_audit", "200029", "sys:audit:page"),
        ("rel_audit_btn_audit_detail", "201061", "sys:audit:detail"),
    ]
    for relation_id, resource_id, permission_key in perm_binds:
        exists = conn.execute(
            sa.text("SELECT 1 FROM sys_iam_relation WHERE id = :id"),
            {"id": relation_id},
        ).scalar()
        if exists:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO sys_iam_relation (
                    id, relation_type, subject_type, subject_id, account_type,
                    target_type, target_id, target_key, status,
                    grant_mode, data_scope, custom_scope_dept_ids, sort,
                    is_primary, extra, created_at, created_by, updated_at, updated_by
                ) VALUES (
                    :id, 'RESOURCE_PERMISSION', 'RESOURCE', :resource_id, 'ADMIN',
                    'PERMISSION', '', :permission_key, 'ENABLED',
                    'CASCADE', 'ALL', CAST('[]' AS json), 0,
                    FALSE, CAST('{}' AS json), :now, NULL, :now, NULL
                )
                """
            ),
            {
                "id": relation_id,
                "resource_id": resource_id,
                "permission_key": permission_key,
                "now": _NOW,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM sys_iam_relation WHERE id = ANY(:ids)"),
        {"ids": list(_RELATION_IDS)},
    )
    conn.execute(
        sa.text("DELETE FROM sys_resource WHERE id = ANY(:ids)"),
        {"ids": list(_RESOURCE_IDS)},
    )
