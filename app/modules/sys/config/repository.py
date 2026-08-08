""" Author: Charlie """

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.sys.config.schema import (
    ConfigAdminPageQuery,
    ConfigBatchItem,
    ConfigCreateRequest,
    ConfigUpdateRequest,
)
from app.platform.db.models.sys_config import SysConfig
from app.platform.id_generator.snowflake import generate_snowflake_id


class ConfigRepository:
    """系统配置仓储，负责配置数据持久化和查询。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: ConfigCreateRequest) -> None:
        entity = SysConfig(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()

    async def get_by_id(self, config_id: str) -> SysConfig | None:
        return await self.db.get(SysConfig, config_id)

    async def get_required(self, config_id: str) -> SysConfig:
        entity = await self.get_by_id(config_id)
        if entity is None:
            raise NotFoundError("Config not found")
        return entity

    async def update(self, payload: ConfigUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        data = payload.model_dump(exclude={"id"})
        for key, value in data.items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, config_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(config_ids))
        stmt = select(SysConfig.id).where(SysConfig.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("Config not found")
        await self.db.execute(delete(SysConfig).where(SysConfig.id.in_(unique_ids)))

    async def list_by_category(
        self,
        category: str | None = None,
        scope: str | None = None,
    ) -> list[SysConfig]:
        stmt = select(SysConfig).order_by(SysConfig.sort_code.asc(), SysConfig.id.desc())
        if category:
            stmt = stmt.where(SysConfig.category == category)
        if scope:
            stmt = stmt.where(SysConfig.scope == scope)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_by_key(self, config_key: str) -> SysConfig | None:
        stmt = select(SysConfig).where(SysConfig.config_key == config_key)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def batch_save(self, items: list[ConfigBatchItem]) -> None:
        """按 config_key upsert。"""
        if not items:
            return
        keys = [item.config_key for item in items]
        stmt = select(SysConfig).where(SysConfig.config_key.in_(keys))
        existing = {
            row.config_key: row
            for row in (await self.db.execute(stmt)).scalars().all()
        }
        for item in items:
            entity = existing.get(item.config_key)
            data = item.model_dump(exclude_unset=True)
            if entity is None:
                self.db.add(
                    SysConfig(
                        id=generate_snowflake_id(),
                        config_key=item.config_key,
                        config_value=item.config_value,
                        category=item.category,
                        remark=item.remark,
                        value_type=item.value_type or "STRING",
                        label=item.label,
                        scope=item.scope,
                        scene=item.scene,
                        is_builtin=bool(item.is_builtin) if item.is_builtin is not None else False,
                    )
                )
                continue
            entity.config_value = item.config_value
            if item.category is not None:
                entity.category = item.category
            if item.remark is not None:
                entity.remark = item.remark
            if item.value_type is not None:
                entity.value_type = item.value_type
            if "label" in data:
                entity.label = item.label
            if "scope" in data:
                entity.scope = item.scope
            if "scene" in data:
                entity.scene = item.scene
            if item.is_builtin is not None:
                entity.is_builtin = bool(item.is_builtin)
        await self.db.flush()

    async def page_admin(self, query: ConfigAdminPageQuery) -> tuple[list[SysConfig], int]:
        stmt: Select[tuple[SysConfig]] = select(SysConfig)
        count_stmt = select(func.count(SysConfig.id))
        filters = []
        if query.config_key:
            filters.append(SysConfig.config_key.ilike(f"%{query.config_key}%"))
        if query.category:
            filters.append(SysConfig.category.ilike(f"%{query.category}%"))
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(SysConfig.sort_code.asc(), SysConfig.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total
