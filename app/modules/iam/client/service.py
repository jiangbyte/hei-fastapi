""" Author: Charlie """

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.session import SessionPayload
from app.modules.iam.client.model import SysClientResource
from app.modules.iam.client.repository import ClientModuleRepository, ClientResourceRepository
from app.modules.iam.client.schema import (
    ClientModuleAdminPageQuery,
    ClientModuleCreateRequest,
    ClientModuleSelectorOption,
    ClientModuleSelectorQuery,
    ClientModuleUpdateRequest,
    ClientResourceAdminPageQuery,
    ClientResourceCreateRequest,
    ClientResourcePermissionBindRequest,
    ClientResourceTreeNode,
    ClientResourceTreeQuery,
    ClientResourceUpdateRequest,
    SysClientModuleSchema,
    SysClientResourcePermissionRelSchema,
    SysClientResourceSchema,
)
from app.modules.iam.permission.service import ensure_registered_permission
from app.modules.iam.schema import ResourceGrantModuleOption
from app.modules.user.utils.profile import get_profiles_batch
from app.platform.db.transaction import transactional


async def _resolve_creator_names(db: AsyncSession, items: list) -> None:
    account_ids: set[str] = set()
    for item in items:
        if item.created_by:
            account_ids.add(item.created_by)
        if item.updated_by:
            account_ids.add(item.updated_by)
    if not account_ids:
        return
    profiles = await get_profiles_batch(db, AccountType.ADMIN, list(account_ids))
    for item in items:
        if item.created_by and item.created_by in profiles:
            item.created_name = getattr(profiles[item.created_by], "nickname", None)
        if item.updated_by and item.updated_by in profiles:
            item.updated_name = getattr(profiles[item.updated_by], "nickname", None)


class ClientModuleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ClientModuleRepository(db)

    async def create(self, payload: ClientModuleCreateRequest) -> None:
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: ClientModuleUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysClientModuleSchema:
        schema = to_schema(SysClientModuleSchema, await self.repo.get_required(query.id))
        await _resolve_creator_names(self.db, [schema])
        return schema

    async def page_admin(
        self,
        query: ClientModuleAdminPageQuery,
    ) -> PageData[SysClientModuleSchema]:
        items, total = await self.repo.page_admin(query)
        schemas = to_schema_list(SysClientModuleSchema, items)
        await _resolve_creator_names(self.db, schemas)
        return build_page(query, total, schemas)

    async def selector(
        self,
        query: ClientModuleSelectorQuery,
    ) -> list[ClientModuleSelectorOption]:
        return to_schema_list(
            ClientModuleSelectorOption,
            await self.repo.list_enabled(query.account_type),
        )


class ClientResourceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ClientResourceRepository(db)

    async def create(self, payload: ClientResourceCreateRequest) -> None:
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: ClientResourceUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysClientResourceSchema:
        entity = await self.repo.get_required(query.id)
        schema = to_schema(SysClientResourceSchema, entity)
        await self._fill_module_meta([schema])
        await _resolve_creator_names(self.db, [schema])
        return schema

    async def page_admin(
        self,
        query: ClientResourceAdminPageQuery,
    ) -> PageData[SysClientResourceSchema]:
        items, total = await self.repo.page_admin(query)
        schemas = to_schema_list(SysClientResourceSchema, items)
        await self._fill_module_meta(schemas)
        await _resolve_creator_names(self.db, schemas)
        return build_page(query, total, schemas)

    async def list_tree(
        self,
        _session: SessionPayload | None,
        query: ClientResourceTreeQuery,
    ) -> list[ClientResourceTreeNode]:
        resources = await self.repo.list_resources(
            module_id=query.module_id,
            account_type=query.account_type,
        )
        return await self._build_tree_nodes(resources)

    async def bind_permission(
        self,
        payload: ClientResourcePermissionBindRequest,
        _session: SessionPayload | None = None,
    ) -> SysClientResourcePermissionRelSchema:
        await ensure_registered_permission(payload.permission_key)
        async with transactional(self.db):
            relation = await self.repo.bind_permission(payload)
        return SysClientResourcePermissionRelSchema(
            id=relation.id,
            resource_id=relation.subject_id,
            permission_key=relation.target_key,
            data_scope=relation.data_scope,
            custom_scope_dept_ids=list(relation.custom_scope_dept_ids or []),
            sort=relation.sort,
            status=relation.status,
            description=relation.description,
            created_at=relation.created_at,
            created_by=relation.created_by,
            updated_at=relation.updated_at,
            updated_by=relation.updated_by,
        )

    async def list_grant_modules(
        self,
        account_type: AccountType | None = None,
    ) -> list[ResourceGrantModuleOption]:
        return await self.repo.list_all_client_resource_grant_modules(account_type=account_type)

    async def _fill_module_meta(self, schemas: list[SysClientResourceSchema]) -> None:
        meta = await self.repo.list_module_meta_map(
            [item.module_id for item in schemas if item.module_id]
        )
        for schema in schemas:
            name, account_type = meta.get(schema.module_id or "", ("", None))
            schema.module_id_name = name
            schema.account_type = AccountType(account_type) if account_type else None

    async def _build_tree_nodes(
        self,
        resources: list[SysClientResource],
    ) -> list[ClientResourceTreeNode]:
        meta = await self.repo.list_module_meta_map(
            [resource.module_id for resource in resources if resource.module_id]
        )
        node_map = {
            resource.id: to_schema(ClientResourceTreeNode, resource) for resource in resources
        }
        for node in node_map.values():
            name, account_type = meta.get(node.module_id or "", ("", None))
            node.module_id_name = name
            node.account_type = AccountType(account_type) if account_type else None
        roots: list[ClientResourceTreeNode] = []
        for resource in resources:
            node = node_map[resource.id]
            if resource.parent_id and resource.parent_id in node_map:
                node_map[resource.parent_id].children.append(node)
            else:
                roots.append(node)
        return roots
