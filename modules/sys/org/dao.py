from typing import List, Dict, Any
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from .models import SysOrg
from .params import OrgPageParam
from core.db.base_dao import BaseDAO
from core.db.query_wrapper import QueryWrapper


class OrgDao(BaseDAO):
    def __init__(self, db: Session):
        super().__init__(db, SysOrg)

    def find_page_by_filters(self, param: OrgPageParam) -> Dict[str, Any]:
        wrapper = QueryWrapper(SysOrg)
        if param.parent_id:
            wrapper.where(or_(SysOrg.parent_id == param.parent_id, SysOrg.id == param.parent_id))
        if param.keyword:
            wrapper.like(SysOrg.name, param.keyword)
        wrapper.order_by_asc(SysOrg.sort_code)
        return self.select_page(wrapper, param)

    def find_all_ordered(self) -> List[SysOrg]:
        wrapper = QueryWrapper(SysOrg).order_by_asc(SysOrg.sort_code)
        return self.select_list(wrapper)
