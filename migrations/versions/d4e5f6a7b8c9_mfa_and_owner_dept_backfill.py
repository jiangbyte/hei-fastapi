""" Author: Charlie

在 sys_account 添加 MFA 列并回填 biz owner_dept_id。
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9_mfa_owner_backfill"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8_biz_owner_dept"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BIZ_TABLES = (
    "cg_test_activity",
    "cg_test_catalog",
    "cg_test_order",
    "cg_test_knowledge_category",
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "sys_account" in tables:
        cols = {c["name"] for c in inspector.get_columns("sys_account")}
        if "mfa_enabled" not in cols:
            op.add_column(
                "sys_account",
                sa.Column(
                    "mfa_enabled",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                    comment="是否启用 MFA",
                ),
            )
        if "mfa_secret_encrypted" not in cols:
            op.add_column(
                "sys_account",
                sa.Column("mfa_secret_encrypted", sa.Text(), nullable=True, comment="MFA TOTP 密钥（加密）"),
            )
        if "mfa_enabled_at" not in cols:
            op.add_column(
                "sys_account",
                sa.Column(
                    "mfa_enabled_at",
                    sa.DateTime(timezone=True),
                    nullable=True,
                    comment="MFA 启用时间",
                ),
            )
        if "mfa_backup_codes_hash" not in cols:
            op.add_column(
                "sys_account",
                sa.Column(
                    "mfa_backup_codes_hash",
                    sa.Text(),
                    nullable=True,
                    comment="MFA 备份码哈希 JSON",
                ),
            )

    # 从 ACCOUNT_DEPT 关系回填 owner_dept_id（每账户取首个部门）。
    if "sys_iam_relation" not in tables:
        return
    for table in _BIZ_TABLES:
        if table not in tables:
            continue
        cols = {c["name"] for c in inspector.get_columns(table)}
        if "owner_dept_id" not in cols or "created_by" not in cols:
            continue
        op.execute(
            sa.text(
                f"""
                UPDATE {table} AS t
                SET owner_dept_id = (
                    SELECT r.target_id
                    FROM sys_iam_relation AS r
                    WHERE r.subject_id = t.created_by
                      AND r.relation_type = 'ACCOUNT_DEPT'
                    ORDER BY r.created_at ASC
                    LIMIT 1
                )
                WHERE t.owner_dept_id IS NULL
                  AND t.created_by IS NOT NULL
                """
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "sys_account" not in set(inspector.get_table_names()):
        return
    cols = {c["name"] for c in inspector.get_columns("sys_account")}
    for name in (
        "mfa_backup_codes_hash",
        "mfa_enabled_at",
        "mfa_secret_encrypted",
        "mfa_enabled",
    ):
        if name in cols:
            op.drop_column("sys_account", name)
