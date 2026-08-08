""" Author: Charlie """

from app.core.config.enums import AccountStatusEnum, AccountType
from app.core.security.session import SessionPayload, session_store
from app.modules.iam.account.model import SysAccount
from app.modules.sys.file.model import SysFile


async def test_admin_file_list_uses_current_size_total_pages_records(client):
    override = client._transport.app.dependency_overrides
    get_db_session = next(iter(override))

    async for session in override[get_db_session]():
        account_id = "admin-pager-id"
        account = SysAccount(
            id=account_id,
            password_hash="hashed",
            account_type=AccountType.ADMIN.value,
            account_status=AccountStatusEnum.ENABLED.value,
        )
        file = SysFile(
            object_name="uploads/20260617/demo.txt",
            original_name="demo.txt",
            storage_provider="local",
            bucket=None,
            content_type="text/plain",
            size=4,
            url="http://testserver/storage/uploads/20260617/demo.txt",
            created_by=account_id,
        )
        session.add_all([account, file])
        await session.flush()
        await session_store.set(
            SessionPayload(
                token="admin-pagination-token",
                account_id=account_id,
                account_type=AccountType.ADMIN.value,
                role_ids=[],
                dept_ids=[],
                group_ids=[],
                permission_keys=["sys:file:page"],
                permission_grants=[],
            ),
            ttl_seconds=3600,
        )
        await session.commit()
        break

    response = await client.get(
        "/api/v1/admin/sys/file/page?current=1&size=20",
        headers={"Authorization": "admin-pagination-token"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["current"] == "1"
    assert data["size"] == "20"
    assert data["total"] == "1"
    assert data["pages"] == "1"
    assert isinstance(data["records"], list)
    assert data["records"][0]["object_name"] == "uploads/20260617/demo.txt"
    assert "page" not in data
    assert "page_size" not in data
    assert "items" not in data
