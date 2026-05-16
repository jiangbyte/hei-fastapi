from typing import Optional, List
from fastapi import Request
from sqlalchemy.orm import Session
from .params import OrgVO, OrgPageParam, OrgTreeParam
from .dao import OrgDao
from .models import SysOrg
from core.pojo import IdParam, IdsParam
from core.result import page_data, PageDataField
from core.exception import BusinessException
from core.utils import apply_update
from core.auth import HeiAuthTool


class OrgService:
    def __init__(self, db: Session):
        self.dao = OrgDao(db)

    async def _get_current_user_id(self, request: Optional[Request] = None) -> Optional[str]:
        try:
            return await HeiAuthTool.getLoginIdDefaultNull(request)
        except Exception:
            return None

    def detail(self, param: IdParam):
        entity = self.dao.find_by_id(param.id)
        if not entity:
            return None
        return OrgVO.model_validate(entity).model_dump()

    async def create(self, vo: OrgVO, request: Optional[Request] = None) -> None:
        entity = SysOrg(**vo.model_dump())
        self.dao.insert(entity, user_id=await self._get_current_user_id(request))

    def page(self, param: OrgPageParam) -> dict:
        result = self.dao.find_page_by_filters(param)
        records = [OrgVO.model_validate(r).model_dump() for r in result[PageDataField.RECORDS]]
        return page_data(
            records=records,
            total=result[PageDataField.TOTAL],
            page=param.current,
            size=param.size
        )

    def tree(self, param: OrgTreeParam) -> List[dict]:
        records = self.dao.find_all_ordered()
        if param.category:
            records = [r for r in records if r.category == param.category]

        node_map = {}
        roots = []
        for r in records:
            r_dict = OrgVO.model_validate(r).model_dump()
            r_dict["children"] = []
            node_map[r.id] = r_dict

        for r_dict in node_map.values():
            pid = r_dict.get("parent_id")
            if pid and pid != "0" and pid in node_map:
                node_map[pid]["children"].append(r_dict)
            else:
                roots.append(r_dict)

        self._sort_tree(roots)
        return roots

    @staticmethod
    def _sort_tree(nodes: List[dict]):
        nodes.sort(key=lambda x: x.get("sort_code", 0) or 0)
        for n in nodes:
            children = n.get("children")
            if children:
                OrgService._sort_tree(children)

    async def modify(self, vo: OrgVO, request: Optional[Request] = None) -> None:
        entity = self.dao.find_by_id(vo.id)
        if not entity:
            raise BusinessException("数据不存在")
        if vo.parent_id is not None and vo.parent_id != entity.parent_id:
            self._check_circular_parent(vo.id, vo.parent_id)
        update_data = vo.model_dump(exclude_unset=True)
        apply_update(entity, update_data)
        self.dao.update(entity, user_id=await self._get_current_user_id(request))

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

    def remove(self, param: IdsParam) -> None:
        from sqlalchemy import func, select, delete as sa_delete, update as sa_update
        from ..user.models import SysUser
        from ..group.models import SysGroup
        from ..position.models import SysPosition

        all_ids = self._collect_descendant_ids(param.ids)
        db = self.dao.db

        if db.execute(
            select(func.count()).select_from(SysUser).where(
                SysUser.org_id.in_(all_ids)
            )
        ).scalar() > 0:
            raise BusinessException("组织存在关联用户，无法删除")

        if db.execute(
            select(func.count()).select_from(SysGroup).where(
                SysGroup.org_id.in_(all_ids)
            )
        ).scalar() > 0:
            raise BusinessException("组织下存在用户组，无法删除")

        db.execute(
            sa_update(SysPosition).where(
                SysPosition.org_id.in_(all_ids)
            ).values(org_id=None)
        )

        self.dao.delete_by_ids(all_ids)
