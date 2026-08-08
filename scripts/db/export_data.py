""" Author: Charlie

导出当前数据库业务数据到 scripts/db/seed/data.sql（不含 alembic_version）。
依赖本机 Docker 容器 `dev-postgres` 中的 pg_dump，或系统 PATH 中的 pg_dump。
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


def _run_pg_dump(env: dict[str, str], out_path: Path) -> None:
    args = [
        "--data-only",
        "--inserts",
        "--column-inserts",
        "--no-owner",
        "--no-privileges",
        "--exclude-table=alembic_version",
        "-U",
        env["PGUSER"],
        "-d",
        env["PGDATABASE"],
    ]
    if shutil.which("pg_dump"):
        cmd = ["pg_dump", *args]
        proc_env = {**os.environ, **env}
        result = subprocess.run(cmd, capture_output=True, text=True, env=proc_env, check=False)
    else:
        cmd = [
            "docker",
            "exec",
            "-e",
            f"PGPASSWORD={env['PGPASSWORD']}",
            "dev-postgres",
            "pg_dump",
            *args,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "pg_dump failed")
    text = "\n".join(
        line
        for line in result.stdout.splitlines()
        if not line.startswith("\\restrict") and not line.startswith("\\unrestrict")
    ).strip()
    wrapped = (
        "-- HEI FastAPI data seed (exported from live DB)\n"
        "-- Restore after schema migrations via scripts/db/import_data.py\n\n"
        "BEGIN;\n"
        "SET session_replication_role = replica;\n\n"
        f"{text}\n\n"
        "SET session_replication_role = DEFAULT;\n"
        "COMMIT;\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(wrapped, encoding="utf-8")


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    os.chdir(project_root)
    out = project_root / "scripts" / "db" / "seed" / "data.sql"
    env = _pg_env(_load_db_url())
    _run_pg_dump(env, out)
    inserts = sum(1 for line in out.read_text(encoding="utf-8").splitlines() if line.startswith("INSERT INTO"))
    print(f"exported {out} ({inserts} inserts, {out.stat().st_size} bytes)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"export failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
