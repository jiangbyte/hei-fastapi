from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.modules.sys.config.repository import ConfigRepository
from app.modules.sys.config.schema import (
    CategoryQuery,
    ConfigAdminPageQuery,
    ConfigBatchSaveRequest,
    ConfigCreateRequest,
    ConfigUpdateRequest,
    SysConfigSchema,
)
from app.platform.config.crypto import decrypt_config_value, encrypt_config_value, is_sensitive
from app.platform.config.sync import reload_and_publish
from app.platform.db.transaction import transactional


class ConfigService:
    """系统配置服务，负责管理端配置维护。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ConfigRepository(db)

    async def create(self, payload: ConfigCreateRequest) -> None:
        payload.config_value = encrypt_config_value(payload.config_key, payload.config_value)
        async with transactional(self.db):
            await self.repo.create(payload)
        await reload_and_publish("sys_config.create")

    async def update(self, payload: ConfigUpdateRequest) -> None:
        payload.config_value = encrypt_config_value(payload.config_key, payload.config_value)
        async with transactional(self.db):
            await self.repo.update(payload)
        await reload_and_publish("sys_config.update")

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)
        await reload_and_publish("sys_config.delete")

    async def detail(self, query: IdQuery) -> SysConfigSchema:
        schema = to_schema(SysConfigSchema, await self.repo.get_required(query.id))
        schema.config_value = decrypt_config_value(schema.config_key, schema.config_value) or ""
        return schema

    async def list_by_category(self, query: CategoryQuery) -> list[SysConfigSchema]:
        items = await self.repo.list_by_category(query.category)
        schemas = to_schema_list(SysConfigSchema, items)
        for s in schemas:
            s.config_value = decrypt_config_value(s.config_key, s.config_value) or ""
        return schemas

    async def batch_save(self, payload: ConfigBatchSaveRequest) -> None:
        items_to_save = []
        for item in payload.items:
            if is_sensitive(item.config_key):
                if not item.config_value:
                    continue  # 密码字段传空表示不修改，保留 DB 原值
                item.config_value = encrypt_config_value(item.config_key, item.config_value)
            items_to_save.append(item)
        if not items_to_save:
            return
        async with transactional(self.db):
            await self.repo.batch_save(items_to_save)
        await reload_and_publish("sys_config.batch_save")

    async def page_admin(self, query: ConfigAdminPageQuery) -> PageData[SysConfigSchema]:
        items, total = await self.repo.page_admin(query)
        schemas = to_schema_list(SysConfigSchema, items)
        for s in schemas:
            if is_sensitive(s.config_key):
                s.config_value = ""
        return build_page(query.pagination, total, schemas)
