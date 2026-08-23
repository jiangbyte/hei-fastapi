""" Author: Charlie

回归：禁止在应用/测试代码中出现整库清空类危险操作。
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = (ROOT / "app", ROOT / "tests")
FORBIDDEN = (
    "metadata.drop_all",
    "Base.metadata.drop_all",
    "DROP DATABASE",
    "TRUNCATE TABLE",
    "flushall",
    "flushdb",
)


def test_no_destructive_db_wipe_apis_in_app_or_tests() -> None:
    hits: list[str] = []
    for base in SCAN_DIRS:
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for needle in FORBIDDEN:
                if needle in text:
                    # 允许本文件自身列出这些关键词
                    if path.name == "test_no_destructive_db_ops.py":
                        continue
                    hits.append(f"{path.relative_to(ROOT)}: {needle}")
    assert not hits, "forbidden destructive DB ops:\n" + "\n".join(hits)


def test_seed_sql_has_no_drop_table() -> None:
    sql = (ROOT / "scripts" / "hei_fastapi.sql").read_text(encoding="utf-8")
    for line in sql.splitlines():
        stripped = line.strip().upper()
        if stripped.startswith("DROP TABLE"):
            raise AssertionError(f"scripts/hei_fastapi.sql must not DROP TABLE: {line}")
