""" Author: Charlie

实现 DataScopeResolverProtocol — 部门树的部门及子部门 ID 查询。
"""
from collections import defaultdict
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.dept.model import SysDept


class DeptDataScopeResolver:
    async def list_dept_and_child_ids(self, db: AsyncSession, dept_ids: Iterable[str]) -> list[str]:
        root_ids = sorted({str(dept_id) for dept_id in dept_ids if dept_id})
        if not root_ids:
            return []

        rows = (await db.execute(select(SysDept.id, SysDept.parent_id))).all()
        children_by_parent: dict[str, list[str]] = defaultdict(list)
        for dept_id, parent_id in rows:
            if parent_id:
                children_by_parent[str(parent_id)].append(str(dept_id))

        result: set[str] = set()
        stack = list(root_ids)
        while stack:
            dept_id = stack.pop()
            if dept_id in result:
                continue
            result.add(dept_id)
            stack.extend(children_by_parent.get(dept_id, []))
        return sorted(result)


resolver = DeptDataScopeResolver()
