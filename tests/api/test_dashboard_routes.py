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
    metric_keys = {item["key"] for item in data["metrics"]}
    assert metric_keys >= {"accounts", "online_sessions", "files"}
    assert all("title" not in item for item in data["metrics"])
    assert all("unit" not in item for item in data["metrics"])
    assert "audits" not in metric_keys
    assert "todos" not in metric_keys
    assert "messages" not in metric_keys
    assert "banners" not in metric_keys
    assert "notifications" not in metric_keys
    assert len(data["account_trend"]) == 7
    assert "audit_trend" not in data
    assert "todo_status" not in data
    assert "banner_status" not in data
    assert "recent_activities" not in data
