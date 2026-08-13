""" Author: Charlie

系统配置服务层：配置维护、敏感值加解密、同步发布与批量保存。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import BusinessError
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
        """绑定会话并初始化仓储。"""
        self.db = db
        self.repo = ConfigRepository(db)

    async def create(self, payload: ConfigCreateRequest) -> None:
        """加密敏感值后创建配置并重新加载发布。"""
        payload.config_value = encrypt_config_value(payload.config_key, payload.config_value)
        async with transactional(self.db):
            await self.repo.create(payload)
        await reload_and_publish("sys_config.create")

    async def update(self, payload: ConfigUpdateRequest) -> None:
        """校验内置配置约束，加密敏感值后更新并重新加载发布。"""
        entity = await self.repo.get_required(payload.id)
        if entity.is_builtin and payload.scene and payload.scene != entity.scene:
            raise BusinessError("内置配置不可修改场景编码")
        if entity.is_builtin:
            payload.is_builtin = True
            payload.scene = entity.scene
            payload.scope = entity.scope or payload.scope
        payload.config_value = encrypt_config_value(payload.config_key, payload.config_value)
        async with transactional(self.db):
            await self.repo.update(payload)
        await reload_and_publish("sys_config.update")

    async def delete(self, payload: IdsRequest) -> None:
        """拒绝删除内置配置，删除后重新加载发布。"""
        async with transactional(self.db):
            unique_ids = list(dict.fromkeys(payload.ids))
            entities = []
            for config_id in unique_ids:
                entities.append(await self.repo.get_required(config_id))
            builtin = [e.config_key for e in entities if e.is_builtin]
            if builtin:
                raise BusinessError(f"内置配置不可删除: {', '.join(builtin)}")
            await self.repo.delete_many(unique_ids)
        await reload_and_publish("sys_config.delete")

    async def detail(self, query: IdQuery) -> SysConfigSchema:
        """查询配置详情并解密敏感值。"""
        schema = to_schema(SysConfigSchema, await self.repo.get_required(query.id))
        schema.config_value = decrypt_config_value(schema.config_key, schema.config_value) or ""
        return schema

    async def list_by_category(self, query: CategoryQuery) -> list[SysConfigSchema]:
        """按分类/作用域查询，敏感值不回显。"""
        items = await self.repo.list_by_category(query.category, query.scope)
        schemas = to_schema_list(SysConfigSchema, items)
        for s in schemas:
            if is_sensitive(s.config_key) and s.config_key.startswith("STORAGE_"):
                # 不向浏览器回显存储密钥；is_set 供表单「已配置，留空不修改」
                has_value = bool(s.config_value)
                s.config_value = ""
                s.ext_json = {**(s.ext_json or {}), "is_set": has_value}
            else:
                s.config_value = decrypt_config_value(s.config_key, s.config_value) or ""
        return schemas

    async def batch_save(self, payload: ConfigBatchSaveRequest) -> None:
        """批量保存配置，敏感值传空表示保留原值。"""
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
        """后台分页查询，敏感值置空。"""
        items, total = await self.repo.page_admin(query)
        schemas = to_schema_list(SysConfigSchema, items)
        for s in schemas:
            if is_sensitive(s.config_key):
                s.config_value = ""
        return build_page(query, total, schemas)
