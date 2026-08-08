""" Author: Charlie

移除账户 MFA / WebAuthn 字段。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "k4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "j3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("sys_account", "webauthn_credentials_json")
    op.drop_column("sys_account", "mfa_backup_codes_hash")
    op.drop_column("sys_account", "mfa_enabled_at")
    op.drop_column("sys_account", "mfa_secret_encrypted")
    op.drop_column("sys_account", "mfa_enabled")


def downgrade() -> None:
    op.add_column(
        "sys_account",
        sa.Column(
            "mfa_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="是否启用 MFA",
        ),
    )
    op.add_column(
        "sys_account",
        sa.Column("mfa_secret_encrypted", sa.Text(), nullable=True, comment="MFA TOTP 密钥（加密）"),
    )
    op.add_column(
        "sys_account",
        sa.Column(
            "mfa_enabled_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="MFA 启用时间",
        ),
    )
    op.add_column(
        "sys_account",
        sa.Column("mfa_backup_codes_hash", sa.Text(), nullable=True, comment="MFA 备份码哈希 JSON"),
    )
    op.add_column(
        "sys_account",
        sa.Column(
            "webauthn_credentials_json",
            sa.Text(),
            nullable=True,
            comment="WebAuthn 凭证 JSON 列表",
        ),
    )
    op.alter_column("sys_account", "mfa_enabled", server_default=None)
