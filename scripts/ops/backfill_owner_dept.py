#!/usr/bin/env python3
""" Author: Charlie

幂等回填 biz owner_dept_id（来自 ACCOUNT_DEPT 关系）。

优先通过 alembic 迁移 d4e5f6a7b8c9 执行；本脚本供运维重复运行。
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config.settings import settings

TABLES = (
    "cg_test_activity",
    "cg_test_catalog",
    "cg_test_order",
    "cg_test_knowledge_category",
)


async def backfill(dry_run: bool = False) -> None:
    engine = create_async_engine(settings.db.url)
    async with engine.begin() as conn:
        for table in TABLES:
            exists = await conn.scalar(
                text("SELECT 1 FROM information_schema.tables WHERE table_name = :t"),
                {"t": table},
            )
            # SQLite 回退：尝试 pragma
            if exists is None:
                try:
                    await conn.execute(text(f"SELECT owner_dept_id FROM {table} LIMIT 0"))
                except Exception:
                    print(f"skip missing table: {table}")
                    continue
            sql = text(
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
            if dry_run:
                print(f"would run backfill on {table}")
                continue
            result = await conn.execute(sql)
            print(f"{table}: rowcount={result.rowcount}")
    await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(backfill(dry_run=args.dry_run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
