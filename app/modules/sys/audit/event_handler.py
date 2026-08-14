""" Author: Charlie

订阅 on_audit_event 事件，将审计事件持久化到 sys_operation_audit 表。
"""
import logging

from app.core.audit.queue import OperationAuditEvent
from app.core.db.session import get_session_factory
from app.core.events import subscribe

logger = logging.getLogger(__name__)


def _build_module(resource_type: str) -> str:
    """将资源类型映射为审计模块名（iam 资源归入 iam，其余归入 resource）。"""
    return "iam" if resource_type != "resources" else "resource"


async def _persist_audit_event(event: OperationAuditEvent) -> None:
    """将收到的审计事件写入 sys_operation_audit 表。"""
    from app.modules.sys.audit.service import OperationAuditService

    async with get_session_factory()() as session:
        await OperationAuditService(session).record(
            module=_build_module(event.resource_type),
            resource_type=event.resource_type,
            action=event.action,
            summary=f"{event.method} {event.path}",
            success=event.status_code < 400,
            error_message=None if event.status_code < 400 else str(event.status_code),
            account_id=event.account_id,
            account_type=event.account_type,
            request_id=event.request_id,
            ip=event.ip,
            user_agent=event.user_agent,
        )


def register() -> None:
    """订阅 on_audit_event 事件，触发审计事件持久化。"""
    subscribe("on_audit_event", _persist_audit_event)
