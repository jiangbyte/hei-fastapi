from sqlalchemy import select

from app.core.config.enums import AccountType
from app.core.config.settings import settings
from app.core.schema.datetime import format_utc_iso8601
from app.core.security.session import SessionPayload
from app.modules.sys.file.model import SysFile
from app.modules.sys.file.schema import FileUploadRequest, ObjectNameQuery
from app.modules.sys.file.service import FileService
from app.modules.user.admin.model import AdminUserProfile
from app.modules.user.admin.service import AdminUserProfileService
from app.modules.user.portal.model import PortalUserProfile
from app.modules.user.portal.service import PortalUserProfileService


async def test_file_service_upload_and_url(tmp_path, db_session):
    old_provider = settings.storage.provider
    old_root = settings.storage.local_root
    old_base_url = settings.storage.base_url
    old_public_path = settings.storage.public_path
    settings.storage.provider = "local"
    settings.storage.local_root = str(tmp_path)
    settings.storage.base_url = ""
    settings.storage.public_path = "/api/v1/files"
    try:
        service = FileService(db_session)
        entity = await service.upload(
            FileUploadRequest(filename="avatar.png", content=b"hello", content_type="image/png")
        )
        await db_session.commit()
        assert entity.object_name.startswith("uploads/")
        assert entity.object_name.endswith(".png")
        assert entity.url == f"/api/v1/files?object_name={entity.object_name}"
        assert str(tmp_path) not in entity.url
        assert format_utc_iso8601(entity.created_at).endswith("Z")
        assert await service.get_url(ObjectNameQuery(object_name=entity.object_name)) == entity.url
        stored = (
            await db_session.execute(select(SysFile).where(SysFile.id == entity.id))
        ).scalar_one()
        assert stored.original_name == "avatar.png"
        await service.delete_by_object_name(entity.object_name)
        deleted = (
            await db_session.execute(select(SysFile).where(SysFile.id == entity.id))
        ).scalar_one_or_none()
        assert deleted is None
        assert not (tmp_path / entity.object_name).exists()
    finally:
        settings.storage.provider = old_provider
        settings.storage.local_root = old_root
        settings.storage.base_url = old_base_url
        settings.storage.public_path = old_public_path


async def test_admin_avatar_update_deletes_previous_file(tmp_path, db_session):
    old_provider = settings.storage.provider
    old_root = settings.storage.local_root
    old_base_url = settings.storage.base_url
    old_public_path = settings.storage.public_path
    settings.storage.provider = "local"
    settings.storage.local_root = str(tmp_path)
    settings.storage.base_url = ""
    settings.storage.public_path = "/api/v1/files"
    try:
        file_service = FileService(db_session)
        old_avatar = await file_service.upload(
            FileUploadRequest(
                filename="old-avatar.png",
                content=b"old",
                content_type="image/png",
                category="avatars",
                object_name="avatars/admin/account-1/old-avatar.png",
            )
        )
        db_session.add(AdminUserProfile(account_id="account-1", avatar=old_avatar.object_name))
        await db_session.commit()

        response = await AdminUserProfileService(db_session).update_current_avatar(
            content=b"new",
            content_type="image/png",
            session=SessionPayload(
                token="token",
                account_id="account-1",
                account_type=AccountType.ADMIN,
            ),
        )

        profile = await db_session.get(AdminUserProfile, "account-1")
        old_record = (
            await db_session.execute(select(SysFile).where(SysFile.id == old_avatar.id))
        ).scalar_one_or_none()
        new_record = (
            await db_session.execute(select(SysFile).where(SysFile.id == response.file_id))
        ).scalar_one_or_none()
        assert profile is not None
        assert profile.avatar == response.object_name
        assert old_record is None
        assert new_record is not None
        assert not (tmp_path / old_avatar.object_name).exists()
        assert (tmp_path / response.object_name).exists()
    finally:
        settings.storage.provider = old_provider
        settings.storage.local_root = old_root
        settings.storage.base_url = old_base_url
        settings.storage.public_path = old_public_path


async def test_portal_avatar_update_deletes_previous_file(tmp_path, db_session):
    old_provider = settings.storage.provider
    old_root = settings.storage.local_root
    old_base_url = settings.storage.base_url
    old_public_path = settings.storage.public_path
    settings.storage.provider = "local"
    settings.storage.local_root = str(tmp_path)
    settings.storage.base_url = ""
    settings.storage.public_path = "/api/v1/files"
    try:
        file_service = FileService(db_session)
        old_avatar = await file_service.upload(
            FileUploadRequest(
                filename="old-avatar.png",
                content=b"old",
                content_type="image/png",
                category="avatars",
                object_name="avatars/portal/account-2/old-avatar.png",
            )
        )
        db_session.add(PortalUserProfile(account_id="account-2", avatar=old_avatar.object_name))
        await db_session.commit()

        response = await PortalUserProfileService(db_session).update_current_avatar(
            content=b"new",
            content_type="image/png",
            session=SessionPayload(
                token="token",
                account_id="account-2",
                account_type=AccountType.PORTAL,
            ),
        )

        profile = await db_session.get(PortalUserProfile, "account-2")
        old_record = (
            await db_session.execute(select(SysFile).where(SysFile.id == old_avatar.id))
        ).scalar_one_or_none()
        new_record = (
            await db_session.execute(select(SysFile).where(SysFile.id == response.file_id))
        ).scalar_one_or_none()
        assert profile is not None
        assert profile.avatar == response.object_name
        assert old_record is None
        assert new_record is not None
        assert not (tmp_path / old_avatar.object_name).exists()
        assert (tmp_path / response.object_name).exists()
    finally:
        settings.storage.provider = old_provider
        settings.storage.local_root = old_root
        settings.storage.base_url = old_base_url
        settings.storage.public_path = old_public_path
