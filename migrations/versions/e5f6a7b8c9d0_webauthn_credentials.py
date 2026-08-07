""" Author: Charlie

在 sys_account 添加 webauthn_credentials_json。
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0_webauthn"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9_mfa_owner_backfill"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "sys_account" not in set(inspector.get_table_names()):
        return
    cols = {c["name"] for c in inspector.get_columns("sys_account")}
    if "webauthn_credentials_json" in cols:
        return
    op.add_column(
        "sys_account",
        sa.Column(
            "webauthn_credentials_json",
            sa.Text(),
            nullable=True,
            comment="WebAuthn 凭证 JSON 列表",
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "sys_account" not in set(inspector.get_table_names()):
        return
    cols = {c["name"] for c in inspector.get_columns("sys_account")}
    if "webauthn_credentials_json" in cols:
        op.drop_column("sys_account", "webauthn_credentials_json")
