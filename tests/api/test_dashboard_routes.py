""" Author: Charlie """

from app.core.config.enums import AccountStatusEnum, AccountType
from app.core.security.password import hash_password
from app.core.security.session import SessionPayload, session_store
from app.deps.db import get_db_session
from app.modules.iam.account.model import SysAccount


async def test_dashboard_overview_returns_real_shape(client):
    override = client._transport.app.dependency_overrides[get_db_session]
    async for session in override():
        account = SysAccount(
            password_hash=hash_password("Admin@123456"),
            account_type=AccountType.ADMIN.value,
            account_status=AccountStatusEnum.ENABLED.value,
        )
        session.add(account)
        await session.flush()
        await session_store.set(
            SessionPayload(
                token="dashboard-token",
                account_id=account.id,
                account_type=AccountType.ADMIN.value,
                permission_keys=["dashboard:overview:view"],
            ),
            ttl_seconds=3600,
        )
        await session.commit()
        break

    response = await client.get(
        "/api/v1/admin/dashboard/overview",
        headers={"Authorization": "dashboard-token"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data.keys()) == {
        "summary",
        "accounts",
        "iam",
        "ops_today",
        "trends",
        "files",
    }
    assert set(data["summary"].keys()) == {
        "account_total",
        "online_sessions",
        "file_total",
        "storage_bytes",
    }
    assert set(data["accounts"].keys()) == {"enabled", "disabled", "today_new", "by_type"}
    assert set(data["iam"].keys()) == {
        "role_count",
        "dept_count",
        "group_count",
        "menu_count",
    }
    assert set(data["ops_today"].keys()) == {
        "audit_total",
        "audit_failed",
        "feedback_pending",
    }
    assert set(data["trends"].keys()) == {"account_trend", "audit_trend"}
    assert len(data["trends"]["account_trend"]) == 7
    assert len(data["trends"]["audit_trend"]) == 7
    assert "by_content_type" in data["files"]
    assert "metrics" not in data
    assert "account_trend" not in data
    assert "file_type_share" not in data
