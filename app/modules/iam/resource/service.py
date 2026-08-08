""" Author: Charlie """

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.exceptions.business import AuthorizationError, ConflictError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.data_scope import resolve_data_scope_dept_ids
from app.core.security.permission_registry import list_permission_resources
from app.core.security.session import SessionPayload
from app.modules.iam.enums import ResourceType
from app.modules.iam.permission.service import ensure_registered_permission
from app.modules.iam.relation.repository import IamRelationRepository
from app.modules.iam.resource.model import SysResource
from app.modules.iam.resource.repository import ResourceModuleRepository, ResourceRepository
from app.modules.iam.resource.schema import (
    ResourceAdminPageQuery,
    ResourceButtonCreateRequest,
    ResourceButtonPageQuery,
    ResourceButtonSchema,
    ResourceButtonUpdateRequest,
    ResourceCreateRequest,
    ResourceModuleAdminPageQuery,
    ResourceModuleCreateRequest,
    ResourceModuleSelectorOption,
    ResourceModuleSelectorQuery,
    ResourceModuleUpdateRequest,
    ResourcePermissionBindRequest,
    ResourceTreeNode,
    ResourceTreeQuery,
    ResourceUpdateRequest,
    SysResourceModuleSchema,
    SysResourcePermissionRelSchema,
    SysResourceSchema,
)
from app.modules.iam.schema import PermissionRegistryItem, ResourceGrantModuleOption
from app.modules.user.utils.profile import get_profiles_batch
from app.platform.db.transaction import transactional


async def _resolve_creator_names(db: AsyncSession, items: list) -> None:
    """批量查询 created_by / updated_by 对应的昵称。"""
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


class ResourceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ResourceRepository(db)

    async def create(self, payload: ResourceCreateRequest) -> None:
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: ResourceUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysResourceSchema:
        return (await self._build_resource_schemas([await self.repo.get_required(query.id)]))[0]

    async def page_admin(self, query: ResourceAdminPageQuery) -> PageData[SysResourceSchema]:
        items, total = await self.repo.page_admin(query)
        return build_page(query, total, await self._build_resource_schemas(items))

    async def page_buttons(self, query: ResourceButtonPageQuery) -> PageData[ResourceButtonSchema]:
        await self._get_button_parent(query.parent_id)
        items, total = await self.repo.page_buttons(query)
        return build_page(query, total, await self._build_button_schemas(items))

    async def bind_resource_permission(
        self,
        payload: ResourcePermissionBindRequest,
        session: SessionPayload | None = None,
    ) -> SysResourcePermissionRelSchema:
        if session is not None:
            await self._ensure_depts_visible(
                session,
                "iam:resource:grant",
                payload.custom_scope_dept_ids,
            )
        await ensure_registered_permission(payload.permission_key)
        async with transactional(self.db):
            return to_schema(
                SysResourcePermissionRelSchema,
                await self.repo.bind_resource_permission(payload),
            )

    async def create_button(
        self,
        payload: ResourceButtonCreateRequest,
        session: SessionPayload | None = None,
    ) -> ResourceButtonSchema:
        parent = await self._prepare_button_permission(payload, session)
        async with transactional(self.db):
            button = await self.repo.create(self._build_button_resource_payload(payload, parent))
            await self.repo.replace_resource_permission(
                self._build_button_permission_payload(button.id, payload)
            )
            return (await self._build_button_schemas([button]))[0]

    async def update_button(
        self,
        payload: ResourceButtonUpdateRequest,
        session: SessionPayload | None = None,
    ) -> ResourceButtonSchema:
        button = await self.repo.get_required(payload.id)
        if button.resource_type != ResourceType.BUTTON.value:
            raise ConflictError("Resource is not a button")
        parent = await self._prepare_button_permission(payload, session)
        async with transactional(self.db):
            await self.repo.update(
                ResourceUpdateRequest(
                    id=payload.id,
                    **self._build_button_resource_payload(payload, parent).model_dump(),
                )
            )
            await self.repo.replace_resource_permission(
                self._build_button_permission_payload(payload.id, payload)
            )
            return (await self._build_button_schemas([await self.repo.get_required(payload.id)]))[0]

    async def delete_button(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            for button_id in dict.fromkeys(payload.ids):
                await self.repo.delete_button(button_id)

    async def list_resource_tree(
        self,
        session: SessionPayload,
        query: ResourceTreeQuery,
    ) -> list[ResourceTreeNode]:
        resources = await self._list_visible_resources(
            session,
            module_id=query.module_id,
            module_client=query.module_client,
        )
        resources = [
            resource
            for resource in resources
            if resource.resource_type not in {ResourceType.BUTTON.value, ResourceType.ACTION.value}
        ]
        return await self._build_resource_tree_nodes(resources)

    async def list_current_resources(
        self,
        session: SessionPayload,
        module_client: AccountType | None = None,
    ) -> list[SysResourceSchema]:
        resources = await self._list_visible_resources(
            session,
            module_client=module_client,
        )
        return await self._build_resource_schemas(resources)

    async def list_public_portal_resources(self) -> list[SysResourceSchema]:
        resources = await self.repo.list_resources(module_client=AccountType.PORTAL)
        return await self._build_resource_schemas(resources)

    async def _list_visible_resources(
        self,
        session: SessionPayload,
        module_id: str | None = None,
        module_client: AccountType | None = None,
    ) -> list[SysResource]:
        if "*:*:*" in session.permission_keys:
            return await self.repo.list_resources(
                module_id=module_id,
                module_client=module_client,
            )
        resource_ids = session.resource_ids
        if not resource_ids:
            resource_ids = await IamRelationRepository(self.db).get_account_resource_ids(
                session.account_id
            )
        resources = await self.repo.list_resources_by_ids_with_parents(
            resource_ids,
            module_client=module_client,
        )
        if module_id:
            resources = [resource for resource in resources if resource.module_id == module_id]
        return resources

    async def list_grant_modules(
        self,
        module_client: AccountType | None = None,
    ) -> list[ResourceGrantModuleOption]:
        return await self.repo.list_all_resource_grant_modules(module_client=module_client)

    async def _build_resource_schemas(
        self,
        resources: list[SysResource],
    ) -> list[SysResourceSchema]:
        module_meta_map = await self.repo.list_module_meta_map(
            [resource.module_id for resource in resources if resource.module_id]
        )
        schemas = to_schema_list(SysResourceSchema, resources)
        for schema in schemas:
            module_name, module_client = module_meta_map.get(schema.module_id or "", ("", None))
            schema.module_id_name = module_name
            schema.module_client = module_client
        await _resolve_creator_names(self.db, schemas)
        return schemas

    async def _build_button_schemas(
        self,
        resources: list[SysResource],
    ) -> list[ResourceButtonSchema]:
        schemas = to_schema_list(ResourceButtonSchema, resources)
        permission_map = await self.repo.list_permissions_by_resource_ids(
            [resource.id for resource in resources]
        )
        for schema in schemas:
            permissions = permission_map.get(schema.id, [])
            permission = permissions[0] if permissions else None
            if permission is None:
                continue
            schema.permission_rel_id = permission.id
            schema.permission_key = permission.permission_key
            schema.data_scope = permission.data_scope
            schema.custom_scope_dept_ids = list(permission.custom_scope_dept_ids or [])
            schema.permission_description = permission.description
        return schemas

    async def _build_resource_tree_nodes(
        self,
        resources: list[SysResource],
    ) -> list[ResourceTreeNode]:
        module_meta_map = await self.repo.list_module_meta_map(
            [resource.module_id for resource in resources if resource.module_id]
        )
        return _build_resource_tree_nodes(resources, module_meta_map)

    async def list_permission_registry_items(self) -> list[PermissionRegistryItem]:
        resources = await list_permission_resources()
        items: list[PermissionRegistryItem] = []
        for resource in resources:
            index = resource.find("[")
            permission_key = resource[:index] if index > -1 else resource
            name = (
                resource[index + 1 : -1]
                if index > -1 and resource.endswith("]")
                else permission_key
            )
            items.append(PermissionRegistryItem(permission_key=permission_key, name=name))
        return sorted(items, key=lambda item: item.permission_key)

    async def _ensure_depts_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        dept_ids: list[str],
    ) -> None:
        unique_ids = list(dict.fromkeys(dept_ids))
        if not unique_ids:
            return
        visible_dept_ids = await resolve_data_scope_dept_ids(self.db, session, permission_key)
        if visible_dept_ids is None:
            return
        allowed_ids = set(visible_dept_ids)
        if any(dept_id not in allowed_ids for dept_id in unique_ids):
            raise AuthorizationError("Dept is outside current data scope")

    async def _get_button_parent(self, parent_id: str) -> SysResource:
        parent = await self.repo.get_required(parent_id)
        if parent.resource_type in {ResourceType.BUTTON.value, ResourceType.ACTION.value}:
            raise ConflictError("Button resource cannot be parent resource")
        return parent

    async def _prepare_button_permission(
        self,
        payload: ResourceButtonCreateRequest | ResourceButtonUpdateRequest,
        session: SessionPayload | None,
    ) -> SysResource:
        parent = await self._get_button_parent(payload.parent_id)
        if session is not None:
            await self._ensure_depts_visible(
                session,
                "iam:resource:grant",
                payload.custom_scope_dept_ids,
            )
        await ensure_registered_permission(payload.permission_key)
        return parent

    def _build_button_resource_payload(
        self,
        payload: ResourceButtonCreateRequest | ResourceButtonUpdateRequest,
        parent: SysResource,
    ) -> ResourceCreateRequest:
        return ResourceCreateRequest(
            code=payload.code,
            name=payload.name,
            resource_type=ResourceType.BUTTON,
            parent_id=parent.id,
            module_id=parent.module_id,
            path=None,
            component=None,
            redirect=None,
            icon=None,
            color=None,
            href=None,
            sort=payload.sort,
            is_visible=False,
            is_cache=False,
            is_affix=False,
            status=payload.status,
            description=payload.description,
            extra={},
        )

    def _build_button_permission_payload(
        self,
        button_id: str,
        payload: ResourceButtonCreateRequest | ResourceButtonUpdateRequest,
    ) -> ResourcePermissionBindRequest:
        return ResourcePermissionBindRequest(
            resource_id=button_id,
            permission_key=payload.permission_key,
            data_scope=payload.data_scope,
            custom_scope_dept_ids=payload.custom_scope_dept_ids,
            sort=payload.sort,
            description=payload.description,
        )


class ResourceModuleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ResourceModuleRepository(db)

    async def create(self, payload: ResourceModuleCreateRequest) -> None:
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: ResourceModuleUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysResourceModuleSchema:
        schema = to_schema(SysResourceModuleSchema, await self.repo.get_required(query.id))
        await _resolve_creator_names(self.db, [schema])
        return schema

    async def page_admin(
        self,
        query: ResourceModuleAdminPageQuery,
    ) -> PageData[SysResourceModuleSchema]:
        items, total = await self.repo.page_admin(query)
        schemas = to_schema_list(SysResourceModuleSchema, items)
        await _resolve_creator_names(self.db, schemas)
        return build_page(query, total, schemas)

    async def selector(
        self,
        query: ResourceModuleSelectorQuery,
    ) -> list[ResourceModuleSelectorOption]:
        return to_schema_list(
            ResourceModuleSelectorOption,
            await self.repo.list_enabled_modules(query.client),
        )


def _build_resource_tree_nodes(
    resources: list[SysResource],
    module_meta_map: dict[str, tuple[str, str]],
) -> list[ResourceTreeNode]:
    node_map = {resource.id: to_schema(ResourceTreeNode, resource) for resource in resources}
    for node in node_map.values():
        module_name, module_client = module_meta_map.get(node.module_id or "", ("", None))
        node.module_id_name = module_name
        node.module_client = module_client
    roots: list[ResourceTreeNode] = []
    for resource in resources:
        node = node_map[resource.id]
        if resource.parent_id and resource.parent_id in node_map:
            node_map[resource.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots
