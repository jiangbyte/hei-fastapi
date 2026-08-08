"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-08-08 21:09:55
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import (
    IdQuery,
    IdsRequest,
    KeywordQuery,
    to_schema,
    to_schema_list,
)
from app.core.security.data_scope import build_data_scope_filter, default_owner_dept_id
from app.core.security.session import SessionPayload
from app.modules.user.utils.profile import enrich_audit_names
from app.platform.db.transaction import transactional
from app.modules.biz.cg_test_knowledge_category.model import CgTestKnowledgeCategory
from app.modules.biz.cg_test_knowledge_category.repository import (
    CgTestKnowledgeCategoryRepository,
    CgTestKnowledgeDocRepository,
)
from app.modules.biz.cg_test_knowledge_category.schema import (
    CgTestKnowledgeCategoryAdminPageQuery,
    CgTestKnowledgeCategoryCreateRequest,
    CgTestKnowledgeCategorySchema,
    CgTestKnowledgeCategoryTreeNode,
    CgTestKnowledgeCategoryUpdateRequest,
    CgTestKnowledgeDocAdminPageQuery,
    CgTestKnowledgeDocCreateRequest,
    CgTestKnowledgeDocSchema,
    CgTestKnowledgeDocUpdateRequest,
)


class CgTestKnowledgeCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CgTestKnowledgeCategoryRepository(db)

    async def create(
        self,
        payload: CgTestKnowledgeCategoryCreateRequest,
        session: SessionPayload | None = None,
    ) -> None:
        async with transactional(self.db):
            await self.repo.create(payload, owner_dept_id=default_owner_dept_id(session))

    async def update(self, payload: CgTestKnowledgeCategoryUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> CgTestKnowledgeCategorySchema:
        schema = await self._to_schema_with_parent_name(await self.repo.get_required(query.id))
        await enrich_audit_names(self.db, [schema], account_type=AccountType.ADMIN)
        return schema

    async def page_admin(
        self,
        query: CgTestKnowledgeCategoryAdminPageQuery,
        session: SessionPayload | None = None,
    ) -> PageData[CgTestKnowledgeCategorySchema]:
        data_scope_filter = None
        if session is not None:
            data_scope_filter = await build_data_scope_filter(
                self.db,
                session,
                "biz:cgtestknowledgecategory:page",
                owner_column=CgTestKnowledgeCategory.created_by,
                dept_column=getattr(CgTestKnowledgeCategory, "owner_dept_id", None),
            )
        items, total = await self.repo.page_admin(query, data_scope_filter)
        records = await self._attach_parent_names(to_schema_list(CgTestKnowledgeCategorySchema, items))
        await enrich_audit_names(self.db, records, account_type=AccountType.ADMIN)
        return build_page(query, total, records)

    async def _to_schema_with_parent_name(self, item: object) -> CgTestKnowledgeCategorySchema:
        schemas = await self._attach_parent_names([to_schema(CgTestKnowledgeCategorySchema, item)])
        return schemas[0]

    async def _attach_parent_names(self, items: list[CgTestKnowledgeCategorySchema]) -> list[CgTestKnowledgeCategorySchema]:
        parent_ids = {item.parent_id for item in items if item.parent_id}
        parent_name_map = await self.repo.get_parent_name_map(parent_ids)
        for item in items:
            item.parent_id_name = parent_name_map.get(item.parent_id or "")
        return items

    async def tree(
        self,
        query: KeywordQuery,
        session: SessionPayload | None = None,
    ) -> list[CgTestKnowledgeCategoryTreeNode]:
        data_scope_filter = None
        if session is not None:
            data_scope_filter = await build_data_scope_filter(
                self.db,
                session,
                "biz:cgtestknowledgecategory:list",
                owner_column=CgTestKnowledgeCategory.created_by,
                dept_column=getattr(CgTestKnowledgeCategory, "owner_dept_id", None),
            )
        items = await self.repo.list_tree(query.keyword, data_scope_filter)
        return _build_cg_test_knowledge_category_tree(items)


def _build_cg_test_knowledge_category_tree(items) -> list[CgTestKnowledgeCategoryTreeNode]:
    node_map = {item.id: to_schema(CgTestKnowledgeCategoryTreeNode, item) for item in items}
    roots: list[CgTestKnowledgeCategoryTreeNode] = []
    for item in items:
        node = node_map[item.id]
        parent_id = getattr(item, "parent_id", None)
        if parent_id and parent_id in node_map:
            node.parent_id_name = getattr(node_map[parent_id], "name", None)
            node_map[parent_id].children.append(node)
        else:
            roots.append(node)
    return roots


class CgTestKnowledgeDocService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CgTestKnowledgeDocRepository(db)

    async def create(self, payload: CgTestKnowledgeDocCreateRequest) -> None:
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: CgTestKnowledgeDocUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> CgTestKnowledgeDocSchema:
        schema = to_schema(CgTestKnowledgeDocSchema, await self.repo.get_required(query.id))
        await enrich_audit_names(self.db, [schema], account_type=AccountType.ADMIN)
        return schema

    async def page_admin(self, query: CgTestKnowledgeDocAdminPageQuery) -> PageData[CgTestKnowledgeDocSchema]:
        items, total = await self.repo.page_admin(query)
        records = to_schema_list(CgTestKnowledgeDocSchema, items)
        await enrich_audit_names(self.db, records, account_type=AccountType.ADMIN)
        return build_page(query, total, records)
