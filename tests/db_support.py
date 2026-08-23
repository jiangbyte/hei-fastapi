""" Author: Charlie

测试库 URL：默认与 DB__URL 相同；pytest 不得 drop 表或清数据。
"""

from __future__ import annotations

import os

from app.core.config.settings import settings
from app.core.db.compat import dialect_name_from_url


def resolve_test_db_url() -> str:
    """返回测试用数据库 URL（TEST_DB__URL 优先，否则与 DB__URL 相同）。"""
    explicit = (os.environ.get("TEST_DB__URL") or "").strip()
    if explicit:
        dialect_name_from_url(explicit)
        return explicit

    url = (settings.db.url or "").strip()
    if not url:
        raise RuntimeError("DB__URL is not configured; cannot resolve test database URL")
    dialect_name_from_url(url)
    return url
