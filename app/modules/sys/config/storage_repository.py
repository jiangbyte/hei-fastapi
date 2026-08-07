""" Author: Charlie """

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import BusinessError, NotFoundError
from app.modules.sys.config.storage_schema import (
    StorageConfigCreateRequest,
    StorageConfigUpdateRequest,
)
from app.platform.db.models.sys_storage_config import SysStorageConfig


class StorageConfigRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: StorageConfigCreateRequest) -> SysStorageConfig:
        entity = SysStorageConfig(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, config_id: str) -> SysStorageConfig | None:
        return await self.db.get(SysStorageConfig, config_id)

    async def get_required(self, config_id: str) -> SysStorageConfig:
        entity = await self.get_by_id(config_id)
        if entity is None:
            raise NotFoundError("Storage config not found")
        return entity

    async def update(self, payload: StorageConfigUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        data = payload.model_dump(exclude={"id"}, exclude_none=True)
        for key, value in data.items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, config_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(config_ids))
        entities = list(
            (
                await self.db.execute(
                    select(SysStorageConfig).where(SysStorageConfig.id.in_(unique_ids))
                )
            )
            .scalars()
            .all()
        )
        if len(entities) != len(unique_ids):
            raise NotFoundError("Storage config not found")
        if any(entity.is_default for entity in entities):
            raise BusinessError("Cannot delete the default storage config")
        await self.db.execute(delete(SysStorageConfig).where(SysStorageConfig.id.in_(unique_ids)))
        await self.db.flush()

    async def list_all(self) -> list[SysStorageConfig]:
        stmt = select(SysStorageConfig).order_by(
            SysStorageConfig.sort_code.asc(), SysStorageConfig.name.asc()
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def set_default(self, config_id: str) -> None:
        await self.get_required(config_id)
        await self.db.execute(update(SysStorageConfig).values(is_default=False))
        await self.db.execute(
            update(SysStorageConfig).where(SysStorageConfig.id == config_id).values(is_default=True)
        )
        await self.db.flush()

    async def get_active(self) -> SysStorageConfig | None:
        stmt = select(SysStorageConfig).where(
            SysStorageConfig.is_default == True  # noqa: E712
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()
