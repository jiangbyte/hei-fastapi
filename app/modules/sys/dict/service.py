""" Author: Charlie """

from collections.abc import Mapping, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import to_schema, to_schema_list
from app.modules.sys.dict.repository import DictRepository, DictTreeRecord
from app.modules.sys.dict.schema import (
    DictAdminPageQuery,
    DictCreateRequest,
    DictIdQuery,
    DictIdsRequest,
    DictTreeQuery,
    DictUpdateRequest,
    SysDictSchema,
    SysDictTreeNode,
)
from app.modules.user.utils.profile import get_profiles_batch
from app.platform.db.transaction import transactional


class DictService:
    """字典业务服务，负责 CRUD、分页查询和树形响应转换。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DictRepository(db)

    async def create(self, payload: DictCreateRequest) -> None:
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: DictUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: DictIdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def get(self, query: DictIdQuery) -> SysDictSchema:
        schema = await self._to_schema_with_parent_name(await self.repo.get_required(query.id))
        await self._resolve_creator_names([schema])
        return schema

    async def page_admin(self, query: DictAdminPageQuery) -> PageData[SysDictSchema]:
        items, total = await self.repo.page_admin(query)
        records = await self._attach_parent_names(to_schema_list(SysDictSchema, items))
        await self._resolve_creator_names(records)
        return build_page(query, total, records)

    async def list_tree(self, query: DictTreeQuery) -> list[SysDictTreeNode]:
        return _build_tree_nodes(await self.repo.list_tree(query))

    async def _to_schema_with_parent_name(self, item: object) -> SysDictSchema:
        schemas = await self._attach_parent_names([to_schema(SysDictSchema, item)])
        return schemas[0]

    async def _attach_parent_names(self, items: list[SysDictSchema]) -> list[SysDictSchema]:
        parent_ids = {item.parent_id for item in items if item.parent_id}
        parent_name_map = await self.repo.get_parent_name_map(parent_ids)
        for item in items:
            item.parent_id_name = parent_name_map.get(item.parent_id or "")
        return items

    async def _resolve_creator_names(self, items: list[SysDictSchema]) -> None:
        """批量查询 created_by / updated_by 对应的昵称，写入 created_name / updated_name。"""
        account_ids: set[str] = set()
        for item in items:
            if item.created_by:
                account_ids.add(item.created_by)
            if item.updated_by:
                account_ids.add(item.updated_by)
        if not account_ids:
            return
        profiles = await get_profiles_batch(self.db, AccountType.ADMIN, list(account_ids))
        for item in items:
            if item.created_by and item.created_by in profiles:
                item.created_name = getattr(profiles[item.created_by], "nickname", None)
            if item.updated_by and item.updated_by in profiles:
                item.updated_name = getattr(profiles[item.updated_by], "nickname", None)


def _build_tree_nodes(
    items: Sequence[DictTreeRecord | SysDictTreeNode | Mapping[str, object]],
) -> list[SysDictTreeNode]:
    nodes: list[SysDictTreeNode] = []
    for item in items:
        raw_item: Mapping[str, object] = (
            item.model_dump() if isinstance(item, SysDictTreeNode) else item
        )
        nodes.append(
            SysDictTreeNode(
                id=str(raw_item["id"]),
                code=str(raw_item["code"]),
                label=raw_item.get("label"),  # type: ignore[arg-type]
                value=raw_item.get("value"),  # type: ignore[arg-type]
                color=raw_item.get("color"),  # type: ignore[arg-type]
                category=raw_item.get("category"),  # type: ignore[arg-type]
                parent_id=raw_item.get("parent_id"),  # type: ignore[arg-type]
                parent_id_name=raw_item.get("parent_id_name"),  # type: ignore[arg-type]
                status=str(raw_item["status"]),
                sort=int(raw_item["sort"]),
                children=_build_tree_nodes(raw_item.get("children", [])),  # type: ignore[arg-type]
            )
        )
    return nodes
