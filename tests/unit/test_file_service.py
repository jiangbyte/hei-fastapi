""" Author: Charlie

文件服务单测：使用内存假存储替代 LOCAL。
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.config.enums import StorageProvider
from app.core.config.settings import settings
from app.core.schema.base import IdQuery
from app.core.schema.datetime import format_utc_iso8601
from app.core.storage.config import StorageConfig
from app.modules.sys.file.model import SysFile
from app.modules.sys.file.schema import FileUploadRequest, ObjectNameQuery
from app.modules.sys.file.service import FileService


class _MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.config = StorageConfig(
            id="memory",
            name="memory",
            provider=StorageProvider.MINIO,
            bucket="test",
            bucket_public=True,
            base_url="https://cdn.example.com",
            is_default=True,
        )

    def upload_bytes(self, object_name: str, content: bytes, content_type: str = "") -> str:
        self.objects[object_name] = content
        return self.get_object_url(object_name)

    def delete_object(self, object_name: str) -> None:
        self.objects.pop(object_name, None)

    def get_object_url(self, object_name: str) -> str:
        return f"https://cdn.example.com/{object_name}"

    def get_presigned_url(self, object_name: str) -> str:
        return f"https://cdn.example.com/{object_name}?X-Amz-Signature=test"

    def get_object_bytes(self, object_name: str) -> bytes:
        return self.objects[object_name]


def _install_memory_storage(monkeypatch) -> _MemoryStorage:
    storage = _MemoryStorage()
    config = storage.config
    monkeypatch.setattr(
        "app.modules.sys.file.service.resolve_storage_config", lambda *a, **k: config
    )
    monkeypatch.setattr("app.modules.sys.file.service.get_storage", lambda *a, **k: storage)
    monkeypatch.setattr(settings.storage, "provider", StorageProvider.MINIO)
    return storage


async def test_file_service_upload_and_url(monkeypatch, db_session):
    storage = _install_memory_storage(monkeypatch)
    service = FileService(db_session)
    entity = await service.upload(
        FileUploadRequest(filename="avatar.png", content=b"hello", content_type="image/png")
    )
    await db_session.commit()
    assert entity.object_name.startswith("uploads/")
    assert entity.object_name.endswith(".png")
    assert entity.url == f"https://cdn.example.com/{entity.object_name}"
    assert entity.object_name in storage.objects
    assert format_utc_iso8601(entity.created_at).endswith("Z")
    assert await service.get_url(ObjectNameQuery(object_name=entity.object_name)) == entity.url
    stored = (await db_session.execute(select(SysFile).where(SysFile.id == entity.id))).scalar_one()
    assert stored.original_name == "avatar.png"
    await service.delete_by_object_name(entity.object_name)
    deleted = (
        await db_session.execute(select(SysFile).where(SysFile.id == entity.id))
    ).scalar_one_or_none()
    assert deleted is None
    assert entity.object_name not in storage.objects


async def test_file_service_download_has_content_disposition(monkeypatch, db_session):
    _install_memory_storage(monkeypatch)
    service = FileService(db_session)
    entity = await service.upload(
        FileUploadRequest(filename="报告.png", content=b"png", content_type="image/png")
    )
    await db_session.commit()
    response = await service.download_by_id(IdQuery(id=entity.id))
    assert response.body == b"png"
    assert "filename*=UTF-8''" in response.headers["Content-Disposition"]
