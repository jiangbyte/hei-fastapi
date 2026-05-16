from typing import Optional, List
from fastapi import Request
from sqlalchemy import select, delete as sa_delete, update as sa_update
from sqlalchemy.orm import Session
from .models import SysModule, SysResource
from .params import ModuleVO, ResourceVO, ModulePageParam, ResourcePageParam
from .dao import ModuleDao, ResourceDao
from core.pojo import IdParam, IdsParam
from core.result import page_data, PageDataField
from core.exception import BusinessException
from core.utils import strip_system_fields, apply_update, generate_id
from core.auth import HeiAuthTool
import logging

logger = logging.getLogger(__name__)


class ModuleService:
    def __init__(self, db: Session):
        self.dao = ModuleDao(db)

    async def _get_current_user_id(self, request: Optional[Request] = None) -> Optional[str]:
        try:
            return await HeiAuthTool.getLoginIdDefaultNull(request)
        except Exception as e:
            logger.warning(f"Failed to get current user: {e}")
            return None

    def page(self, param: ModulePageParam) -> dict:
        result = self.dao.find_page(param)
        records = [ModuleVO.model_validate(r).model_dump() for r in result[PageDataField.RECORDS]]
        return page_data(
            records=records,
            total=result[PageDataField.TOTAL],
            page=param.current,
            size=param.size,
        )

    def detail(self, param: IdParam):
        entity = self.dao.find_by_id(param.id)
        if not entity:
            return None
        return ModuleVO.model_validate(entity).model_dump()

    async def create(self, vo: ModuleVO, request: Optional[Request] = None) -> None:
        entity = SysModule(**strip_system_fields(vo.model_dump()))
        self.dao.insert(entity, user_id=await self._get_current_user_id(request))

    async def modify(self, vo: ModuleVO, request: Optional[Request] = None) -> None:
        entity = self.dao.find_by_id(vo.id)
        if not entity:
            raise BusinessException("数据不存在")
        apply_update(entity, vo.model_dump(exclude_unset=True))
        self.dao.update(entity, user_id=await self._get_current_user_id(request))

    def remove(self, param: IdsParam) -> None:
        self.dao.delete_by_ids(param.ids)


class ResourceService:
    def __init__(self, db: Session):
        self.dao = ResourceDao(db)

    async def _get_current_user_id(self, request: Optional[Request] = None) -> Optional[str]:
        try:
            return await HeiAuthTool.getLoginIdDefaultNull(request)
        except Exception as e:
            logger.warning(f"Failed to get current user: {e}")
            return None

    def page(self, param: ResourcePageParam) -> dict:
        result = self.dao.find_page(param)
        records = [ResourceVO.model_validate(r).model_dump() for r in result[PageDataField.RECORDS]]
        return page_data(
            records=records,
            total=result[PageDataField.TOTAL],
            page=param.current,
            size=param.size,
        )

    def detail(self, param: IdParam):
        entity = self.dao.find_by_id(param.id)
        if not entity:
            return None
        return ResourceVO.model_validate(entity).model_dump()

    async def create(self, vo: ResourceVO, request: Optional[Request] = None) -> None:
        entity = SysResource(**strip_system_fields(vo.model_dump()))
        self.dao.insert(entity, user_id=await self._get_current_user_id(request))

    async def modify(self, vo: ResourceVO, request: Optional[Request] = None) -> None:
        entity = self.dao.find_by_id(vo.id)
        if not entity:
            raise BusinessException("数据不存在")

        if vo.parent_id is not None and vo.parent_id != entity.parent_id:
            self._check_circular_parent(vo.id, vo.parent_id)

        old_extra = entity.extra
        update_data = {k: getattr(vo, k) for k in vo.model_fields_set if k != 'id'}
        apply_update(entity, update_data)
        self.dao.update(entity, user_id=await self._get_current_user_id(request))

        # If extra.permission_code changed, sync role-permission assignments
        if old_extra != entity.extra:
            import json
            from ..role.models import RelRoleResource, RelRolePermission

            old_code = None
            new_code = None
            try:
                if old_extra:
                    old_code = json.loads(old_extra).get("permission_code")
                if entity.extra:
                    new_code = json.loads(entity.extra).get("permission_code")
            except (json.JSONDecodeError, TypeError):
                pass

            if old_code != new_code:
                role_ids = list(
                    self.dao.db.execute(
                        select(RelRoleResource.role_id).where(RelRoleResource.resource_id == entity.id)
                    ).scalars().all()
                )
                if role_ids:
                    if old_code:
                        self.dao.db.execute(
                            sa_delete(RelRolePermission).where(
                                RelRolePermission.role_id.in_(role_ids),
                                RelRolePermission.permission_code == old_code
                            )
                        )
                    if new_code:
                        existing_role_ids = set(
                            self.dao.db.execute(
                                select(RelRolePermission.role_id).where(
                                    RelRolePermission.role_id.in_(role_ids),
                                    RelRolePermission.permission_code == new_code
                                )
                            ).scalars().all()
                        )
                        for role_id in role_ids:
                            if role_id not in existing_role_ids:
                                rel = RelRolePermission(
                                    id=generate_id(), role_id=role_id,
                                    permission_code=new_code, scope="ALL",
                                )
                                self.dao.db.add(rel)
                    self.dao.db.commit()

    def remove(self, param: IdsParam) -> None:
        from ..role.models import RelRoleResource

        all_ids = self._collect_descendant_ids(param.ids)
        db = self.dao.db

        db.execute(sa_delete(RelRoleResource).where(RelRoleResource.resource_id.in_(all_ids)))

        self.dao.delete_by_ids(all_ids)

    def tree(self) -> list:
        records = self.dao.find_all()
        records.sort(key=lambda r: r.sort_code or 0)
        nodes = [ResourceVO.model_validate(r).model_dump() for r in records]
        children_map: dict[str, list] = {}
        for n in nodes:
            pid = n.get("parent_id") or ""
            pid = "" if pid == "0" else pid
            children_map.setdefault(pid, []).append(n)

        def build(pid: str) -> list:
            result = []
            for n in children_map.get(pid, []):
                n["children"] = build(n["id"])
                result.append(n)
            return result

        return build("")

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
