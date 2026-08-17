""" Author: Charlie

双库 e2e 编排（对齐 hei-gin）：导入种子 → 启 uvicorn → 扫路由报告。

用法::

    python scripts/run_dialect_e2e.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
PASS = "123456"
DB = "hei_fastapi_compat"
PORT = 18080
REDIS_URL = f"redis://:{quote(PASS)}@{HOST}:6379/15"
CRYPTO = "XV1rJ-UPAbWeYjprihKNS3ZCCHdBuVbIc0WXmYc70ck="
MYSQL_URL = f"mysql+aiomysql://root:{quote(PASS)}@{HOST}:3306/{DB}?charset=utf8mb4"
PG_URL = f"postgresql+asyncpg://postgres:{quote(PASS)}@{HOST}:5432/{DB}"


def _env(db_url: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "DB__URL": db_url,
            "REDIS__URL": REDIS_URL,
            "APP__CONFIG_CRYPTO_KEY": CRYPTO,
            "SWAGGER__ENABLED": "true",
            "JOB__SCAN_INTERVAL_MS": "60000",
            "E2E_DISABLE_RATE_LIMIT": "1",
            "PYTHONUNBUFFERED": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    return env


def prepare_postgres() -> None:
    subprocess.run(
        [
            "wsl",
            "docker",
            "exec",
            "-i",
            "dev-postgres",
            "psql",
            "-U",
            "postgres",
            "-c",
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='{DB}' AND pid <> pg_backend_pid();",
        ],
        check=False,
        cwd=ROOT,
    )
    subprocess.run(
        ["wsl", "docker", "exec", "-i", "dev-postgres", "psql", "-U", "postgres", "-c", f'DROP DATABASE IF EXISTS "{DB}";'],
        check=False,
        cwd=ROOT,
    )
    subprocess.run(
        ["wsl", "docker", "exec", "-i", "dev-postgres", "psql", "-U", "postgres", "-c", f'CREATE DATABASE "{DB}";'],
        check=True,
        cwd=ROOT,
    )
    sql = (ROOT / "scripts" / "db.sql").read_bytes()
    proc = subprocess.run(
        ["wsl", "docker", "exec", "-i", "dev-postgres", "psql", "-U", "postgres", "-d", DB, "-v", "ON_ERROR_STOP=1"],
        input=sql,
        cwd=ROOT,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("postgres seed import failed")
    print("postgres: seeded", DB)


def prepare_mysql() -> None:
    mysql_sql = ROOT / "scripts" / "db.mysql.sql"
    if not mysql_sql.exists():
        raise RuntimeError("scripts/db.mysql.sql missing; run pg2mysql first")
    ddl = (
        f"DROP DATABASE IF EXISTS {DB}; "
        f"CREATE DATABASE {DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    )
    subprocess.run(
        [
            "wsl",
            "docker",
            "exec",
            "-i",
            "dev-mysql",
            "mysql",
            "-uroot",
            f"-p{PASS}",
            "-e",
            ddl,
        ],
        check=True,
        cwd=ROOT,
    )
    sql = mysql_sql.read_bytes()
    proc = subprocess.run(
        ["wsl", "docker", "exec", "-i", "dev-mysql", "mysql", "-uroot", f"-p{PASS}", DB],
        input=sql,
        cwd=ROOT,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("mysql seed import failed")
    print("mysql: seeded", DB)


def run_e2e(dialect: str, db_url: str) -> dict:
    if dialect == "mysql":
        prepare_mysql()
    else:
        prepare_postgres()

    env = _env(db_url)
    base = f"http://127.0.0.1:{PORT}"
    out = ROOT / "scripts" / "e2e" / f"report-{dialect}.json"
    log_path = ROOT / "scripts" / "e2e" / f"uvicorn-{dialect}.log"
    log_fp = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        env=env,
        stdout=log_fp,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait(base)
        e2e = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.e2e",
                "--base",
                base,
                "--redis",
                REDIS_URL,
                "--out",
                str(out),
            ],
            cwd=ROOT,
            env=env,
            check=False,
        )
        summary = {}
        if out.exists():
            summary = json.loads(out.read_text(encoding="utf-8"))
        return {
            "dialect": dialect,
            "e2e_exit": e2e.returncode,
            "report": str(out),
            "admin_login_ok": summary.get("admin_login_ok"),
            "portal_login_ok": summary.get("portal_login_ok"),
            "fail_5xx": summary.get("fail_5xx"),
            "hard_fail": summary.get("hard_fail"),
            "out_pass": (summary.get("out_cases") or {}).get("pass"),
            "out_total": (summary.get("out_cases") or {}).get("total"),
            "in_pass": (summary.get("in_cases") or {}).get("pass"),
            "in_total": (summary.get("in_cases") or {}).get("total"),
            "crud_pass": (summary.get("crud_cases") or {}).get("pass"),
            "crud_total": (summary.get("crud_cases") or {}).get("total"),
            "contract": summary.get("contract"),
            "schema_fails": len(summary.get("schema_fails") or []),
        }
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_fp.close()


def _wait(base: str, attempts: int = 60) -> None:
    import urllib.request

    for _ in range(attempts):
        try:
            with urllib.request.urlopen(base + "/api/v1/internal/health/live", timeout=2) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("uvicorn not ready")


def main() -> int:
    started = time.time()
    results = []
    for dialect, url in (("mysql", MYSQL_URL), ("postgresql", PG_URL)):
        print(f"\n===== {dialect} =====")
        results.append(run_e2e(dialect, url))
    report = {"elapsed_seconds": round(time.time() - started, 1), "rounds": results}
    path = ROOT / "scripts" / "e2e" / "report-summary.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("summary:", path)
    ok = all(r.get("e2e_exit") == 0 for r in results)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
