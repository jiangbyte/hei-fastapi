""" Author: Charlie """

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.business import NotFoundError
from app.modules.sys.audit.model import SysOperationAuditLog
from app.modules.sys.audit.schema import OperationAuditCreate, OperationAuditPageQuery


class OperationAuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: OperationAuditCreate) -> SysOperationAuditLog:
        entity = SysOperationAuditLog(**payload.model_dump())
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_required(self, audit_id: str) -> SysOperationAuditLog:
        entity = await self.db.get(SysOperationAuditLog, audit_id)
        if entity is None:
            raise NotFoundError("Operation audit log not found")
        return entity

    async def page_admin(
        self,
        query: OperationAuditPageQuery,
    ) -> tuple[list[SysOperationAuditLog], int]:
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
