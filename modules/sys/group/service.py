from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Request

from . import SysGroup
from .params import GroupVO, GroupTreeVO, GroupPageParam, GroupTreeParam
from .dao import GroupDao
from ..org.params import OrgVO
from ..org.dao import OrgDao
from core.pojo import IdParam, IdsParam
from core.result import page_data, PageDataField
from core.exception import BusinessException
from core.utils import apply_update
from core.auth import HeiAuthTool
from core.utils.resolve_utils import resolve_name_path


class GroupService:
    def __init__(self, db: Session):
        self.dao = GroupDao(db)
        self._org_dao = OrgDao(db)

    async def _get_current_user_id(self, request: Optional[Request] = None) -> Optional[str]:
        try:
            return await HeiAuthTool.getLoginIdDefaultNull(request)
        except Exception:
            return None

    async def create(self, vo: GroupVO, request: Optional[Request] = None) -> None:
        entity = SysGroup(**vo.model_dump())
        self.dao.insert(entity, user_id=await self._get_current_user_id(request))

    def page(self, param: GroupPageParam) -> dict:
        if not param.parent_id and not param.org_id:
            return page_data(records=[], total=0, page=param.current, size=param.size)
        result = self.dao.find_page_by_filters(param)
        records = [GroupVO.model_validate(r).model_dump() for r in result[PageDataField.RECORDS]]
        self._batch_enrich(records)
        return page_data(
            records=records,
            total=result[PageDataField.TOTAL],
            page=param.current,
            size=param.size
        )

    def detail(self, param: IdParam) -> Optional[dict]:
        entity = self.dao.find_by_id(param.id)
        if not entity:
            return None
        vo = GroupVO.model_validate(entity).model_dump()
        self._enrich_vo(vo)
        return vo

    def _enrich_vo(self, vo: dict) -> None:
        from modules.sys.org.models import SysOrg
        vo["org_names"] = resolve_name_path(vo.get("org_id"), self.dao.db, SysOrg)

    def _batch_enrich(self, vo_list: List[dict]) -> None:
        from modules.sys.org.models import SysOrg
        for vo in vo_list:
            vo["org_names"] = resolve_name_path(vo.get("org_id"), self.dao.db, SysOrg)

    def tree(self, param: GroupTreeParam) -> List[dict]:
        if not param.org_id:
            return []
        records = self.dao.find_all_ordered()
        filtered = []
        for r in records:
            if r.org_id != param.org_id:
                continue
            if param.keyword and param.keyword.lower() not in (r.name or "").lower():
                continue
            filtered.append(r)

        node_map = {}
        roots = []
        for r in filtered:
            r_dict = GroupVO.model_validate(r).model_dump()
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
                GroupService._sort_tree(children)

    def union_tree(self) -> List[dict]:
        orgs = self._org_dao.find_all_ordered()
        groups = self.dao.find_all_ordered()

        org_nodes: dict[str, dict] = {}
        for o in orgs:
            node = OrgVO.model_validate(o).model_dump()
            node["_type"] = "org"
            node["children"] = []
            org_nodes[o.id] = node

        group_nodes: dict[str, dict] = {}
        for g in groups:
            node = GroupVO.model_validate(g).model_dump()
            node["_type"] = "group"
            node["children"] = []
            group_nodes[g.id] = node

        for gid, node in group_nodes.items():
            pid = node.get("parent_id")
            if pid and pid != "0" and pid in group_nodes:
                group_nodes[pid]["children"].append(node)

        orphan_groups: dict[str, list[dict]] = {}
        for gid, node in group_nodes.items():
            pid = node.get("parent_id")
            if not pid or pid not in group_nodes:
                oid = node.get("org_id") or ""
                orphan_groups.setdefault(oid, []).append(node)

        for oid, node in org_nodes.items():
            if oid in orphan_groups:
                node["children"] = orphan_groups[oid] + node["children"]

        roots: list[dict] = []
        for oid, node in org_nodes.items():
            pid = node.get("parent_id")
            if pid and pid != "0" and pid in org_nodes:
                org_nodes[pid]["children"].append(node)
            else:
                roots.append(node)

        self._sort_tree(roots)
        return roots

    async def modify(self, vo: GroupVO, request: Optional[Request] = None) -> None:
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
        from sqlalchemy import func, select, update as sa_update
        from ..user.models import SysUser
        from ..position.models import SysPosition

        all_ids = self._collect_descendant_ids(param.ids)
        db = self.dao.db

        if db.execute(
            select(func.count()).select_from(SysUser).where(SysUser.group_id.in_(all_ids))
        ).scalar() > 0:
            raise BusinessException("用户组存在关联用户，无法删除")

        db.execute(
            sa_update(SysUser).where(SysUser.group_id.in_(all_ids)).values(group_id=None)
        )
        db.execute(
            sa_update(SysPosition).where(
                SysPosition.group_id.in_(all_ids)
            ).values(group_id=None)
        )

        self.dao.delete_by_ids(all_ids)
