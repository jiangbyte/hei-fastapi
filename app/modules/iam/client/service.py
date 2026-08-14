""" Author: Charlie

客户端模块/资源应用服务：CRUD、树组装与授权模块渲染。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.db.transaction import transactional
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.permission_registry import ensure_registered_permission_key
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
from app.modules.iam.schema import ResourceGrantModuleOption
from app.modules.user.utils.profile import enrich_audit_names


class ClientModuleService:
    """客户端模块应用服务。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ClientModuleRepository(db)

    async def create(self, payload: ClientModuleCreateRequest) -> None:
        """创建客户端模块。"""
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: ClientModuleUpdateRequest) -> None:
        """更新客户端模块。"""
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        """批量删除客户端模块。"""
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysClientModuleSchema:
        """查询客户端模块详情并回显创建人/更新人昵称。"""
        schema = to_schema(SysClientModuleSchema, await self.repo.get_required(query.id))
        await enrich_audit_names(self.db, [schema], account_type=AccountType.ADMIN)
        return schema

    async def page_admin(
        self,
        query: ClientModuleAdminPageQuery,
    ) -> PageData[SysClientModuleSchema]:
        """分页查询客户端模块。"""
        items, total = await self.repo.page_admin(query)
        schemas = to_schema_list(SysClientModuleSchema, items)
        await enrich_audit_names(self.db, schemas, account_type=AccountType.ADMIN)
        return build_page(query, total, schemas)

    async def selector(
        self,
        query: ClientModuleSelectorQuery,
    ) -> list[ClientModuleSelectorOption]:
        """返回启用的客户端模块下拉选项。"""
        return to_schema_list(
            ClientModuleSelectorOption,
            await self.repo.list_enabled(query.account_type),
        )


class ClientResourceService:
    """客户端资源应用服务，负责资源 CRUD、树组装与权限绑定。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ClientResourceRepository(db)

    async def create(self, payload: ClientResourceCreateRequest) -> None:
        """创建客户端资源。"""
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: ClientResourceUpdateRequest) -> None:
        """更新客户端资源。"""
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        """批量删除客户端资源。"""
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysClientResourceSchema:
        """查询客户端资源详情，填充模块元信息与创建人昵称。"""
        entity = await self.repo.get_required(query.id)
        schema = to_schema(SysClientResourceSchema, entity)
        await self._fill_module_meta([schema])
        await enrich_audit_names(self.db, [schema], account_type=AccountType.ADMIN)
        return schema

    async def page_admin(
        self,
        query: ClientResourceAdminPageQuery,
    ) -> PageData[SysClientResourceSchema]:
        """分页查询客户端资源。"""
        items, total = await self.repo.page_admin(query)
        schemas = to_schema_list(SysClientResourceSchema, items)
        await self._fill_module_meta(schemas)
        await enrich_audit_names(self.db, schemas, account_type=AccountType.ADMIN)
        return build_page(query, total, schemas)

    async def list_tree(
        self,
        _session: SessionPayload | None,
        query: ClientResourceTreeQuery,
    ) -> list[ClientResourceTreeNode]:
        """查询客户端资源并组装为树结构。"""
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
        """校验权限码后绑定客户端资源权限。"""
        await ensure_registered_permission_key(payload.permission_key)
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
        """返回授权页所需的客户端资源模块树。"""
        return await self.repo.list_all_client_resource_grant_modules(account_type=account_type)

    async def _fill_module_meta(self, schemas: list[SysClientResourceSchema]) -> None:
        """批量填充模块名称与账户体系到资源 Schema。"""
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
        """将扁平资源列表组装为带模块元信息的树节点。"""
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
