""" Author: Charlie """

from typing import TypedDict

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.sys.dict.model import SysDict
from app.modules.sys.dict.schema import (
    DictAdminPageQuery,
    DictCreateRequest,
    DictTreeQuery,
    DictUpdateRequest,
)


class DictTreeRecord(TypedDict):
    id: str
    code: str
    label: str | None
    value: str | None
    color: str | None
    category: str | None
    parent_id: str | None
    parent_id_name: str | None
    status: str
    sort: int
    children: list["DictTreeRecord"]


class DictRepository:
    """字典仓储，负责直接持久化、分页查询和树形组装。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: DictCreateRequest) -> None:
        entity = SysDict(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()

    async def get_by_id(self, dict_id: str) -> SysDict | None:
        return await self.db.get(SysDict, dict_id)

    async def get_required(self, dict_id: str) -> SysDict:
        entity = await self.get_by_id(dict_id)
        if entity is None:
            raise NotFoundError("Dict not found")
        return entity

    async def update(self, payload: DictUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        data = payload.model_dump(exclude={"id"})
        for key, value in data.items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, dict_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(dict_ids))
        stmt = select(SysDict.id).where(SysDict.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("Dict not found")
        await self.db.execute(delete(SysDict).where(SysDict.id.in_(unique_ids)))

    async def page_admin(self, query: DictAdminPageQuery) -> tuple[list[SysDict], int]:
        stmt: Select[tuple[SysDict]] = select(SysDict)
        count_stmt = select(func.count(SysDict.id))
        filters = []
        if query.code:
            filters.append(SysDict.code == query.code)
        if query.category:
            filters.append(SysDict.category == query.category)
        if query.parent_id:
            filters.append(or_(SysDict.id == query.parent_id, SysDict.parent_id == query.parent_id))
        if query.status:
            filters.append(SysDict.status == str(query.status))
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(SysDict.sort.asc(), SysDict.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total

    async def get_parent_name_map(self, parent_ids: set[str]) -> dict[str, str]:
        if not parent_ids:
            return {}
        stmt = select(SysDict.id, SysDict.code, SysDict.label).where(SysDict.id.in_(parent_ids))
        rows = (await self.db.execute(stmt)).all()
        return {id_: label or code for id_, code, label in rows}

    async def list_tree(self, query: DictTreeQuery) -> list[DictTreeRecord]:
        stmt = select(SysDict)
        if query.category:
            stmt = stmt.where(SysDict.category == query.category)
        stmt = stmt.order_by(SysDict.sort.asc(), SysDict.id.desc())
        items = list((await self.db.execute(stmt)).scalars().all())
        return _build_tree(items)


def _build_tree(items: list[SysDict]) -> list[DictTreeRecord]:
    node_map: dict[str, DictTreeRecord] = {
        item.id: {
            "id": item.id,
            "code": item.code,
            "label": item.label,
            "value": item.value,
            "color": item.color,
            "category": item.category,
            "parent_id": item.parent_id,
            "parent_id_name": None,
            "status": item.status,
            "sort": item.sort,
            "children": [],
        }
        for item in items
    }
    roots: list[DictTreeRecord] = []
    for item in items:
        if item.parent_id and item.parent_id in node_map:
            parent = node_map[item.parent_id]
            node_map[item.id]["parent_id_name"] = parent["label"] or parent["code"]
            node_map[item.parent_id]["children"].append(node_map[item.id])
        else:
            roots.append(node_map[item.id])
    return roots
