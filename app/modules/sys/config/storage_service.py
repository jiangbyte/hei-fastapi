from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.modules.sys.config.storage_repository import StorageConfigRepository
from app.modules.sys.config.storage_schema import (
    StorageConfigCreateRequest,
    StorageConfigSetDefaultRequest,
    StorageConfigUpdateRequest,
    SysStorageConfigSchema,
)
from app.platform.config.crypto import decrypt_storage_value, encrypt_storage_value
from app.platform.config.sync import reload_and_publish
from app.platform.db.models.sys_storage_config import SysStorageConfig
from app.platform.db.transaction import transactional


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
                await self.db.execute(
                    update(SysStorageConfig).values(is_default=False)
                )
            entity = await self.repo.create(payload)
            if payload.is_default:
                await self.db.execute(
                    update(SysStorageConfig)
                    .where(SysStorageConfig.id == entity.id)
                    .values(is_default=True)
                )
        await reload_and_publish("sys_storage_config.create")

    async def update(self, payload: StorageConfigUpdateRequest) -> None:
        # 空字符串表示前端未填写（脱敏回显），跳过更新，保持 DB 加密值不变
        payload.access_key = (
            encrypt_storage_value("access_key", payload.access_key)
            if payload.access_key
            else None
        )
        payload.secret_key = (
            encrypt_storage_value("secret_key", payload.secret_key)
            if payload.secret_key
            else None
        )
        async with transactional(self.db):
            if payload.is_default is True:
                await self.db.execute(
                    update(SysStorageConfig).values(is_default=False)
                )
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
        schema = to_schema(
            SysStorageConfigSchema,
            await self.repo.get_required(query.id),
        )
        schema.access_key = decrypt_storage_value("access_key", schema.access_key) or ""
        schema.secret_key = decrypt_storage_value("secret_key", schema.secret_key) or ""
        return schema

    async def list_all(self) -> list[SysStorageConfigSchema]:
        items = await self.repo.list_all()
        schemas = to_schema_list(SysStorageConfigSchema, items)
        for s in schemas:
            s.access_key = decrypt_storage_value("access_key", s.access_key) or ""
            s.secret_key = decrypt_storage_value("secret_key", s.secret_key) or ""
        return schemas

    async def set_default(self, payload: StorageConfigSetDefaultRequest) -> None:
        async with transactional(self.db):
            await self.repo.set_default(payload.id)
        await reload_and_publish("sys_storage_config.set_default")
