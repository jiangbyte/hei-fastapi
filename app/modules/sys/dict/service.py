""" Author: Charlie

系统字典服务层：字典 CRUD、分页、树形转换与昵称填充。
"""

from collections.abc import Mapping, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.db.transaction import transactional
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
from app.modules.profile.utils.profile import enrich_audit_names


class DictService:
    """字典业务服务，负责 CRUD、分页查询和树形响应转换。"""

    def __init__(self, db: AsyncSession):
        """绑定会话并初始化仓储。"""
        self.db = db
        self.repo = DictRepository(db)

    async def create(self, payload: DictCreateRequest) -> None:
        """事务内新增字典。"""
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: DictUpdateRequest) -> None:
        """事务内更新字典。"""
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: DictIdsRequest) -> None:
        """事务内批量删除字典。"""
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def get(self, query: DictIdQuery) -> SysDictSchema:
        """查询字典详情并填充父级名称与昵称。"""
        schema = await self._to_schema_with_parent_name(await self.repo.get_required(query.id))
        await enrich_audit_names(self.db, [schema], account_type=AccountType.ADMIN)
        return schema

    async def page_admin(self, query: DictAdminPageQuery) -> PageData[SysDictSchema]:
        """分页查询字典并填充父级名称与昵称。"""
        items, total = await self.repo.page_admin(query)
        records = await self._attach_parent_names(to_schema_list(SysDictSchema, items))
        await enrich_audit_names(self.db, records, account_type=AccountType.ADMIN)
        return build_page(query, total, records)

    async def list_tree(self, query: DictTreeQuery) -> list[SysDictTreeNode]:
        """查询字典树。"""
        return _build_tree_nodes(await self.repo.list_tree(query))

    async def _to_schema_with_parent_name(self, item: object) -> SysDictSchema:
        """将实体转为 schema 并填充父级名称。"""
        schemas = await self._attach_parent_names([to_schema(SysDictSchema, item)])
        return schemas[0]

    async def _attach_parent_names(self, items: list[SysDictSchema]) -> list[SysDictSchema]:
        """批量填充字典的父级名称。"""
        parent_ids = {item.parent_id for item in items if item.parent_id}
        parent_name_map = await self.repo.get_parent_name_map(parent_ids)
        for item in items:
            item.parent_id_name = parent_name_map.get(item.parent_id or "")
        return items


def _build_tree_nodes(
    items: Sequence[DictTreeRecord | SysDictTreeNode | Mapping[str, object]],
) -> list[SysDictTreeNode]:
    """递归将字典树记录转换为树节点响应。"""
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
