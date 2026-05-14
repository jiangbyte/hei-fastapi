from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Request
from .params import DictVO, DictPageParam, DictListParam, DictTreeParam, DictExportParam, DictImportParam
from .dao import DictDao
from .models import SysDict
from core.pojo import IdParam, IdsParam
from core.result import page_data, PageDataField
from core.exception import BusinessException
from core.enums import ExportTypeEnum
from core.utils import export_excel, generate_id, strip_system_fields, apply_update, make_template
from core.auth import HeiAuthTool
from core.db.base_service import BaseCrudService
from core.db.redis import get_client
from core.constants import DICT_CACHE_KEY, DICT_TREE_CACHE_KEY
import json
import logging

logger = logging.getLogger(__name__)


class DictService(BaseCrudService):
    model_class = SysDict
    vo_class = DictVO
    dao_class = DictDao
    page_param_class = DictPageParam
    export_name = "字典数据"

    def page(self, param: DictPageParam) -> dict:
        result = self.dao.find_page_by_filters(param)
        records = [DictVO.model_validate(r).model_dump() for r in result[PageDataField.RECORDS]]
        self._batch_enrich(records)
        return page_data(
            records=records,
            total=result[PageDataField.TOTAL],
            page=param.current,
            size=param.size
        )

    def list(self, param: DictListParam) -> List[dict]:
        records = self.dao.find_list_by_filters(param)
        return [DictVO.model_validate(r).model_dump() for r in records]

    async def tree(self, param: DictTreeParam) -> List[dict]:
        cached = await self._get_cached_tree()
        if cached is not None:
            return cached

        records = self.dao.find_all_ordered()
        if param.category:
            records = [r for r in records if r.category == param.category]

        node_map = {}
        roots = []
        for r in records:
            r_dict = DictVO.model_validate(r).model_dump()
            r_dict["children"] = []
            node_map[r.id] = r_dict

        for r_dict in node_map.values():
            pid = r_dict.get("parent_id")
            if pid and pid in node_map:
                node_map[pid]["children"].append(r_dict)
            else:
                roots.append(r_dict)

        self._sort_tree(roots)
        return roots

    @staticmethod
    async def _get_cached_tree() -> Optional[List[dict]]:
        try:
            client = get_client()
            if not client:
                return None
            data = await client.get(DICT_TREE_CACHE_KEY)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Failed to read dict tree cache: {e}")
        return None

    @staticmethod
    def _sort_tree(nodes: List[dict]):
        nodes.sort(key=lambda x: x.get("sort_code", 0) or 0)
        for n in nodes:
            children = n.get("children")
            if children:
                DictService._sort_tree(children)

    async def create(self, vo: DictVO, request: Optional[Request] = None) -> None:
        parent_id = vo.parent_id or "0"
        self._check_duplicate(parent_id, vo.label, vo.value, None)

        entity_data = strip_system_fields(vo.model_dump(), extra_fields={'parent_id'})
        if not entity_data.get("code"):
            entity_data["code"] = str(generate_id())
        entity = SysDict(**entity_data, parent_id=parent_id)
        self.dao.insert(entity, user_id=await self._get_current_user_id(request))
        await self._sync_cache()

    def _check_duplicate(self, parent_id: str, label: Optional[str], value: Optional[str], exclude_id: Optional[str]):
        if label:
            if self.dao.count_by_parent_and_label(parent_id, label, exclude_id) > 0:
                raise BusinessException(f"同一父字典下已存在相同标签: {label}")
        if value:
            if self.dao.count_by_parent_and_value(parent_id, value, exclude_id) > 0:
                raise BusinessException(f"同一父字典下已存在相同值: {value}")

    async def modify(self, vo: DictVO, request: Optional[Request] = None) -> None:
        entity = self.dao.find_by_id(vo.id)
        if not entity:
            raise BusinessException("数据不存在")

        parent_id = vo.parent_id or "0"
        self._check_duplicate(parent_id, vo.label, vo.value, vo.id)
        if str(parent_id) != str(entity.parent_id):
            self._check_circular_parent(vo.id, parent_id if parent_id != "0" else None)

        update_data = vo.model_dump(exclude_unset=True)
        apply_update(entity, update_data)
        entity.parent_id = parent_id
        self.dao.update(entity, user_id=await self._get_current_user_id(request))
        await self._sync_cache()

    def _check_circular_parent(self, entity_id: str, new_parent_id: Optional[str]) -> None:
        if not new_parent_id:
            return
        all_records = self.dao.find_all()
        parent_map = {r.id: r.parent_id for r in all_records}
        current = new_parent_id
        while current:
            if current == entity_id:
                raise BusinessException("父级不能选择自身或子节点")
            current = parent_map.get(current)
            if not current or current == "0":
                break

    def _collect_descendant_ids(self, ids: List[str]) -> List[str]:
        all_records = self.dao.find_all()
        children_map: dict[str, list[str]] = {}
        for r in all_records:
            children_map.setdefault(r.parent_id or "0", []).append(r.id)

        all_ids = set(ids)
        stack = list(ids)
        while stack:
            parent_id = stack.pop()
            for child_id in children_map.get(parent_id, []):
                if child_id not in all_ids:
                    all_ids.add(child_id)
                    stack.append(child_id)
        return list(all_ids)

    async def remove(self, param: IdsParam) -> None:
        all_ids = self._collect_descendant_ids(param.ids)
        self.dao.delete_by_ids(all_ids)
        await self._sync_cache()

    async def import_data(self, param: DictImportParam, request: Optional[Request] = None) -> dict:
        if not param.data:
            raise BusinessException("导入数据不能为空")
        entities = [SysDict(**strip_system_fields(vo.model_dump())) for vo in param.data]
        self.dao.insert_batch(entities, user_id=await self._get_current_user_id(request))
        await self._sync_cache()
        return {"total": len(entities), "message": f"成功导入{len(entities)}条数据"}

    # ---- Dict translation helpers ----

    def get_dict_label(self, type_code: str, value: str) -> Optional[str]:
        root = self.dao.find_by_code(type_code)
        if not root:
            return None
        children = self.dao.find_by_parent_id(root.id)
        for child in children:
            if child.value == value:
                return child.label
        return None

    def get_dict_children(self, type_code: str) -> List[dict]:
        root = self.dao.find_by_code(type_code)
        if not root:
            return []
        children = self.dao.find_by_parent_id(root.id)
        return [DictVO.model_validate(c).model_dump() for c in children]

    # ---- Redis cache ----

    async def _sync_cache(self):
        redis_client = get_client()
        if not redis_client:
            return
        try:
            records = self.dao.find_all_ordered()

            # Flat cache: typeCode -> children (for get_cached_dicts)
            flat_cache = {}
            full_tree = self._build_full_tree(records)

            children_by_parent: dict[str, list] = {}
            for r in records:
                children_by_parent.setdefault(r.parent_id or "0", []).append(r)

            for r in records:
                code = r.code
                if code and r.parent_id in ("0", None):
                    children = children_by_parent.get(r.id, [])
                    if children:
                        flat_cache[code] = [
                            {"label": c.label, "value": c.value, "color": c.color}
                            for c in children
                        ]

            await redis_client.set(DICT_CACHE_KEY, json.dumps(flat_cache, ensure_ascii=False))
            await redis_client.set(DICT_TREE_CACHE_KEY, json.dumps(full_tree, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to sync dict cache: {e}")

    @staticmethod
    def _build_full_tree(records: list) -> list:
        node_map = {}
        roots = []
        for r in records:
            r_dict = DictVO.model_validate(r).model_dump()
            r_dict["children"] = []
            node_map[r.id] = r_dict

        for r_dict in node_map.values():
            pid = r_dict.get("parent_id")
            if pid and pid in node_map:
                node_map[pid]["children"].append(r_dict)
            else:
                roots.append(r_dict)

        DictService._sort_tree(roots)
        return roots

    @staticmethod
    async def get_cached_dicts() -> dict:
        redis_client = get_client()
        if not redis_client:
            return {}
        data = await redis_client.get(DICT_CACHE_KEY)
        if data:
            return json.loads(data)
        return {}
