""" Author: Charlie

弱密码库服务层：弱密码的维护与查询。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.modules.sys.weak_password.repository import WeakPasswordRepository
from app.modules.sys.weak_password.schema import (
    SysWeakPasswordSchema,
    WeakPasswordAdminPageQuery,
    WeakPasswordCreateRequest,
    WeakPasswordListQuery,
    WeakPasswordUpdateRequest,
)
from app.platform.db.transaction import transactional


class WeakPasswordService:
    """弱密码库管理服务。"""

    def __init__(self, db: AsyncSession):
        """绑定会话并初始化仓储。"""
        self.db = db
        self.repo = WeakPasswordRepository(db)

    async def create(self, payload: WeakPasswordCreateRequest) -> None:
        """事务内新增弱密码。"""
        async with transactional(self.db):
            await self.repo.create(payload)

    async def update(self, payload: WeakPasswordUpdateRequest) -> None:
        """事务内更新弱密码。"""
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        """事务内批量删除弱密码。"""
        async with transactional(self.db):
            await self.repo.delete_many(payload.ids)

    async def detail(self, query: IdQuery) -> SysWeakPasswordSchema:
        """查询弱密码详情。"""
        return to_schema(SysWeakPasswordSchema, await self.repo.get_required(query.id))

    async def page_admin(self, query: WeakPasswordAdminPageQuery) -> PageData[SysWeakPasswordSchema]:
        """分页查询弱密码。"""
        items, total = await self.repo.page_admin(query)
        return build_page(query, total, to_schema_list(SysWeakPasswordSchema, items))

    async def list_all(self, query: WeakPasswordListQuery) -> list[SysWeakPasswordSchema]:
        """列出全部弱密码。"""
        items = await self.repo.list_all(query)
        return to_schema_list(SysWeakPasswordSchema, items)
