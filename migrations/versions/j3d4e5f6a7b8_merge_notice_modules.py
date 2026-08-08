""" Author: Charlie

合并 msg_notification / msg_announcement → msg_notice（kind 区分），
合并已读表，并替换菜单为「消息管理」。
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "j3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "i2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 8, tzinfo=UTC)


def upgrade() -> None:
    op.create_table(
        "msg_notice",
        sa.Column("id", sa.String(length=64), nullable=False, comment="主键"),
        sa.Column("kind", sa.String(length=32), nullable=False, comment="类型"),
        sa.Column("title", sa.String(length=255), nullable=False, comment="标题"),
        sa.Column("content", sa.Text(), nullable=False, comment="内容"),
        sa.Column("content_type", sa.String(length=32), nullable=False, comment="内容格式"),
        sa.Column("category", sa.String(length=32), nullable=True, comment="分类"),
        sa.Column("severity", sa.String(length=32), nullable=False, comment="等级"),
        sa.Column("target_scope", sa.String(length=32), nullable=False, comment="目标范围"),
        sa.Column("target_account_types", sa.JSON(), nullable=False, comment="目标账户类型"),
        sa.Column("target_account_ids", sa.JSON(), nullable=False, comment="目标账户ID"),
        sa.Column("target_dept_ids", sa.JSON(), nullable=False, comment="目标部门ID"),
        sa.Column("target_role_ids", sa.JSON(), nullable=False, comment="目标角色ID"),
        sa.Column("publish_locations", sa.JSON(), nullable=False, comment="发布位置"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, comment="是否置顶"),
        sa.Column("pinned_until", sa.DateTime(timezone=True), nullable=True, comment="置顶截止"),
        sa.Column("sender_account_type", sa.String(length=32), nullable=True),
        sa.Column("sender_account_id", sa.String(length=64), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=True),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, comment="状态"),
        sa.Column("publish_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expire_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=False, comment="查看次数"),
        sa.Column("extra", sa.JSON(), nullable=False, comment="扩展信息"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_notice")),
    )
    op.create_index("ix_msg_notice_kind", "msg_notice", ["kind"])
    op.create_index("ix_msg_notice_status", "msg_notice", ["status"])

    op.create_table(
        "msg_notice_read",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("notice_id", sa.String(length=64), nullable=False),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column("account_id", sa.String(length=64), nullable=False),
        sa.Column(
            "read_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_msg_notice_read")),
        sa.UniqueConstraint(
            "notice_id",
            "account_type",
            "account_id",
            name="uq_msg_notice_read_account",
        ),
    )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO msg_notice (
                id, kind, title, content, content_type, category, severity,
                target_scope, target_account_types, target_account_ids,
                target_dept_ids, target_role_ids, publish_locations, is_pinned,
                pinned_until, sender_account_type, sender_account_id,
                source_type, source_id, status, publish_at, revoked_at,
                expire_at, view_count, extra, created_at, created_by,
                updated_at, updated_by
            )
            SELECT
                id, 'NOTIFICATION', title, content, content_type, category, severity,
                target_scope, target_account_types, target_account_ids,
                target_dept_ids, target_role_ids, CAST('{}' AS json), FALSE,
                NULL, sender_account_type, sender_account_id,
                source_type, source_id, status, publish_at, revoked_at,
                NULL, 0, extra, created_at, created_by, updated_at, updated_by
            FROM msg_notification
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO msg_notice (
                id, kind, title, content, content_type, category, severity,
                target_scope, target_account_types, target_account_ids,
                target_dept_ids, target_role_ids, publish_locations, is_pinned,
                pinned_until, sender_account_type, sender_account_id,
                source_type, source_id, status, publish_at, revoked_at,
                expire_at, view_count, extra, created_at, created_by,
                updated_at, updated_by
            )
            SELECT
                id, 'ANNOUNCEMENT', title, content, content_type, 'SYSTEM', severity,
                target_scope, target_account_types, target_account_ids,
                target_dept_ids, target_role_ids, publish_locations, is_pinned,
                pinned_until, sender_account_type, sender_account_id,
                NULL, NULL, status, publish_at, revoked_at,
                expire_at, view_count, extra, created_at, created_by,
                updated_at, updated_by
            FROM msg_announcement
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO msg_notice_read (id, notice_id, account_type, account_id, read_at)
            SELECT id, notification_id, account_type, account_id, read_at
            FROM msg_notification_read
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO msg_notice_read (id, notice_id, account_type, account_id, read_at)
            SELECT id, announcement_id, account_type, account_id, COALESCE(created_at, :now)
            FROM msg_announcement_read
            ON CONFLICT ON CONSTRAINT uq_msg_notice_read_account DO NOTHING
            """
        ),
        {"now": _NOW},
    )

    op.drop_table("msg_notification_read")
    op.drop_table("msg_announcement_read")
    op.drop_table("msg_notification")
    op.drop_table("msg_announcement")

    _migrate_menu_resources(conn)


