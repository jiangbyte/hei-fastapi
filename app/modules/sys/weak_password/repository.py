""" Author: Charlie

弱密码库仓储层：封装弱密码的持久化、去重校验与查询。
"""

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import ConflictError, NotFoundError
from app.modules.sys.weak_password.schema import (
    WeakPasswordAdminPageQuery,
    WeakPasswordCreateRequest,
    WeakPasswordListQuery,
    WeakPasswordUpdateRequest,
)
from app.platform.db.models.sys_weak_password import SysWeakPassword


class WeakPasswordRepository:
    """弱密码库仓储。"""

    def __init__(self, db: AsyncSession):
        """绑定数据库会话。"""
        self.db = db

    async def create(self, payload: WeakPasswordCreateRequest) -> None:
        """校验密码唯一后新增弱密码。"""
        await self._ensure_unique(payload.password)
        self.db.add(SysWeakPassword(password=payload.password))
        await self.db.flush()

    async def get_by_id(self, row_id: str) -> SysWeakPassword | None:
        """按主键查询，不存在返回 None。"""
        return await self.db.get(SysWeakPassword, row_id)

    async def get_required(self, row_id: str) -> SysWeakPassword:
        """按主键查询，不存在时抛出 NotFoundError。"""
        entity = await self.get_by_id(row_id)
        if entity is None:
            raise NotFoundError("Weak password not found")
        return entity

    async def update(self, payload: WeakPasswordUpdateRequest) -> None:
        """校验密码唯一后更新弱密码。"""
        entity = await self.get_required(payload.id)
        await self._ensure_unique(payload.password, exclude_id=payload.id)
        entity.password = payload.password
        await self.db.flush()

    async def delete_many(self, row_ids: list[str]) -> None:
        """批量删除；存在不存在的 ID 时抛出 NotFoundError。"""
        unique_ids = list(dict.fromkeys(row_ids))
        stmt = select(SysWeakPassword.id).where(SysWeakPassword.id.in_(unique_ids))
        existing_ids = set((await self.db.execute(stmt)).scalars().all())
        if len(existing_ids) != len(unique_ids):
            raise NotFoundError("Weak password not found")
        await self.db.execute(delete(SysWeakPassword).where(SysWeakPassword.id.in_(unique_ids)))

    async def page_admin(
        self, query: WeakPasswordAdminPageQuery
    ) -> tuple[list[SysWeakPassword], int]:
        """按密码模糊匹配后台分页，返回记录列表与总数。"""
        stmt: Select[tuple[SysWeakPassword]] = select(SysWeakPassword)
        count_stmt = select(func.count(SysWeakPassword.id))
        if query.password:
            like = f"%{query.password}%"
            stmt = stmt.where(SysWeakPassword.password.ilike(like))
            count_stmt = count_stmt.where(SysWeakPassword.password.ilike(like))
        stmt = (
            stmt.order_by(SysWeakPassword.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = (await self.db.execute(count_stmt)).scalar_one()
        return items, total

    async def list_all(self, query: WeakPasswordListQuery) -> list[SysWeakPassword]:
        """按密码模糊匹配列出全部弱密码。"""
        stmt = select(SysWeakPassword).order_by(SysWeakPassword.id.desc())
        if query.password:
            stmt = stmt.where(SysWeakPassword.password.ilike(f"%{query.password}%"))
        return list((await self.db.execute(stmt)).scalars().all())

    async def exists_password(self, password: str) -> bool:
        """判断指定密码是否已存在于弱密码库。"""
        stmt = select(SysWeakPassword.id).where(SysWeakPassword.password == password).limit(1)
        return (await self.db.execute(stmt)).scalar_one_or_none() is not None

    async def _ensure_unique(self, password: str, *, exclude_id: str | None = None) -> None:
        """校验密码唯一（排除自身），重复时抛出 ConflictError。"""
        stmt = select(SysWeakPassword.id).where(SysWeakPassword.password == password)
        if exclude_id:
            stmt = stmt.where(SysWeakPassword.id != exclude_id)
        if (await self.db.execute(stmt)).scalar_one_or_none() is not None:
            raise ConflictError("Weak password already exists")
