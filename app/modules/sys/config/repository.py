""" Author: Charlie """

from sqlalchemy import Select, case, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.sys.config.schema import (
    ConfigAdminPageQuery,
    ConfigBatchItem,
    ConfigCreateRequest,
    ConfigUpdateRequest,
)
from app.platform.db.models.sys_config import SysConfig


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

    async def list_by_category(self, category: str | None = None) -> list[SysConfig]:
        stmt = select(SysConfig).order_by(SysConfig.sort_code.asc(), SysConfig.id.desc())
        if category:
            stmt = stmt.where(SysConfig.category == category)
        return list((await self.db.execute(stmt)).scalars().all())

    async def batch_save(self, items: list[ConfigBatchItem]) -> None:
        """通过单条 SQL CASE WHEN 批量更新，避免 N+1 问题。"""
        if not items:
            return
        when_clauses = {item.id: item.config_value for item in items}
        id_list = list(when_clauses.keys())
        stmt = (
            update(SysConfig)
            .where(SysConfig.id.in_(id_list))
            .values(
                config_value=case(when_clauses, value=SysConfig.id, else_=SysConfig.config_value),
            )
        )
        await self.db.execute(stmt)
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
