""" Author: Charlie

部门应用服务：部门 CRUD、数据范围可见性校验与名称回显。
"""

from collections.abc import Mapping, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.db.transaction import transactional
from app.core.exceptions.business import AuthorizationError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.data_scope import build_data_scope_filter, resolve_data_scope_dept_ids
from app.core.security.session import SessionPayload
from app.modules.iam.dept.model import SysDept
from app.modules.iam.dept.repository import DeptRepository, DeptTreeRecord
from app.modules.iam.dept.schema import (
    DeptAdminPageQuery,
    DeptCreateRequest,
    DeptTreeNode,
    DeptUpdateRequest,
    SysDeptSchema,
)
from app.modules.profile.utils.profile import get_profiles_batch


class DeptService:
    """部门应用服务。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DeptRepository(db)

    async def create(
        self, payload: DeptCreateRequest, session: SessionPayload | None = None
    ) -> None:
        """创建部门，传入 session 时校验父级部门可见性。"""
        if session is not None and payload.parent_id:
            await self._ensure_dept_ids_visible(session, "iam:dept:create", [payload.parent_id])
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(
        self, payload: DeptUpdateRequest, session: SessionPayload | None = None
    ) -> None:
        """更新部门，传入 session 时校验目标及父级可见性。"""
        if session is not None:
            await self._ensure_dept_records_visible(session, "iam:dept:update", [payload.id])
            if payload.parent_id:
                await self._ensure_dept_records_visible(
                    session, "iam:dept:update", [payload.parent_id]
                )
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest, session: SessionPayload | None = None) -> None:
        """删除部门，传入 session 时先校验可见性。"""
        if session is not None:
            await self._ensure_dept_records_visible(session, "iam:dept:delete", payload.ids)
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery, session: SessionPayload | None = None) -> SysDeptSchema:
        """查询部门详情并回显名称。"""
        if session is not None:
            await self._ensure_dept_records_visible(session, "iam:dept:detail", [query.id])
        result = to_schema(SysDeptSchema, await self.repo.get_required(query.id))
        await self._resolve_names([result])
        return result

    async def page_admin(
        self,
        query: DeptAdminPageQuery,
        session: SessionPayload | None = None,
    ) -> PageData[SysDeptSchema]:
        """分页查询部门，叠加数据范围过滤。"""
        data_scope_filter = (
            await self._dept_scope_filter(session, "iam:dept:page") if session is not None else None
        )
        items, total = await self.repo.page_admin(query, data_scope_filter)
        dtos = to_schema_list(SysDeptSchema, items)
        await self._resolve_names(dtos)
        return build_page(query, total, dtos)

    async def list_dept_tree(self, session: SessionPayload | None = None) -> list[DeptTreeNode]:
        """返回部门树，并批量回显负责人名称。"""
        data_scope_filter = (
            await self._dept_scope_filter(session, "iam:dept:tree") if session is not None else None
        )
        raw_records = await self.repo.get_dept_tree(data_scope_filter)

        # 批量回显负责人名称
        all_ids: set[str] = set()

        def collect_ids(nodes: list[DeptTreeRecord]) -> None:
            for n in nodes:
                if n.get("master_id"):
                    all_ids.add(str(n["master_id"]))
                if n.get("deputy_master_id"):
                    all_ids.add(str(n["deputy_master_id"]))
                if n.get("children"):
                    collect_ids(n["children"])

        collect_ids(raw_records)

        if all_ids:
            name_map = await self.repo.resolve_account_names(list(all_ids))

            def apply_names(nodes: list[DeptTreeRecord]) -> None:
                for n in nodes:
                    mid = n.get("master_id")
                    if mid and str(mid) in name_map:
                        n["master_name"] = name_map[str(mid)]
                    did = n.get("deputy_master_id")
                    if did and str(did) in name_map:
                        n["deputy_master_name"] = name_map[str(did)]
                    if n.get("children"):
                        apply_names(n["children"])

            apply_names(raw_records)

        return _build_dept_tree_nodes(raw_records)

    async def _resolve_names(self, dtos: list[SysDeptSchema]) -> None:
        """批量回显负责人/副负责人名称和父级部门名称，避免 N+1 查询。"""
        account_ids = set()
        parent_ids = set()
        for dto in dtos:
            if dto.master_id:
                account_ids.add(dto.master_id)
            if dto.deputy_master_id:
                account_ids.add(dto.deputy_master_id)
            if dto.parent_id:
                parent_ids.add(dto.parent_id)
        # 解析创建人/更新人昵称
        creator_ids: set[str] = set()
        for dto in dtos:
            if dto.created_by:
                creator_ids.add(dto.created_by)
            if dto.updated_by:
                creator_ids.add(dto.updated_by)
        if creator_ids:
            profiles = await get_profiles_batch(self.db, AccountType.ADMIN, list(creator_ids))
            for dto in dtos:
                if dto.created_by and dto.created_by in profiles:
                    dto.created_name = getattr(profiles[dto.created_by], "nickname", None)
                if dto.updated_by and dto.updated_by in profiles:
                    dto.updated_name = getattr(profiles[dto.updated_by], "nickname", None)
        if account_ids:
            name_map = await self.repo.resolve_account_names(list(account_ids))
            for dto in dtos:
                if dto.master_id and dto.master_id in name_map:
                    dto.master_name = name_map[dto.master_id]
                if dto.deputy_master_id and dto.deputy_master_id in name_map:
                    dto.deputy_master_name = name_map[dto.deputy_master_id]
        if parent_ids:
            dept_map = await self.repo.resolve_dept_names(list(parent_ids))
            for dto in dtos:
                if dto.parent_id and dto.parent_id in dept_map:
                    dto.parent_name = dept_map[dto.parent_id]

    async def _dept_scope_filter(self, session: SessionPayload, permission_key: str):
        """构造部门数据范围过滤条件。"""
        return await build_data_scope_filter(
            self.db,
            session,
            permission_key,
            owner_column=SysDept.created_by,
            dept_column=SysDept.id,
        )

    async def _ensure_dept_records_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        dept_ids: list[str],
    ) -> None:
        """校验目标部门均在当前数据范围内，否则抛授权错误。"""
        unique_ids = list(dict.fromkeys(dept_ids))
        if not unique_ids:
            return
        data_scope_filter = await self._dept_scope_filter(session, permission_key)
        if await self.repo.count_depts_in_scope(unique_ids, data_scope_filter) != len(unique_ids):
            raise AuthorizationError("Dept is outside current data scope")

    async def _ensure_dept_ids_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        dept_ids: list[str],
    ) -> None:
        """按解析出的可见部门 ID 校验目标部门可见性。"""
        unique_ids = list(dict.fromkeys(dept_ids))
        if not unique_ids:
            return
        visible_dept_ids = await resolve_data_scope_dept_ids(self.db, session, permission_key)
        if visible_dept_ids is None:
            return
        allowed_ids = set(visible_dept_ids)
        if any(dept_id not in allowed_ids for dept_id in unique_ids):
            raise AuthorizationError("Dept is outside current data scope")


def _build_dept_tree_nodes(
    items: Sequence[DeptTreeRecord | DeptTreeNode | Mapping[str, object]],
) -> list[DeptTreeNode]:
    """将树记录递归转换为 DeptTreeNode 响应结构。"""
    nodes: list[DeptTreeNode] = []
    for item in items:
        raw_item: Mapping[str, object] = (
            item.model_dump() if isinstance(item, DeptTreeNode) else item
        )
        nodes.append(
            DeptTreeNode(
                id=str(raw_item["id"]),
                name=str(raw_item["name"]),
                category=str(raw_item["category"]),
                parent_id=str(raw_item["parent_id"]) if raw_item.get("parent_id") else None,
                master_id=str(raw_item["master_id"]) if raw_item.get("master_id") else None,
                master_name=str(raw_item["master_name"]) if raw_item.get("master_name") else None,
                deputy_master_id=str(raw_item["deputy_master_id"])
                if raw_item.get("deputy_master_id")
                else None,
                deputy_master_name=str(raw_item["deputy_master_name"])
                if raw_item.get("deputy_master_name")
                else None,
                status=str(raw_item.get("status", "ENABLED")),
                sort=int(raw_item.get("sort", 99)),
                weight=int(raw_item.get("weight", raw_item.get("sort", 99))),
                is_virtual=bool(raw_item.get("is_virtual", False)),
                extra=dict(raw_item.get("extra", {})),
                created_at=raw_item["created_at"],
                created_by=str(raw_item["created_by"]) if raw_item.get("created_by") else None,
                updated_at=raw_item.get("updated_at"),
                updated_by=str(raw_item["updated_by"]) if raw_item.get("updated_by") else None,
                children=_build_dept_tree_children(raw_item.get("children", [])),
            )
        )
    return nodes


def _build_dept_tree_children(
    items: Sequence[DeptTreeRecord | DeptTreeNode | Mapping[str, object]],
) -> list[DeptTreeNode] | None:
    """子节点为空时返回 None，使 JSON 省略 children 键（对齐 hei-boot）。"""
    nodes = _build_dept_tree_nodes(items)
    return nodes or None
