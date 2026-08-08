""" Author: Charlie

1. 内容运营目录补 path，避免前端因无 path 过滤掉 CATALOG 导致子菜单顶到根级；
2. 从「资源授权」拆出「客户端资源授权」目录。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "x7b8c9d0e1f2"
down_revision: str | Sequence[str] | None = "w6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 9, tzinfo=UTC)
_CLIENT_CATALOG_ID = "200041"


def upgrade() -> None:
    conn = op.get_bind()

    # 内容运营：侧边栏目录必须有 path 才会进入菜单树
    conn.execute(
        sa.text(
            """
            UPDATE sys_resource
            SET path = '/content',
                redirect = COALESCE(NULLIF(redirect, ''), '/message/notice'),
                updated_at = :now
            WHERE id = '200019'
            """
        ),
        {"now": _NOW},
    )

    exists = conn.execute(
        sa.text("SELECT 1 FROM sys_resource WHERE id = :id"),
        {"id": _CLIENT_CATALOG_ID},
    ).scalar()
    if not exists:
        conn.execute(
            sa.text(
                """
                INSERT INTO sys_resource (
                    id, parent_id, code, name, resource_type, module_id, path, component,
                    redirect, icon, color, href, sort, is_visible, is_cache,
                    is_affix, status, description, layout, extra,
                    created_at, created_by, updated_at, updated_by
                ) VALUES (
                    :id, NULL, 'client-resource-auth', '客户端资源授权', 'CATALOG', '210001',
                    '/client-resource-auth', NULL, NULL, 'icon-park-outline:application-one',
                    NULL, NULL, 16, TRUE, FALSE, FALSE, 'ENABLED',
                    '客户端模块与客户端资源授权配置', NULL, CAST('{}' AS json),
                    :now, NULL, :now, NULL
                )
                """
            ),
            {"id": _CLIENT_CATALOG_ID, "now": _NOW},
        )
    else:
        conn.execute(
            sa.text(
                """
                UPDATE sys_resource
                SET parent_id = NULL,
                    code = 'client-resource-auth',
                    name = '客户端资源授权',
                    resource_type = 'CATALOG',
                    path = '/client-resource-auth',
                    icon = 'icon-park-outline:application-one',
                    sort = 16,
                    is_visible = TRUE,
                    status = 'ENABLED',
                    description = '客户端模块与客户端资源授权配置',
                    updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": _CLIENT_CATALOG_ID, "now": _NOW},
        )

    # 客户端模块/资源迁入新目录
    for rid, sort in (("200031", 1), ("200032", 2)):
        conn.execute(
            sa.text(
                """
                UPDATE sys_resource
                SET parent_id = :parent_id, sort = :sort, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": rid, "parent_id": _CLIENT_CATALOG_ID, "sort": sort, "now": _NOW},
        )

    # 资源授权仅保留菜单资源相关项，并收紧排序
    for rid, sort in (("200012", 1), ("200018", 2)):
        conn.execute(
            sa.text(
                """
                UPDATE sys_resource
                SET parent_id = '200040', sort = :sort, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": rid, "sort": sort, "now": _NOW},
        )
    conn.execute(
        sa.text(
            """
            UPDATE sys_resource
            SET name = '资源授权',
                description = '菜单资源与资源模块授权配置',
                updated_at = :now
            WHERE id = '200040'
            """
        ),
        {"now": _NOW},
    )


def downgrade() -> None:
    conn = op.get_bind()
    for rid, sort in (("200031", 3), ("200032", 4)):
        conn.execute(
            sa.text(
                """
                UPDATE sys_resource
                SET parent_id = '200040', sort = :sort, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": rid, "sort": sort, "now": _NOW},
        )
    conn.execute(
        sa.text("DELETE FROM sys_resource WHERE id = :id"),
        {"id": _CLIENT_CATALOG_ID},
    )
    conn.execute(
        sa.text(
            """
            UPDATE sys_resource
            SET path = NULL, redirect = '/message/notice', updated_at = :now
            WHERE id = '200019'
            """
        ),
        {"now": _NOW},
    )
