from app.core.config.enums import AccountStatusEnum, AccountType
from app.core.config.settings import settings
from app.core.security.session import SessionPayload, session_store
from app.deps.db import get_db_session
from app.modules.iam.account.model import SysAccount


async def _seed_admin(client, token: str, permissions: list[str]) -> None:
    override = client._transport.app.dependency_overrides[get_db_session]
    async for session in override():
        account = SysAccount(
            password_hash="hashed",
            account_type=AccountType.ADMIN.value,
            account_status=AccountStatusEnum.ENABLED.value,
        )
        session.add(account)
        await session.flush()
        await session_store.set(
            SessionPayload(
                token=token,
                account_id=account.id,
                account_type=AccountType.ADMIN.value,
                role_ids=[],
                dept_ids=[],
                group_ids=[],
                permission_keys=permissions,
                permission_grants=[],
            ),
            ttl_seconds=3600,
        )
        await session.commit()
        break


async def test_admin_file_upload_page_detail_update_delete(client, tmp_path):
    old_provider = settings.storage.provider
    old_root = settings.storage.local_root
    old_base_url = settings.storage.base_url
    old_public_path = settings.storage.public_path
    settings.storage.provider = "local"
    settings.storage.local_root = str(tmp_path)
    settings.storage.base_url = ""
    settings.storage.public_path = "/api/v1/files"

    token = "admin-file-token"
    await _seed_admin(
        client,
        token,
        [
            "sys:file:upload",
            "sys:file:page",
            "sys:file:detail",
            "sys:file:update",
            "sys:file:delete",
        ],
    )
    headers = {"Authorization": token}

    try:
        upload_response = await client.post(
            "/api/v1/admin/sys/file/upload",
            headers=headers,
            files={"file": ("report.png", b"image-bytes", "image/png")},
        )
        assert upload_response.status_code == 200
        uploaded = upload_response.json()["data"]
        assert uploaded["original_name"] == "report.png"
        assert uploaded["content_type"] == "image/png"
        assert uploaded["url"] == f"/api/v1/files?object_name={uploaded['object_name']}"
        assert (tmp_path / uploaded["object_name"]).exists()

        page_response = await client.get(
            "/api/v1/admin/sys/file/page?current=1&size=20&original_name=report&content_type=image",
            headers=headers,
        )
        assert page_response.status_code == 200
        assert page_response.json()["data"]["total"] == 1
        file_id = page_response.json()["data"]["records"][0]["id"]

        detail_response = await client.get(
            f"/api/v1/admin/sys/file/detail?id={file_id}",
            headers=headers,
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["data"]["object_name"] == uploaded["object_name"]

        update_response = await client.post(
            "/api/v1/admin/sys/file/update",
            headers=headers,
            json={"id": file_id, "original_name": "renamed.png"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"] is None

        updated_detail_response = await client.get(
            f"/api/v1/admin/sys/file/detail?id={file_id}",
            headers=headers,
        )
        assert updated_detail_response.json()["data"]["original_name"] == "renamed.png"
        assert updated_detail_response.json()["data"]["object_name"] == uploaded["object_name"]

        delete_response = await client.post(
            "/api/v1/admin/sys/file/delete",
            headers=headers,
            json={"ids": [file_id]},
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["data"] is None
        assert not (tmp_path / uploaded["object_name"]).exists()

        empty_page_response = await client.get(
            "/api/v1/admin/sys/file/page?current=1&size=20&original_name=renamed",
            headers=headers,
        )
        assert empty_page_response.json()["data"]["total"] == 0
    finally:
        settings.storage.provider = old_provider
        settings.storage.local_root = old_root
        settings.storage.base_url = old_base_url
        settings.storage.public_path = old_public_path
