""" Author: Charlie

操作审计日志仓储层：封装审计记录的持久化与后台分页查询。
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.sys.audit.model import SysOperationAuditLog
from app.modules.sys.audit.schema import OperationAuditCreate, OperationAuditPageQuery


class OperationAuditRepository:
    """操作审计日志仓储，提供创建、单条查询与后台分页。"""

    def __init__(self, db: AsyncSession) -> None:
        """绑定数据库会话。"""
        self.db = db

    async def create(self, payload: OperationAuditCreate) -> SysOperationAuditLog:
        """写入一条审计日志并 flush，返回持久化实体。"""
        entity = SysOperationAuditLog(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_required(self, audit_id: str) -> SysOperationAuditLog:
        """按主键查询审计日志，不存在时抛出 NotFoundError。"""
        entity = await self.db.get(SysOperationAuditLog, audit_id)
        if entity is None:
            raise NotFoundError("Operation audit log not found")
        return entity

    async def page_admin(
        self,
        query: OperationAuditPageQuery,
    ) -> tuple[list[SysOperationAuditLog], int]:
        """按查询条件后台分页，返回记录列表与总数。"""
        stmt = select(SysOperationAuditLog)
        count_stmt = select(func.count(SysOperationAuditLog.id))
        filters = []
        if query.module:
            filters.append(SysOperationAuditLog.module == query.module)
        if query.action:
            filters.append(SysOperationAuditLog.action == query.action)
        if query.account_id:
            filters.append(SysOperationAuditLog.account_id == query.account_id)
        if query.success is not None:
            filters.append(SysOperationAuditLog.success.is_(query.success))
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)
        stmt = (
            stmt.order_by(SysOperationAuditLog.created_at.desc(), SysOperationAuditLog.id.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        total = int((await self.db.execute(count_stmt)).scalar_one())
        return items, total
