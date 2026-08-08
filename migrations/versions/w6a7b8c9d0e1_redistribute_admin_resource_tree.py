""" Author: Charlie

重建管理端资源树：按职责拆分顶级目录，仅调整 parent_id / name / sort / 可见性，
保留既有资源 id、code、path、component 与授权绑定。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "w6a7b8c9d0e1"
down_revision: str | Sequence[str] | None = "v5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 9, tzinfo=UTC)

# 新顶级目录
_NEW_CATALOGS = [
    (
        "200040",
        "resource-auth",
        "资源授权",
        "/resource-auth",
        "icon-park-outline:all-application",
        15,
        "菜单资源、模块与客户端资源授权配置",
    ),
    (
        "202030",
        "biz-demo",
        "业务示例",
        "/biz",
        "icon-park-outline:application-one",
        40,
        "代码生成业务示例页面",
    ),
]

# id -> (parent_id, sort) ；parent_id=None 表示顶级
_PARENT_SORT: dict[str, tuple[str | None, int]] = {
    # 组织权限（复用原 iam 目录）
    "200006": (None, 10),
    "200007": ("200006", 1),
    "200008": ("200006", 2),
    "200009": ("200006", 3),
    "200010": ("200006", 4),
    "200011": ("200006", 5),
    # 资源授权
    "200040": (None, 15),
    "200012": ("200040", 1),
    "200018": ("200040", 2),
    "200031": ("200040", 3),
    "200032": ("200040", 4),
    # 内容运营（复用原消息中心目录）
    "200019": (None, 20),
    "200005": ("200019", 1),
    "202200": ("200019", 2),
    "202220": ("200019", 3),
    # 系统运维（复用原系统目录）
    "200003": (None, 25),
    "200025": ("200003", 1),
    "200004": ("200003", 2),
    "200023": ("200003", 3),
    "202010": ("200003", 4),
    "200028": ("200003", 5),
    "200027": ("200003", 6),
    "200029": ("200003", 7),
    # 业务示例
    "202030": (None, 40),
    "202004": ("202030", 1),
    "202005": ("202030", 2),
    "202006": ("202030", 3),
    "202007": ("202030", 4),
    # 开发工具（复用原测试目录）
    "202001": (None, 90),
    "202015": ("202001", 1),
    "202002": ("202001", 2),
    "202003": ("202001", 3),
}

_RENAMES: dict[str, tuple[str, str | None, str | None]] = {
    # id -> (name, icon or None=keep, redirect or None=keep / ''=clear)
    "200006": ("组织权限", "icon-park-outline:people", None),
    "200019": ("内容运营", "icon-park-outline:picture-album", "/message/notice"),
    "200003": ("系统运维", "icon-park-outline:setting-two", None),
    "202001": ("开发工具", "icon-park-outline:code", "/sys/codegen"),
    "202200": ("通知消息", None, None),
}

# 嵌套「消息管理」目录迁出子菜单后隐藏，避免空壳层级
_HIDE_IDS = ("202230",)

# downgrade 还原快照（迁移前结构）
_DOWN_PARENT_SORT: dict[str, tuple[str | None, int]] = {
    "200003": (None, 10),
    "200025": ("200003", 1),
    "200004": ("200003", 2),
    "200005": ("200003", 3),
    "200023": ("200003", 4),
    "202010": ("200003", 5),
    "200028": ("200003", 8),
    "200027": ("200003", 9),
    "200029": ("200003", 9),
    "202015": ("200003", 10),
    "200006": (None, 15),
    "200007": ("200006", 1),
    "200008": ("200006", 2),
    "200009": ("200006", 3),
    "200010": ("200006", 4),
    "200011": ("200006", 5),
    "200012": ("200006", 6),
    "200018": ("200006", 7),
    "200031": ("200006", 9),
    "200032": ("200006", 10),
    "200019": (None, 18),
    "202230": ("200019", 6),
    "202200": ("202230", 3),
    "202220": ("202230", 5),
    "202001": (None, 30),
    "202002": ("202001", 1),
    "202003": ("202001", 2),
    "202004": ("202001", 10),
    "202005": ("202001", 11),
    "202006": ("202001", 12),
    "202007": ("202001", 13),
}

_DOWN_RENAMES: dict[str, tuple[str, str | None, str | None]] = {
    "200006": ("身份与权限", "icon-park-outline:permissions", None),
    "200019": ("消息中心", "icon-park-outline:message", "/message/notice"),
    "200003": ("系统", "icon-park-outline:setting-two", None),
    "202001": ("测试目录", "icon-park-outline:experiment-one", "/test/editor"),
    "202200": ("消息管理", None, None),
}


def _upsert_catalog(
    conn,
    *,
    rid: str,
    code: str,
    name: str,
    path: str,
    icon: str,
    sort: int,
    description: str,
) -> None:
    exists = conn.execute(
        sa.text("SELECT 1 FROM sys_resource WHERE id = :id"),
        {"id": rid},
    ).scalar()
    if exists:
        conn.execute(
            sa.text(
                """
                UPDATE sys_resource
                SET parent_id = NULL,
                    code = :code,
                    name = :name,
                    resource_type = 'CATALOG',
                    path = :path,
                    icon = :icon,
                    sort = :sort,
                    is_visible = TRUE,
                    status = 'ENABLED',
                    description = :description,
                    updated_at = :now
                WHERE id = :id
                """
            ),
            {
                "id": rid,
                "code": code,
                "name": name,
                "path": path,
                "icon": icon,
                "sort": sort,
                "description": description,
                "now": _NOW,
            },
        )
        return
    conn.execute(
        sa.text(
            """
            INSERT INTO sys_resource (
                id, parent_id, code, name, resource_type, module_id, path, component,
                redirect, icon, color, href, sort, is_visible, is_cache,
                is_affix, status, description, layout, extra,
                created_at, created_by, updated_at, updated_by
            ) VALUES (
                :id, NULL, :code, :name, 'CATALOG', '210001', :path, NULL,
                NULL, :icon, NULL, NULL, :sort, TRUE, FALSE,
                FALSE, 'ENABLED', :description, NULL, CAST('{}' AS json),
                :now, NULL, :now, NULL
            )
            """
        ),
        {
            "id": rid,
            "code": code,
            "name": name,
            "path": path,
            "icon": icon,
            "sort": sort,
            "description": description,
            "now": _NOW,
        },
    )


def _apply_parent_sort(conn, mapping: dict[str, tuple[str | None, int]]) -> None:
    for rid, (parent_id, sort) in mapping.items():
        conn.execute(
            sa.text(
                """
                UPDATE sys_resource
                SET parent_id = :parent_id, sort = :sort, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": rid, "parent_id": parent_id, "sort": sort, "now": _NOW},
        )


