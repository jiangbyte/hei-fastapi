""" Author: Charlie

清理死 IAM relation、对齐消息字典（删过时树、TARGET_SCOPE 死项、SEVERITY/CATEGORY）。
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "m6a7b8c9d0e1"
down_revision: str | Sequence[str] | None = "l5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = datetime(2026, 8, 8, tzinfo=UTC)

_DEAD_RELATION_TYPES = (
    "SUBJECT_PERMISSION_GRANT",
    "ROLE_RESOURCE",
    "ACCOUNT_RESOURCE",
    "ROLE_PERMISSION",
)

# 按 code 前缀整树删除（根节点 code 等于前缀，子项为 前缀_...）
_DEAD_DICT_PREFIXES = (
    "MESSAGE_TARGET_SCOPE",
    "NOTIFICATION_STATUS",
    "MESSAGE_THREAD",
    "TODO_PRIORITY",
    "TODO_STATUS",
    "GRANT_SUBJECT_TYPE",
    "GRANT_MODE",
    "GRANT_EFFECT",
    "RESOURCE_MODULE_CLIENT",
    "ACCOUNT_IDENTITY_TYPE",
    "SUBMISSION_RESULT",
    "SUBMISSION_STATUS",
    "SUBMISSION_KIND",
    "PROBLEM_DIFFICULTY",
    "PROBLEM_LIST_KIND",
    "PROBLEM_LIST_VISIBILITY",
    "LEARNING_PLAN_CATEGORY",
    "CONTEST_FORMAT",
    "CONTEST_LIFECYCLE_STATUS",
    "CONTEST_TYPE",
)


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text(
            """
            DELETE FROM sys_iam_relation
            WHERE relation_type = ANY(:dead_types)
               OR target_key LIKE 'workbench:%'
               OR (
                    relation_type IN ('SUBJECT_RESOURCE_GRANT', 'RESOURCE_PERMISSION')
                    AND (
                        (
                            relation_type = 'SUBJECT_RESOURCE_GRANT'
                            AND target_type = 'RESOURCE'
                            AND target_id IS NOT NULL
                            AND target_id <> ''
                            AND NOT EXISTS (
                                SELECT 1 FROM sys_resource r WHERE r.id = sys_iam_relation.target_id
                            )
                        )
                        OR (
                            relation_type = 'RESOURCE_PERMISSION'
                            AND subject_type = 'RESOURCE'
                            AND subject_id IS NOT NULL
                            AND subject_id <> ''
                            AND NOT EXISTS (
                                SELECT 1 FROM sys_resource r WHERE r.id = sys_iam_relation.subject_id
                            )
                        )
                    )
               )
            """
        ),
        {"dead_types": list(_DEAD_RELATION_TYPES)},
    )

    for prefix in _DEAD_DICT_PREFIXES:
        conn.execute(
            sa.text("DELETE FROM sys_dict WHERE code = :prefix OR code LIKE :child"),
            {"prefix": prefix, "child": f"{prefix}_%"},
        )

    conn.execute(sa.text("DELETE FROM sys_dict WHERE code = 'CS'"))
    conn.execute(
        sa.text(
            """
            DELETE FROM sys_dict
            WHERE code IN ('TARGET_SCOPE_DEPARTMENT', 'TARGET_SCOPE_ROLE')
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE sys_dict
            SET sort = 3
            WHERE code = 'TARGET_SCOPE_SPECIFIC'
            """
        )
    )

    conn.execute(
        sa.text(
            """
            DELETE FROM sys_dict
            WHERE code IN (
                'NOTIFICATION_SEVERITY_CRITICAL',
                'NOTIFICATION_SEVERITY_URGENT'
            )
            """
        )
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO sys_dict (
                id, code, label, value, color, category, parent_id, status, sort,
                created_at, created_by, updated_at, updated_by
            ) VALUES (
                '100126', 'NOTIFICATION_SEVERITY_URGENT', '紧急', 'URGENT',
                '#d03050', 'SYS', '100095', 'ENABLED', 5,
                :now, NULL, :now, NULL
            )
            ON CONFLICT (id) DO UPDATE SET
                code = EXCLUDED.code,
                label = EXCLUDED.label,
                value = EXCLUDED.value,
                color = EXCLUDED.color,
                parent_id = EXCLUDED.parent_id,
                status = EXCLUDED.status,
                sort = EXCLUDED.sort,
                updated_at = EXCLUDED.updated_at
            """
        ),
        {"now": _NOW},
    )

    conn.execute(
        sa.text("DELETE FROM sys_dict WHERE code = 'NOTIFICATION_CATEGORY' OR code LIKE 'NOTIFICATION_CATEGORY_%'")
    )
    conn.execute(
        sa.text(
            """
            INSERT INTO sys_dict (
                id, code, label, value, color, category, parent_id, status, sort,
                created_at, created_by, updated_at, updated_by
            ) VALUES
            (
                '100210', 'NOTIFICATION_CATEGORY', '通知分类', 'NOTIFICATION_CATEGORY',
                '#2080f0', 'SYS', NULL, 'ENABLED', 0,
                :now, NULL, :now, NULL
            ),
            (
                '100211', 'NOTIFICATION_CATEGORY_ORDER', '订单', 'ORDER',
                '#2080f0', 'SYS', '100210', 'ENABLED', 1,
                :now, NULL, :now, NULL
            ),
            (
                '100212', 'NOTIFICATION_CATEGORY_APPROVAL', '审批', 'APPROVAL',
                '#722ed1', 'SYS', '100210', 'ENABLED', 2,
                :now, NULL, :now, NULL
            ),
            (
                '100213', 'NOTIFICATION_CATEGORY_SYSTEM', '系统', 'SYSTEM',
                '#18a058', 'SYS', '100210', 'ENABLED', 3,
                :now, NULL, :now, NULL
            ),
            (
                '100214', 'NOTIFICATION_CATEGORY_SECURITY', '安全', 'SECURITY',
                '#d03050', 'SYS', '100210', 'ENABLED', 4,
                :now, NULL, :now, NULL
            ),
            (
                '100215', 'NOTIFICATION_CATEGORY_BIZ', '业务', 'BIZ',
                '#f0a020', 'SYS', '100210', 'ENABLED', 5,
                :now, NULL, :now, NULL
            )
            """
        ),
        {"now": _NOW},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM sys_dict WHERE code = 'NOTIFICATION_CATEGORY' OR code LIKE 'NOTIFICATION_CATEGORY_%'"
        )
    )
    conn.execute(
        sa.text("DELETE FROM sys_dict WHERE code = 'NOTIFICATION_SEVERITY_URGENT'")
    )
