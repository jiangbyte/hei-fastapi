""" Author: Charlie """

from app.core.config.enums import AccountStatusEnum, AccountType
from app.core.security.password import hash_password
from app.core.security.session import SessionPayload, session_store
from app.deps.db import get_db_session
from app.modules.iam.account.model import SysAccount, SysAccountIdentity
from app.modules.iam.enums import AccountIdentityBindStatus, AccountIdentityType
from app.modules.user.admin.model import ProfileUserAdmin


async def _seed_session_admin(client, token: str, permissions: list[str]) -> SysAccount:
    override = client._transport.app.dependency_overrides[get_db_session]
    async for session in override():
        account = SysAccount(
            password_hash=hash_password("Admin@123456"),
            account_type=AccountType.ADMIN.value,
            account_status=AccountStatusEnum.ENABLED.value,
        )
        session.add(account)
        await session.flush()
        session.add(
            SysAccountIdentity(
                account_id=account.id,
                identity_type=AccountIdentityType.ACCOUNT.value,
                identifier=f"admin-{account.id}",
                verified=True,
                is_primary=True,
                bind_status=AccountIdentityBindStatus.BOUND.value,
            )
        )
        session.add(ProfileUserAdmin(account_id=account.id, name="Admin"))
        await session_store.set(
            SessionPayload(
                token=token,
                account_id=account.id,
                account_type=AccountType.ADMIN.value,
                permission_keys=permissions,
                client_ip="127.0.0.1",
                device_label="Desktop",
            ),
            ttl_seconds=3600,
        )
        await session.commit()
        return account
    raise AssertionError("Expected test database session")


async def test_session_admin_lists_and_exits_tokens(client):
    token = "session-admin-token"
    account = await _seed_session_admin(
        client,
        token,
        [
            "auth:session:analysis",
            "auth:session:page",
            "auth:session:tokenlist",
            "auth:session:tokenexit",
        ],
    )
    await session_store.set(
        SessionPayload(
            token="second-token",
            account_id=account.id,
            account_type=AccountType.ADMIN.value,
            client_ip="10.0.0.2",
            device_label="Mobile",
        ),
        ttl_seconds=3600,
    )

    analysis = await client.get(
        "/api/v1/admin/auth/sessions/analysis",
        headers={"Authorization": token},
    )
    assert analysis.status_code == 200
    assert analysis.json()["data"]["online_token_count"] == "2"

    page = await client.get(
        "/api/v1/admin/auth/sessions/page",
        headers={"Authorization": token},
    )
    assert page.status_code == 200
    assert page.json()["data"]["records"][0]["token_count"] == "2"

    tokens = await client.get(
        "/api/v1/admin/auth/sessions/tokens",
        headers={"Authorization": token},
        params={"account_type": "ADMIN", "account_id": account.id},
    )
    assert tokens.status_code == 200
    assert {item["token"] for item in tokens.json()["data"]} == {token, "second-token"}

    exit_response = await client.post(
        "/api/v1/admin/auth/sessions/token/exit",
        headers={"Authorization": token},
        json={"tokens": ["second-token"]},
    )
    assert exit_response.status_code == 200
    assert await session_store.get("second-token") is None
