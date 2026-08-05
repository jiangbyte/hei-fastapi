#!/usr/bin/env python3
"""按顺序加载 scripts/sql 下的 bootstrap SQL。

用法：
  python scripts/db/load_bootstrap_sql.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg


BOOTSTRAP_FILES = (
    "sys_dict.sql",
    "sys_config.sql",
    "sys_storage_config.sql",
)


def parse_db_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url.removeprefix("postgresql+asyncpg://")
    return url


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))

    from app.core.config.settings import settings

    sql_dir = project_root / "scripts" / "sql"
    db_url = parse_db_url(settings.db.url)

    with psycopg.connect(db_url) as conn:
        conn.execute("SET client_min_messages TO WARNING")
        for name in BOOTSTRAP_FILES:
            path = sql_dir / name
            if not path.is_file():
                raise FileNotFoundError(f"missing bootstrap sql: {path}")
            sql = path.read_text(encoding="utf-8")
            print(f"applying {path.relative_to(project_root)} ...")
            conn.execute(sql)
            conn.commit()
            print(f"  ok")
    print("bootstrap sql loaded")


if __name__ == "__main__":
    main()
