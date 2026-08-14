""" Author: Charlie

操作审计服务层：统一构造审计载荷并落库，同时上报可观测指标。
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.transaction import transactional
from app.core.observability.context import (
    account_id_ctx,
    account_type_ctx,
    client_ip_ctx,
    request_id_ctx,
    user_agent_ctx,
)
from app.core.observability.metrics import record_operation_audit
from app.core.response.pagination import PageData, build_page
from app.core.schema.base import IdQuery, to_schema, to_schema_list
from app.core.security.masking import mask_identifier
from app.modules.sys.audit.repository import OperationAuditRepository
from app.modules.sys.audit.schema import (
    OperationAuditCreate,
    OperationAuditPageQuery,
    OperationAuditRecord,
)

logger = logging.getLogger(__name__)


class OperationAuditService:
    """操作审计服务，负责审计记录的脱敏、持久化与查询。"""

    def __init__(self, db: AsyncSession) -> None:
        """绑定会话并初始化仓储。"""
        self.db = db
        self.repo = OperationAuditRepository(db)

    async def record(
        self,
        *,
        module: str,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        summary: str | None = None,
        before_data: dict | None = None,
        after_data: dict | None = None,
        success: bool = True,
        error_message: str | None = None,
        account_id: str | None = None,
        account_type: str | None = None,
        request_id: str | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """构造并写入一条审计日志；参数未显式提供时回退到请求上下文。"""
        payload = OperationAuditCreate(
            module=module,
            resource_type=resource_type,
            # 对资源 ID 与摘要脱敏后再落库，避免日志泄漏敏感标识。
            resource_id=mask_identifier(resource_id) if resource_id else None,
            action=action,
            summary=mask_identifier(summary) if summary else None,
            before_data=before_data,
            after_data=after_data,
            account_id=account_id if account_id is not None else account_id_ctx.get(),
            account_type=account_type if account_type is not None else account_type_ctx.get(),
            request_id=request_id if request_id is not None else request_id_ctx.get(),
            ip=ip if ip is not None else client_ip_ctx.get(),
            user_agent=user_agent if user_agent is not None else user_agent_ctx.get(),
            success=success,
            error_message=error_message,
        )
        try:
            async with transactional(self.db):
                await self.repo.create(payload)
            record_operation_audit(module, action, success)
        except Exception:
            logger.exception("Failed to write operation audit log")

    async def detail(self, query: IdQuery) -> OperationAuditRecord:
        """按主键查询单条审计日志详情。"""
        return to_schema(OperationAuditRecord, await self.repo.get_required(query.id))

    async def page_admin(self, query: OperationAuditPageQuery) -> PageData[OperationAuditRecord]:
        """后台分页查询审计日志。"""
        items, total = await self.repo.page_admin(query)
        return build_page(
            query,
            total,
            to_schema_list(OperationAuditRecord, items),
        )