def _apply_renames(conn, mapping: dict[str, tuple[str, str | None, str | None]]) -> None:
    for rid, (name, icon, redirect) in mapping.items():
        if icon is None and redirect is None:
            conn.execute(
                sa.text(
                    """
                    UPDATE sys_resource
                    SET name = :name, updated_at = :now
                    WHERE id = :id
                    """
                ),
                {"id": rid, "name": name, "now": _NOW},
            )
            continue
        sets = ["name = :name", "updated_at = :now"]
        params: dict = {"id": rid, "name": name, "now": _NOW}
        if icon is not None:
            sets.append("icon = :icon")
            params["icon"] = icon
        if redirect is not None:
            sets.append("redirect = :redirect")
            params["redirect"] = redirect or None
        conn.execute(
            sa.text(f"UPDATE sys_resource SET {', '.join(sets)} WHERE id = :id"),
            params,
        )


def upgrade() -> None:
    conn = op.get_bind()
    for row in _NEW_CATALOGS:
        _upsert_catalog(
            conn,
            rid=row[0],
            code=row[1],
            name=row[2],
            path=row[3],
            icon=row[4],
            sort=row[5],
            description=row[6],
        )
    _apply_parent_sort(conn, _PARENT_SORT)
    _apply_renames(conn, _RENAMES)
    for rid in _HIDE_IDS:
        conn.execute(
            sa.text(
                """
                UPDATE sys_resource
                SET is_visible = FALSE, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": rid, "now": _NOW},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for rid in _HIDE_IDS:
        conn.execute(
            sa.text(
                """
                UPDATE sys_resource
                SET is_visible = TRUE, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": rid, "now": _NOW},
        )
    _apply_parent_sort(conn, _DOWN_PARENT_SORT)
    _apply_renames(conn, _DOWN_RENAMES)
    conn.execute(
        sa.text("DELETE FROM sys_resource WHERE id = ANY(:ids)"),
        {"ids": [row[0] for row in _NEW_CATALOGS]},
    )
