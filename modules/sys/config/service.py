from typing import Optional, List
from fastapi import Request
from sqlalchemy.orm import Session
from core.result import page_data, PageDataField
from core.exception import BusinessException
from core.utils.model_utils import strip_system_fields, apply_update
from core.auth import HeiAuthTool
from core.db.base_service import BaseCrudService
from core.db.redis import get_client
from .models import SysConfig
from .dao import ConfigDao
from .params import ConfigVO, ConfigPageParam, ConfigListParam, ConfigCategoryEditParam


CONFIG_CACHE_PREFIX = "sys-config:"


class ConfigService(BaseCrudService):
    model_class = SysConfig
    vo_class = ConfigVO
    dao_class = ConfigDao
    page_param_class = ConfigPageParam
    export_name = "配置数据"

    async def _get_current_user_id(self, request: Request) -> Optional[str]:
        try:
            return await HeiAuthTool.getLoginIdDefaultNull(request)
        except Exception:
            return None

    async def _get_cached_value(self, key: str) -> Optional[str]:
        client = get_client()
        if client:
            val = await client.get(f"{CONFIG_CACHE_PREFIX}{key}")
            if val is not None:
                return val
        return None

    async def _set_cached_value(self, key: str, value: str):
        client = get_client()
        if client:
            await client.set(f"{CONFIG_CACHE_PREFIX}{key}", value)

    async def _del_cached_value(self, key: str):
        client = get_client()
        if client:
            await client.delete(f"{CONFIG_CACHE_PREFIX}{key}")

    async def get_value_by_key(self, key: str) -> Optional[str]:
        cached = await self._get_cached_value(key)
        if cached is not None:
            return cached

        entity = self.dao.find_by_key(key)
        if entity:
            await self._set_cached_value(key, entity.config_value)
            return entity.config_value
        return None

    async def get_values_by_keys(self, keys: list[str]) -> dict[str, Optional[str]]:
        result = {}
        uncached = []
        for key in keys:
            cached = await self._get_cached_value(key)
            if cached is not None:
                result[key] = cached
            else:
                uncached.append(key)

        if uncached:
            entities = self.dao.find_by_keys(uncached)
            for key in uncached:
                entity = entities.get(key)
                if entity:
                    result[key] = entity.config_value
                    await self._set_cached_value(key, entity.config_value)
                else:
                    result[key] = None
        return result

    def page(self, param: ConfigPageParam) -> dict:
        result = self.dao.find_page_by_filters(param)
        records = result[PageDataField.RECORDS]
        total = result[PageDataField.TOTAL]
        vo_list = [ConfigVO.model_validate(r).model_dump() for r in records]
        self._batch_enrich(vo_list)
        return page_data(records=vo_list, total=total, page=param.current, size=param.size)

    def list_by_category(self, param: ConfigListParam) -> List[dict]:
        entities = self.dao.find_by_category(param.category)
        return [ConfigVO.model_validate(e).model_dump() for e in entities]

    async def modify(self, vo: ConfigVO, request: Request):
        entity = self.dao.find_by_id(vo.id)
        if not entity:
            raise BusinessException("数据不存在")
        update_data = strip_system_fields(vo.model_dump(exclude_unset=True))
        apply_update(entity, update_data)
        self.dao.update(entity, user_id=await self._get_current_user_id(request))
        await self._del_cached_value(entity.config_key)

    async def remove(self, param):
        entities = self.dao.find_by_ids(param.ids)
        keys = [entity.config_key for entity in entities]
        if keys:
            client = get_client()
            if client:
                await client.delete(*[f"{CONFIG_CACHE_PREFIX}{k}" for k in keys])
        self.dao.delete_by_ids(param.ids)

    async def edit_batch(self, param, request: Request):
        user_id = await self._get_current_user_id(request)
        ids = [vo.id for vo in param.configs]
        entity_map = {e.id: e for e in self.dao.find_by_ids(ids)}
        keys_to_clear = []
        for vo in param.configs:
            entity = entity_map.get(vo.id)
            if not entity:
                raise BusinessException(f"配置不存在: {vo.id}")
            update_data = strip_system_fields(vo.model_dump(exclude_unset=True))
            apply_update(entity, update_data)
            self.dao.meta_object_handler.update_fill(self.dao, entity, updated_by=user_id)
            keys_to_clear.append(entity.config_key)
        self.dao.db.commit()
        if keys_to_clear:
            client = get_client()
            if client:
                await client.delete(*[f"{CONFIG_CACHE_PREFIX}{k}" for k in keys_to_clear])

    async def edit_by_category(self, param: ConfigCategoryEditParam, request: Request):
        user_id = await self._get_current_user_id(request)
        keys = [vo.config_key for vo in param.configs]
        entity_map = self.dao.find_by_category_and_keys(param.category, keys)
        keys_to_clear = []
        for vo in param.configs:
            entity = entity_map.get(vo.config_key)
            if not entity:
                raise BusinessException(f"分类 [{param.category}] 下不存在配置: {vo.config_key}")
            entity.config_value = vo.config_value
            self.dao.meta_object_handler.update_fill(self.dao, entity, updated_by=user_id)
            keys_to_clear.append(entity.config_key)
        self.dao.db.commit()
        if keys_to_clear:
            client = get_client()
            if client:
                await client.delete(*[f"{CONFIG_CACHE_PREFIX}{k}" for k in keys_to_clear])