def downgrade() -> None:
    raise NotImplementedError("msg_notice merge is not reversible")


def _migrate_menu_resources(conn) -> None:
    old_ids = [
        "202200",
        "202201",
        "202202",
        "202203",
        "202204",
        "202205",
        "202206",
        "202207",
        "202208",
        "202210",
        "202211",
        "202212",
        "202213",
        "202214",
        "202215",
        "202216",
        "202217",
        "202218",
    ]
    # 清理指向旧菜单的 IAM 授权
    conn.execute(
        sa.text(
            """
            DELETE FROM sys_iam_relation
            WHERE subject_id = ANY(:ids) OR target_id = ANY(:ids)
            """
        ),
        {"ids": old_ids},
    )
    conn.execute(
        sa.text("DELETE FROM sys_resource WHERE id = ANY(:ids)"),
        {"ids": old_ids},
    )

    conn.execute(
        sa.text(
            """
            UPDATE sys_resource
            SET redirect = '/message/notice', updated_at = :now
            WHERE id = '200019'
            """
        ),
        {"now": _NOW},
    )

    rows = [
        (
            "202200",
            "202230",
            "message-notice",
            "消息管理",
            "MENU",
            "/message/notice",
            "/message/notice/index.vue",
            "icon-park-outline:message",
            3,
            True,
            "消息管理",
        ),
        ("202201", "202200", "message-notice-page", "分页消息", "BUTTON", None, None, None, 10, False, None),
        ("202202", "202200", "message-notice-create", "新增消息", "BUTTON", None, None, None, 20, False, None),
        ("202203", "202200", "message-notice-detail", "详情消息", "BUTTON", None, None, None, 30, False, None),
        ("202204", "202200", "message-notice-update", "编辑消息", "BUTTON", None, None, None, 40, False, None),
        ("202205", "202200", "message-notice-delete", "删除消息", "BUTTON", None, None, None, 50, False, None),
        ("202209", "202200", "message-notice-publish", "发布消息", "BUTTON", None, None, None, 55, False, None),
        ("202240", "202200", "message-notice-revoke", "撤回消息", "BUTTON", None, None, None, 56, False, None),
        ("202241", "202200", "message-notice-pin", "置顶消息", "BUTTON", None, None, None, 57, False, None),
        (
            "202206",
            "202200",
            "message-notice-create-page",
            "新增消息页",
            "PAGE",
            "/message/notice/create",
            "/message/notice/form.vue",
            None,
            60,
            False,
            None,
        ),
        (
            "202207",
            "202200",
            "message-notice-edit-page",
            "编辑消息页",
            "PAGE",
            "/message/notice/edit",
            "/message/notice/form.vue",
            None,
            70,
            False,
            None,
        ),
        (
            "202208",
            "202200",
            "message-notice-detail-page",
            "消息详情页",
            "PAGE",
            "/message/notice/detail",
            "/message/notice/detail.vue",
            None,
            80,
            False,
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

    # 绑定权限键（与路由 require_permission 对齐）
    perm_binds = [
        ("202201", "message:notice:page"),
        ("202202", "message:notice:create"),
        ("202203", "message:notice:detail"),
        ("202204", "message:notice:update"),
        ("202205", "message:notice:delete"),
        ("202209", "message:notice:publish"),
        ("202240", "message:notice:revoke"),
        ("202241", "message:notice:pin"),
    ]
    for resource_id, permission_key in perm_binds:
        conn.execute(
            sa.text(
                """
                INSERT INTO sys_iam_relation (
                    id, relation_type, subject_type, subject_id, account_type,
                    target_type, target_id, target_key, effect, status,
                    grant_mode, data_scope, custom_scope_dept_ids, sort,
                    is_primary, extra, created_at, created_by, updated_at, updated_by
                ) VALUES (
                    :id, 'RESOURCE_PERMISSION', 'RESOURCE', :resource_id, 'ADMIN',
                    'PERMISSION', '', :permission_key, 'ALLOW', 'ENABLED',
                    'CASCADE', 'ALL', CAST('[]' AS json), 0,
                    FALSE, CAST('{}' AS json), :now, NULL, :now, NULL
                )
                """
            ),
            {
                "id": f"rel_notice_{resource_id}",
                "resource_id": resource_id,
                "permission_key": permission_key,
                "now": _NOW,
            },
        )

