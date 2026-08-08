""" Author: Charlie """

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType, StatusEnum
from app.core.exceptions.business import ConflictError, NotFoundError
from app.modules.iam.enums import (
    IamRelationSubjectType,
    IamRelationTargetType,
    IamRelationType,
    ResourceType,
)
from app.modules.iam.reference_guard import (
    count_resource_references,
    ensure_not_self_or_descendant,
    list_descendant_ids,
    raise_if_referenced,
)
from app.modules.iam.relation.model import SysIamRelation
from app.modules.iam.relation.repository import IamRelationRepository
from app.modules.iam.resource.model import SysResource, SysResourceModule
from app.modules.iam.resource.schema import (
    ResourceAdminPageQuery,
    ResourceButtonPageQuery,
    ResourceCreateRequest,
    ResourceModuleAdminPageQuery,
    ResourceModuleCreateRequest,
    ResourceModuleUpdateRequest,
    ResourcePermissionBindRequest,
    ResourceUpdateRequest,
)
from app.modules.iam.schema import (
    ResourceGrantMenuOption,
    ResourceGrantModuleOption,
    ResourcePermissionOption,
)


class ResourceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.relations = IamRelationRepository(db)

    async def create(self, payload: ResourceCreateRequest) -> SysResource:
        await self._ensure_payload_valid(payload)
        resource = SysResource(**payload.model_dump())
        self.db.add(resource)
        await self.db.flush()
        return resource

    async def get_by_id(self, resource_id: str) -> SysResource | None:
        return await self.db.get(SysResource, resource_id)

    async def get_required(self, resource_id: str) -> SysResource:
        entity = await self.get_by_id(resource_id)
        if entity is None:
            raise NotFoundError("Resource not found")
        return entity

    async def update(self, payload: ResourceUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        await ensure_not_self_or_descendant(
            self.db,
            SysResource,
            payload.id,
            payload.parent_id,
            "Resource",
        )
        await self._ensure_payload_valid(payload, payload.id)
        old_module_id = entity.module_id
        if old_module_id != payload.module_id:
            await self._ensure_descendant_codes_unique_for_module(payload.id, payload.module_id)
        data = payload.model_dump(exclude={"id"})
        for key, value in data.items():
            setattr(entity, key, value)
        if old_module_id != payload.module_id:
            descendant_ids = await list_descendant_ids(self.db, SysResource, payload.id)
            if descendant_ids:
                await self.db.execute(
                    update(SysResource)
                    .where(SysResource.id.in_(descendant_ids))
                    .values(module_id=payload.module_id)
                )
        await self.db.flush()

    async def _ensure_payload_valid(
        self,
        payload: ResourceCreateRequest | ResourceUpdateRequest,
        resource_id: str | None = None,
    ) -> None:
        if payload.module_id and not await self.db.get(SysResourceModule, payload.module_id):
            raise ConflictError("Resource module does not exist")
        await self._ensure_resource_code_unique(payload.code, payload.module_id, resource_id)
        if not payload.parent_id:
            return
        parent = await self.db.get(SysResource, payload.parent_id)
        if parent is None:
            raise ConflictError("Resource parent does not exist")
        if resource_id is not None and parent.id == resource_id:
            raise ConflictError("Resource cannot move under itself")
        if parent.module_id != payload.module_id:
            raise ConflictError("Resource module must be same as parent resource module")

    async def _ensure_resource_code_unique(
        self,
        code: str,
        module_id: str | None,
        resource_id: str | None = None,
    ) -> None:
        stmt = select(SysResource.id).where(SysResource.code == code)
        if module_id is None:
            stmt = stmt.where(SysResource.module_id.is_(None))
        else:
            stmt = stmt.where(SysResource.module_id == module_id)
        if resource_id is not None:
            stmt = stmt.where(SysResource.id != resource_id)
        if (await self.db.execute(stmt)).scalar_one_or_none() is not None:
            raise ConflictError("Resource code already exists in module")

    async def _ensure_descendant_codes_unique_for_module(
        self,
        resource_id: str,
        module_id: str | None,
    ) -> None:
        descendant_ids = await list_descendant_ids(self.db, SysResource, resource_id)
        if not descendant_ids:
            return
        moving_ids = {resource_id, *descendant_ids}
        moving_codes = list(
            (
                await self.db.execute(
                    select(SysResource.code).where(SysResource.id.in_(descendant_ids))
                )
            )
            .scalars()
            .all()
        )
        if not moving_codes:
            return

        stmt = select(SysResource.id).where(
            SysResource.code.in_(moving_codes),
            SysResource.id.notin_(moving_ids),
        )
        if module_id is None:
            stmt = stmt.where(SysResource.module_id.is_(None))
        else:
            stmt = stmt.where(SysResource.module_id == module_id)
        if (await self.db.execute(stmt)).scalar_one_or_none() is not None:
            raise ConflictError("Resource code already exists in module")

    async def delete_many(self, resource_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(resource_ids))
        if not unique_ids:
            return
        stmt = select(SysResource.id).where(SysResource.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("Resource not found")
        raise_if_referenced("Resource", await count_resource_references(self.db, unique_ids))
        await self.db.execute(delete(SysResource).where(SysResource.id.in_(unique_ids)))

    async def page_admin(self, query: ResourceAdminPageQuery) -> tuple[list[SysResource], int]:
        stmt: Select[tuple[SysResource]] = select(SysResource)
        count_stmt = select(func.count(SysResource.id))
        filters = []
        if query.code:
            filters.append(SysResource.code.contains(query.code))
        if query.name:
            filters.append(SysResource.name.contains(query.name))
        if query.resource_type:
            filters.append(SysResource.resource_type == query.resource_type.value)
        if query.module_id:
            filters.append(SysResource.module_id == query.module_id)
        if query.module_client:
            stmt = stmt.join(SysResourceModule, SysResource.module_id == SysResourceModule.id)
            count_stmt = count_stmt.join(
                SysResourceModule,
                SysResource.module_id == SysResourceModule.id,
            )
            filters.append(SysResourceModule.client == query.module_client.value)
        if query.parent_id:
            filters.append(SysResource.parent_id == query.parent_id)
        if query.status:
            filters.append(SysResource.status == query.status)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(SysResource.sort.asc(), SysResource.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        resources = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return resources, total

    async def page_buttons(self, query: ResourceButtonPageQuery) -> tuple[list[SysResource], int]:
        stmt: Select[tuple[SysResource]] = select(SysResource).where(
            SysResource.parent_id == query.parent_id,
            SysResource.resource_type == ResourceType.BUTTON.value,
        )
        count_stmt = select(func.count(SysResource.id)).where(
            SysResource.parent_id == query.parent_id,
            SysResource.resource_type == ResourceType.BUTTON.value,
        )
        filters = []
        if query.code:
            filters.append(SysResource.code.contains(query.code))
        if query.name:
            filters.append(SysResource.name.contains(query.name))
        if query.status:
            filters.append(SysResource.status == query.status)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(SysResource.sort.asc(), SysResource.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        resources = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return resources, total

    async def list_resources(
        self,
        module_id: str | None = None,
        module_client: AccountType | None = None,
    ) -> list[SysResource]:
        stmt = (
            select(SysResource)
            .where(SysResource.status == StatusEnum.ENABLED.value)
            .order_by(
                SysResource.sort.asc(),
                SysResource.id.asc(),
            )
        )
        if module_id:
            stmt = stmt.where(SysResource.module_id == module_id)
        if module_client:
            stmt = stmt.join(SysResourceModule, SysResource.module_id == SysResourceModule.id)
            stmt = stmt.where(SysResourceModule.client == module_client.value)
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_module_meta_map(self, module_ids: list[str]) -> dict[str, tuple[str, str]]:
        unique_ids = list(dict.fromkeys(module_ids))
        if not unique_ids:
            return {}
        rows = (
            await self.db.execute(
                select(
                    SysResourceModule.id,
                    SysResourceModule.name,
                    SysResourceModule.client,
                ).where(SysResourceModule.id.in_(unique_ids))
            )
        ).all()
        return {str(module_id): (str(name), str(client)) for module_id, name, client in rows}

    async def bind_resource_permission(
        self,
        payload: ResourcePermissionBindRequest,
    ) -> SysIamRelation:
        if not await self.db.get(SysResource, payload.resource_id):
            raise NotFoundError("Resource not found")
        data = payload.model_dump()
        data["account_type"] = payload.account_type.value
        relation = self.relations.resource_permission(**data)
        self.db.add(relation)
        await self.db.flush()
        return relation

    async def replace_resource_permission(
        self,
        payload: ResourcePermissionBindRequest,
    ) -> SysIamRelation:
        if not await self.db.get(SysResource, payload.resource_id):
            raise NotFoundError("Resource not found")
        await self.relations.delete_subject_relations(
            IamRelationSubjectType.RESOURCE.value,
            payload.resource_id,
            IamRelationType.RESOURCE_PERMISSION,
            account_type=payload.account_type.value,
        )
        data = payload.model_dump()
        data["account_type"] = payload.account_type.value
        relation = self.relations.resource_permission(**data)
        self.db.add(relation)
        await self.db.flush()
        return relation

    async def delete_button(self, button_id: str) -> None:
        button = await self.get_required(button_id)
        if button.resource_type != ResourceType.BUTTON.value:
            raise ConflictError("Resource is not a button")
        await self.relations.delete_subject_relations(
            IamRelationSubjectType.RESOURCE.value,
            button_id,
            IamRelationType.RESOURCE_PERMISSION,
        )
        await self.delete_many([button_id])

    async def list_resource_permissions(
        self,
        account_type: AccountType | None = None,
    ) -> list[SysIamRelation]:
        stmt = (
            select(SysIamRelation)
            .where(
                SysIamRelation.subject_type == IamRelationSubjectType.RESOURCE.value,
                SysIamRelation.relation_type == IamRelationType.RESOURCE_PERMISSION.value,
                SysIamRelation.target_type == IamRelationTargetType.PERMISSION.value,
                SysIamRelation.status == StatusEnum.ENABLED.value,
            )
            .order_by(SysIamRelation.sort.asc(), SysIamRelation.id.asc())
        )
        if account_type is not None:
            stmt = stmt.where(SysIamRelation.account_type == account_type.value)
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_permissions_by_resource_ids(
        self,
        resource_ids: list[str],
    ) -> dict[str, list[SysIamRelation]]:
        unique_ids = list(dict.fromkeys(resource_ids))
        if not unique_ids:
            return {}
        stmt = (
            select(SysIamRelation)
            .where(
                SysIamRelation.subject_type == IamRelationSubjectType.RESOURCE.value,
                SysIamRelation.relation_type == IamRelationType.RESOURCE_PERMISSION.value,
                SysIamRelation.target_type == IamRelationTargetType.PERMISSION.value,
                SysIamRelation.subject_id.in_(unique_ids),
            )
            .order_by(SysIamRelation.sort.asc(), SysIamRelation.id.asc())
        )
        result: dict[str, list[SysIamRelation]] = {}
        for permission in (await self.db.execute(stmt)).scalars().all():
            result.setdefault(permission.subject_id, []).append(permission)
        return result

    async def list_resources_by_ids_with_parents(
        self,
        resource_ids: list[str],
        module_client: AccountType | None = None,
    ) -> list[SysResource]:
        unique_ids = set(resource_ids)
        if not unique_ids:
            return []
        all_resources = await self.list_resources(module_client=module_client)
        resource_map = {resource.id: resource for resource in all_resources}
        result_ids: set[str] = set()
        for resource_id in unique_ids:
            current = resource_map.get(resource_id)
            while current:
                result_ids.add(current.id)
                current = resource_map.get(current.parent_id or "")
        return [resource for resource in all_resources if resource.id in result_ids]

    async def list_all_resource_grant_modules(
        self,
        module_client: AccountType | None = None,
    ) -> list[ResourceGrantModuleOption]:
        resources = await self.list_resources(module_client=module_client)
        permissions = await self.list_resource_permissions(account_type=module_client)
        modules = await ResourceModuleRepository(self.db).list_enabled_modules(client=module_client)
        permission_map: dict[str, list[ResourcePermissionOption]] = {}
        for permission in permissions:
            permission_map.setdefault(permission.subject_id, []).append(
                ResourcePermissionOption(
                    id=permission.id,
                    permission_key=permission.target_key,
                    title=permission.description or permission.target_key,
                    data_scope=permission.data_scope,
                )
            )
        resource_map = {resource.id: resource for resource in resources}
        child_permission_map: dict[str, list[ResourcePermissionOption]] = {}
        for resource in resources:
            if resource.resource_type not in {ResourceType.BUTTON.value, ResourceType.ACTION.value}:
                continue
            if not resource.parent_id:
                continue
            options = permission_map.get(resource.id)
            if not options:
                options = [
                    ResourcePermissionOption(
                        id=resource.id,
                        permission_key=resource.code,
                        title=resource.name,
                    )
                ]
            child_permission_map.setdefault(resource.parent_id, []).extend(options)
        module_map: dict[str, ResourceGrantModuleOption] = {
            module.id: ResourceGrantModuleOption(
                id=module.id,
                title=module.name,
                menu=[],
            )
            for module in modules
        }
        module_sort_map = {module.id: module.sort for module in modules}
        # CATALOG 只充当父级分组标签，不单独出现在「菜单」列；
        # 无父级时用资源自身名称分组，避免伪造 ROOT 父级授权。
        grant_menu_types = {
            ResourceType.MENU.value,
            ResourceType.PAGE.value,
            ResourceType.API_GROUP.value,
        }
        for resource in resources:
            if resource.resource_type not in grant_menu_types:
                continue
            if not resource.module_id:
                continue
            module_id = resource.module_id
            module = module_map.setdefault(
                module_id,
                ResourceGrantModuleOption(id=module_id, title=module_id, menu=[]),
            )
            parent = resource_map.get(resource.parent_id or "")
            module.menu.append(
                ResourceGrantMenuOption(
                    id=resource.id,
                    module_id=module_id,
                    parent_id=resource.parent_id,
                    parent_id_name=parent.name if parent else resource.name,
                    title=resource.name,
                    button=(
                        permission_map.get(resource.id, [])
                        + child_permission_map.get(resource.id, [])
                    ),
                )
            )
        return sorted(
            [module for module in module_map.values() if module.menu],
            key=lambda item: (module_sort_map.get(item.id, 99), item.id),
        )


class ResourceModuleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: ResourceModuleCreateRequest) -> None:
        await self._ensure_code_unique(payload.code)
        module = SysResourceModule(**payload.model_dump())
        self.db.add(module)
        await self.db.flush()

    async def get_by_id(self, module_id: str) -> SysResourceModule | None:
        return await self.db.get(SysResourceModule, module_id)

    async def get_required(self, module_id: str) -> SysResourceModule:
        entity = await self.get_by_id(module_id)
        if entity is None:
            raise NotFoundError("Resource module not found")
        return entity

    async def update(self, payload: ResourceModuleUpdateRequest) -> None:
        entity = await self.get_required(payload.id)
        await self._ensure_code_unique(payload.code, payload.id)
        data = payload.model_dump(exclude={"id"})
        for key, value in data.items():
            setattr(entity, key, value)
        await self.db.flush()

    async def delete_many(self, module_ids: list[str]) -> None:
        unique_ids = list(dict.fromkeys(module_ids))
        if not unique_ids:
            return
        stmt = select(SysResourceModule.id).where(SysResourceModule.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("Resource module not found")
        reference_count = await self.count_resource_references(unique_ids)
        if reference_count > 0:
            raise ConflictError(f"Resource module is referenced: resources={reference_count}")
        await self.db.execute(delete(SysResourceModule).where(SysResourceModule.id.in_(unique_ids)))

    async def page_admin(
        self,
        query: ResourceModuleAdminPageQuery,
    ) -> tuple[list[SysResourceModule], int]:
        stmt: Select[tuple[SysResourceModule]] = select(SysResourceModule)
        count_stmt = select(func.count(SysResourceModule.id))
        filters = []
        if query.name:
            filters.append(SysResourceModule.name.contains(query.name))
        if query.code:
            filters.append(SysResourceModule.code.contains(query.code))
        if query.client:
            filters.append(SysResourceModule.client == query.client.value)
        if query.status:
            filters.append(SysResourceModule.status == query.status)
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(SysResourceModule.sort.asc(), SysResourceModule.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        modules = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return modules, total

    async def list_enabled_modules(
        self,
        client: AccountType | None = None,
    ) -> list[SysResourceModule]:
        stmt = (
            select(SysResourceModule)
            .where(SysResourceModule.status == StatusEnum.ENABLED.value)
            .order_by(SysResourceModule.sort.asc(), SysResourceModule.id.asc())
        )
        if client:
            stmt = stmt.where(SysResourceModule.client == client.value)
        return list((await self.db.execute(stmt)).scalars().all())

    async def count_resource_references(self, module_ids: list[str]) -> int:
        unique_ids = list(dict.fromkeys(module_ids))
        if not unique_ids:
            return 0
        stmt = select(func.count(SysResource.id)).where(SysResource.module_id.in_(unique_ids))
        return int((await self.db.execute(stmt)).scalar_one())

    async def _ensure_code_unique(self, code: str, module_id: str | None = None) -> None:
        stmt = select(SysResourceModule.id).where(SysResourceModule.code == code)
        if module_id is not None:
            stmt = stmt.where(SysResourceModule.id != module_id)
        if (await self.db.execute(stmt)).scalar_one_or_none() is not None:
            raise ConflictError("Resource module code already exists")
