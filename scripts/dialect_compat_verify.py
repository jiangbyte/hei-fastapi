""" Author: Charlie

双库方言兼容验证编排：建隔离库、alembic、pytest、HTTP 冒烟。

用法（项目根目录）::

    python scripts/dialect_compat_verify.py
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.cache.keys import captcha_key  # noqa: E402
from app.core.config.enums import AccountStatusEnum, AccountType  # noqa: E402
from app.core.security.password import hash_password  # noqa: E402
from app.modules.iam.account.model import SysAccount, SysAccountIdentity  # noqa: E402
from app.modules.iam.enums import AccountIdentityType  # noqa: E402

HOST = "127.0.0.1"
MYSQL_PASS = "123456"
PG_PASS = "123456"
REDIS_PASS = "123456"
DB_NAME = "hei_fastapi_compat"
CRYPTO_KEY = "XV1rJ-UPAbWeYjprihKNS3ZCCHdBuVbIc0WXmYc70ck="
REDIS_URL = f"redis://:{quote(REDIS_PASS)}@{HOST}:6379/15"
MYSQL_URL = (
    f"mysql+aiomysql://root:{quote(MYSQL_PASS)}@{HOST}:3306/{DB_NAME}?charset=utf8mb4"
)
PG_URL = f"postgresql+asyncpg://postgres:{quote(PG_PASS)}@{HOST}:5432/{DB_NAME}"
SMOKE_PORT = 18080
KNOWN_CAPTCHA = "AB12"
REPORT_PATH = ROOT / "scripts" / "dialect_compat_report.json"


@dataclass
class RoundResult:
    dialect: str
    alembic_ok: bool = False
    pytest_exit: int | None = None
    smoke: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def _run(cmd: list[str], env: dict[str, str], *, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _base_env(db_url: str) -> dict[str, str]:
    env = os.environ.copy()
    env["DB__URL"] = db_url
    env["REDIS__URL"] = REDIS_URL
    env["APP__CONFIG_CRYPTO_KEY"] = CRYPTO_KEY
    # 避免加载本地 .env 覆盖（pydantic 仍可能读 .env；子进程用显式 env 优先）
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


async def prepare_mysql() -> None:
    admin = create_async_engine(
        f"mysql+aiomysql://root:{quote(MYSQL_PASS)}@{HOST}:3306/?charset=utf8mb4",
    )
    async with admin.begin() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS `{DB_NAME}`"))
        await conn.execute(
            text(
                f"CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    await admin.dispose()
    print("mysql: recreated", DB_NAME)


async def prepare_postgres() -> None:
    admin = create_async_engine(
        f"postgresql+asyncpg://postgres:{quote(PG_PASS)}@{HOST}:5432/postgres",
        isolation_level="AUTOCOMMIT",
    )
    async with admin.connect() as conn:
        exists = (
            await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :n"),
                {"n": DB_NAME},
            )
        ).scalar()
        if exists:
            await conn.execute(text(f'DROP DATABASE "{DB_NAME}" WITH (FORCE)'))
        await conn.execute(text(f'CREATE DATABASE "{DB_NAME}"'))
    await admin.dispose()
    print("postgres: recreated", DB_NAME)


def run_alembic(db_url: str) -> bool:
    env = _base_env(db_url)
    result = _run([sys.executable, "-m", "alembic", "upgrade", "head"], env, timeout=180)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        return False
    print("alembic: ok")
    return True


def run_pytest(db_url: str) -> int:
    env = _base_env(db_url)
    result = _run(
        [sys.executable, "-m", "pytest", "tests/unit", "tests/api", "-q", "--tb=line"],
        env,
        timeout=900,
    )
    print(result.stdout[-4000:] if result.stdout else "")
    if result.stderr:
        print(result.stderr[-2000:])
    print("pytest-exit", result.returncode)
    return result.returncode


def _encrypt_password(public_key_b64: str, password: str) -> str:
    der = base64.b64decode(public_key_b64)
    public_key = serialization.load_der_public_key(der)
    ciphertext = public_key.encrypt(
        password.encode("utf-8"),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.b64encode(ciphertext).decode("ascii")


async def seed_smoke_accounts(db_url: str) -> None:
    import app.db_models  # noqa: F401

    engine = create_async_engine(db_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await _ensure_account(session, "superadmin", "123456", AccountType.ADMIN)
        await _ensure_account(session, "user", "123456", AccountType.PORTAL)
        await session.commit()
    await engine.dispose()
    print("seed: superadmin + user")


async def _ensure_account(
    session: AsyncSession,
    identifier: str,
    password: str,
    account_type: AccountType,
) -> None:
    from sqlalchemy import select

    existing = (
        await session.execute(
            select(SysAccountIdentity).where(
                SysAccountIdentity.identifier == identifier,
                SysAccountIdentity.identity_type == AccountIdentityType.ACCOUNT.value,
            )
        )
    ).scalar_one_or_none()
    if existing:
        return
    account = SysAccount(
        password_hash=hash_password(password),
        account_type=account_type.value,
        account_status=AccountStatusEnum.ENABLED.value,
    )
    session.add(account)
    await session.flush()
    session.add(
        SysAccountIdentity(
            account_id=account.id,
            identity_type=AccountIdentityType.ACCOUNT.value,
            identifier=identifier,
            verified=True,
            is_primary=True,
        )
    )


async def inject_captcha(redis_url: str, captcha_id: str, plain: str) -> None:
    from redis.asyncio import Redis

    redis = Redis.from_url(redis_url, decode_responses=False)
    try:
        await redis.setex(captcha_key(captcha_id), 120, hash_password(plain.lower()))
    finally:
        await redis.aclose()


async def smoke_http(db_url: str) -> dict:
    await seed_smoke_accounts(db_url)
    env = _base_env(db_url)
    env["SWAGGER__ENABLED"] = "false"
    base = f"http://127.0.0.1:{SMOKE_PORT}"
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(SMOKE_PORT),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    results: dict[str, object] = {"endpoints": {}}
    try:
        await _wait_live(base)
        async with httpx.AsyncClient(base_url=base, timeout=30.0) as client:
            for path in (
                "/api/v1/internal/health/live",
                "/api/v1/internal/health/ready",
            ):
                r = await client.get(path)
                results["endpoints"][path] = {"status": r.status_code, "ok": r.status_code == 200}

            admin_login = await _login_flow(client, "admin", "superadmin", "123456")
            results["admin_login"] = admin_login
            if admin_login.get("token"):
                token = str(admin_login["token"])
                headers = {"Authorization": token}
                for path in (
                    "/api/v1/admin/me",
                    "/api/v1/admin/sys/dicts/page?page=1&size=10",
                    "/api/v1/admin/sys/banners/page?page=1&size=10",
                    "/api/v1/admin/sys/resources/page?page=1&size=10",
                ):
                    r = await client.get(path, headers=headers)
                    results["endpoints"][path] = {
                        "status": r.status_code,
                        "body_code": _api_code(r),
                    }

            portal_login = await _login_flow(client, "portal", "user", "123456")
            results["portal_login"] = portal_login
            if portal_login.get("token"):
                token = str(portal_login["token"])
                r = await client.get("/api/v1/portal/me", headers={"Authorization": token})
                results["endpoints"]["/api/v1/portal/me"] = {
                    "status": r.status_code,
                    "body_code": _api_code(r),
                }
    except Exception as ex:  # noqa: BLE001
        results["error"] = f"{type(ex).__name__}: {ex}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
    return results


async def _wait_live(base: str, *, attempts: int = 40) -> None:
    async with httpx.AsyncClient(timeout=2.0) as client:
        for _ in range(attempts):
            try:
                r = await client.get(f"{base}/api/v1/internal/health/live")
                if r.status_code == 200:
                    return
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(0.5)
    raise RuntimeError("uvicorn did not become ready")


def _api_code(response: httpx.Response) -> object:
    try:
        return response.json().get("code")
    except Exception:  # noqa: BLE001
        return None


async def _login_flow(
    client: httpx.AsyncClient,
    scope: str,
    account: str,
    password: str,
) -> dict:
    captcha = (await client.get(f"/api/v1/{scope}/captcha")).json()["data"]
    captcha_id = captcha["captcha_id"]
    await inject_captcha(REDIS_URL, captcha_id, KNOWN_CAPTCHA)
    key = (await client.get(f"/api/v1/{scope}/password-key")).json()["data"]
    encrypted = _encrypt_password(key["public_key"], password)
    resp = await client.post(
        f"/api/v1/{scope}/login",
        json={
            "account": account,
            "password": encrypted,
            "identity_type": "ACCOUNT",
            "remember_me": False,
            "password_key_id": key["key_id"],
            "captcha_id": captcha_id,
            "captcha_value": KNOWN_CAPTCHA,
        },
    )
    data = {}
    try:
        data = resp.json().get("data") or {}
    except Exception:  # noqa: BLE001
        pass
    return {
        "status": resp.status_code,
        "code": _api_code(resp),
        "token": data.get("token"),
        "message": (resp.json().get("message") if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:200]),
    }


async def run_round(dialect: str, db_url: str) -> RoundResult:
    result = RoundResult(dialect=dialect)
    print("\n========", dialect, "========")
    try:
        if dialect == "mysql":
            await prepare_mysql()
        else:
            await prepare_postgres()
        result.alembic_ok = run_alembic(db_url)
        if not result.alembic_ok:
            result.errors.append("alembic failed")
            return result
        result.pytest_exit = run_pytest(db_url)
        # smoke 需要 alembic 表结构；pytest 会 drop/create 同一库，需再 upgrade
        if dialect == "mysql":
            await prepare_mysql()
        else:
            await prepare_postgres()
        if not run_alembic(db_url):
            result.errors.append("alembic recreate for smoke failed")
            return result
        result.smoke = await smoke_http(db_url)
    except Exception as ex:  # noqa: BLE001
        result.errors.append(f"{type(ex).__name__}: {ex}")
        print("round-error", ex)
    return result


def main() -> int:
    started = time.time()
    mysql_result = asyncio.run(run_round("mysql", MYSQL_URL))
    pg_result = asyncio.run(run_round("postgresql", PG_URL))
    report = {
        "elapsed_seconds": round(time.time() - started, 1),
        "mysql": mysql_result.__dict__,
        "postgresql": pg_result.__dict__,
        "summary": {
            "mysql_pytest_ok": mysql_result.pytest_exit == 0,
            "postgresql_pytest_ok": pg_result.pytest_exit == 0,
            "mysql_alembic_ok": mysql_result.alembic_ok,
            "postgresql_alembic_ok": pg_result.alembic_ok,
            "mysql_admin_login_ok": (mysql_result.smoke.get("admin_login") or {}).get("status")
            == 200,
            "postgresql_admin_login_ok": (pg_result.smoke.get("admin_login") or {}).get("status")
            == 200,
        },
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n======== SUMMARY ========")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print("report:", REPORT_PATH)
    ok = all(
        [
            report["summary"]["mysql_pytest_ok"],
            report["summary"]["postgresql_pytest_ok"],
            report["summary"]["mysql_alembic_ok"],
            report["summary"]["postgresql_alembic_ok"],
            report["summary"]["mysql_admin_login_ok"],
            report["summary"]["postgresql_admin_login_ok"],
        ]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
