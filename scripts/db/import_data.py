""" Author: Charlie

将 scripts/db/seed/data.sql 导入当前数据库（需表结构已存在）。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


def _load_db_url() -> str:
    project_root = Path(__file__).resolve().parents[2]
    env_path = project_root / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DB__URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("DB__URL not found in .env")


def _pg_env(url: str) -> dict[str, str]:
    normalized = (
        url.replace("postgresql+asyncpg://", "postgresql://")
        .replace("postgresql+psycopg://", "postgresql://")
    )
    parsed = urlparse(normalized)
    return {
        "PGHOST": parsed.hostname or "127.0.0.1",
        "PGPORT": str(parsed.port or 5432),
        "PGUSER": parsed.username or "postgres",
        "PGDATABASE": (parsed.path or "/").lstrip("/") or "postgres",
        "PGPASSWORD": unquote(parsed.password or ""),
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    os.chdir(project_root)
    sql_path = project_root / "scripts" / "db" / "seed" / "data.sql"
    if not sql_path.exists():
        raise RuntimeError(f"missing seed file: {sql_path}")
    env = _pg_env(_load_db_url())
    sql = sql_path.read_text(encoding="utf-8")
    if shutil.which("psql"):
        cmd = [
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            env["PGUSER"],
            "-d",
            env["PGDATABASE"],
            "-h",
            env["PGHOST"],
            "-p",
            env["PGPORT"],
        ]
        result = subprocess.run(
            cmd,
            input=sql,
            capture_output=True,
            text=True,
            env={**os.environ, **env},
            check=False,
        )
    else:
        cmd = [
            "docker",
            "exec",
            "-i",
            "-e",
            f"PGPASSWORD={env['PGPASSWORD']}",
            "dev-postgres",
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            env["PGUSER"],
            "-d",
            env["PGDATABASE"],
        ]
        result = subprocess.run(cmd, input=sql, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "psql import failed")
    print(f"imported {sql_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"import failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
