""" Author: Charlie

移除第三方登录与支付相关 sys_config 种子项。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b5c6d7e8f9a0"
down_revision: str | Sequence[str] | None = "a5b6c7d8e9f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM sys_config WHERE category IN ('THIRD_PARTY', 'PAYMENT')"
        )
    )


def downgrade() -> None:
    # 配置项已废弃，不恢复
    pass
