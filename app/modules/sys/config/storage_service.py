""" Author: Charlie """

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schema.base import IdQuery, IdsRequest, to_schema
from app.modules.sys.config.storage_repository import StorageConfigRepository
from app.modules.sys.config.storage_schema import (
    StorageConfigCreateRequest,
    StorageConfigSetDefaultRequest,
    StorageConfigUpdateRequest,
    SysStorageConfigSchema,
)
from app.platform.config.crypto import encrypt_storage_value
from app.platform.config.sync import reload_and_publish
from app.platform.db.models.sys_storage_config import SysStorageConfig
from app.platform.db.transaction import transactional


def _redact_secrets(
    schema: SysStorageConfigSchema, *, has_access: bool, has_secret: bool
) -> SysStorageConfigSchema:
    """不向 API 客户端返回解密后的 AK/SK。"""
    schema.access_key = None
    schema.secret_key = None
    schema.access_key_set = has_access
    schema.secret_key_set = has_secret
    return schema


class StorageConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StorageConfigRepository(db)

    async def create(self, payload: StorageConfigCreateRequest) -> None:
        if payload.access_key:
            payload.access_key = encrypt_storage_value("access_key", payload.access_key)
        if payload.secret_key:
            payload.secret_key = encrypt_storage_value("secret_key", payload.secret_key)
        async with transactional(self.db):
            if payload.is_default:
                await self.db.execute(update(SysStorageConfig).values(is_default=False))
            entity = await self.repo.create(payload)
            if payload.is_default:
                await self.db.execute(
                    update(SysStorageConfig)
                    .where(SysStorageConfig.id == entity.id)
                    .values(is_default=True)
                )
        await reload_and_publish("sys_storage_config.create")

    async def update(self, payload: StorageConfigUpdateRequest) -> None:
        # 空字符串 / None 表示前端未改密钥，跳过更新，保持 DB 加密值不变
        payload.access_key = (
            encrypt_storage_value("access_key", payload.access_key) if payload.access_key else None
        )
        payload.secret_key = (
            encrypt_storage_value("secret_key", payload.secret_key) if payload.secret_key else None
        )
        async with transactional(self.db):
            if payload.is_default is True:
                await self.db.execute(update(SysStorageConfig).values(is_default=False))
            await self.repo.update(payload)
            if payload.is_default is True:
                await self.db.execute(
                    update(SysStorageConfig)
                    .where(SysStorageConfig.id == payload.id)
                    .values(is_default=True)
                )
        await reload_and_publish("sys_storage_config.update")

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)
        await reload_and_publish("sys_storage_config.delete")

    async def detail(self, query: IdQuery) -> SysStorageConfigSchema:
        entity = await self.repo.get_required(query.id)
        schema = to_schema(SysStorageConfigSchema, entity)
        return _redact_secrets(
            schema,
            has_access=bool(entity.access_key),
            has_secret=bool(entity.secret_key),
        )

    async def list_all(self) -> list[SysStorageConfigSchema]:
        items = await self.repo.list_all()
        schemas: list[SysStorageConfigSchema] = []
        for entity in items:
            schema = to_schema(SysStorageConfigSchema, entity)
            schemas.append(
                _redact_secrets(
                    schema,
                    has_access=bool(entity.access_key),
                    has_secret=bool(entity.secret_key),
                )
            )
        return schemas

    async def set_default(self, payload: StorageConfigSetDefaultRequest) -> None:
        async with transactional(self.db):
            await self.repo.set_default(payload.id)
        await reload_and_publish("sys_storage_config.set_default")
