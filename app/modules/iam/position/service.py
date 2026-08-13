""" Author: Charlie

职位应用服务：职位 CRUD、数据范围可见性校验与名称回显。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType
from app.core.exceptions.business import AuthorizationError
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.data_scope import build_data_scope_filter, resolve_data_scope_dept_ids
from app.core.security.session import SessionPayload
from app.modules.iam.position.model import SysPosition
from app.modules.iam.position.repository import PositionRepository
from app.modules.iam.position.schema import (
    PositionAdminPageQuery,
    PositionCreateRequest,
    PositionUpdateRequest,
    SysPositionSchema,
)
from app.modules.user.utils.profile import get_profiles_batch
from app.platform.db.transaction import transactional


class PositionService:
    """职位应用服务。"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PositionRepository(db)

    async def create(
        self, payload: PositionCreateRequest, session: SessionPayload | None = None
    ) -> None:
        """创建职位，传入 session 时校验所属部门可见性。"""
        if session is not None and payload.owner_dept_id:
            await self._ensure_depts_visible(
                session, "iam:position:create", [payload.owner_dept_id]
            )
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(
        self, payload: PositionUpdateRequest, session: SessionPayload | None = None
    ) -> None:
        """更新职位，传入 session 时校验职位与所属部门可见性。"""
        if session is not None:
            await self._ensure_positions_visible(session, "iam:position:update", [payload.id])
            if payload.owner_dept_id:
                await self._ensure_depts_visible(
                    session, "iam:position:update", [payload.owner_dept_id]
                )
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest, session: SessionPayload | None = None) -> None:
        """删除职位，传入 session 时先校验可见性。"""
        if session is not None:
            await self._ensure_positions_visible(session, "iam:position:delete", payload.ids)
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(
        self, query: IdQuery, session: SessionPayload | None = None
    ) -> SysPositionSchema:
        """查询职位详情并回显创建人昵称。"""
        if session is not None:
            await self._ensure_positions_visible(session, "iam:position:detail", [query.id])
        schema = to_schema(SysPositionSchema, await self.repo.get_required(query.id))
        await self._resolve_creator_names([schema])
        return schema

    async def page_admin(
        self,
        query: PositionAdminPageQuery,
        session: SessionPayload | None = None,
    ) -> PageData[SysPositionSchema]:
        """分页查询职位，叠加数据范围过滤。"""
        data_scope_filter = (
            await self._position_scope_filter(session, "iam:position:page")
            if session is not None
            else None
        )
        items, total = await self.repo.page_admin(query, data_scope_filter)
        schemas = to_schema_list(SysPositionSchema, items)
        await self._resolve_creator_names(schemas)
        return build_page(query, total, schemas)

    async def _resolve_creator_names(self, items: list[SysPositionSchema]) -> None:
        """批量查询 created_by / updated_by 对应的昵称。"""
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

    async def _position_scope_filter(self, session: SessionPayload, permission_key: str):
        """构造职位数据范围过滤条件。"""
        return await build_data_scope_filter(
            self.db,
            session,
            permission_key,
            owner_column=SysPosition.created_by,
            dept_column=SysPosition.owner_dept_id,
        )

    async def _ensure_positions_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        position_ids: list[str],
    ) -> None:
        """校验目标职位均在当前数据范围内，否则抛授权错误。"""
        unique_ids = list(dict.fromkeys(position_ids))
        if not unique_ids:
            return
        data_scope_filter = await self._position_scope_filter(session, permission_key)
        if await self.repo.count_positions_in_scope(unique_ids, data_scope_filter) != len(
            unique_ids
        ):
            raise AuthorizationError("Position is outside current data scope")

    async def _ensure_depts_visible(
        self,
        session: SessionPayload,
        permission_key: str,
        dept_ids: list[str],
    ) -> None:
        """校验目标部门均在当前可见部门集合内，否则抛授权错误。"""
        unique_ids = list(dict.fromkeys(dept_ids))
        if not unique_ids:
            return
        visible_dept_ids = await resolve_data_scope_dept_ids(self.db, session, permission_key)
        if visible_dept_ids is None:
            return
        allowed_ids = set(visible_dept_ids)
        if any(dept_id not in allowed_ids for dept_id in unique_ids):
            raise AuthorizationError("Dept is outside current data scope")
