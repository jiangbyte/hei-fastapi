""" Author: Charlie

审计分析任务：按配置规则扫描审计日志并分发告警。
"""
import logging

from app.core.config.settings import settings
from app.core.db.session import get_session_factory
from app.modules.sys.audit.alert import alert_dispatcher
from app.modules.sys.audit.analyzer import audit_analyzer
from app.modules.sys.job.registry import job_handler

logger = logging.getLogger(__name__)


@job_handler("sys_audit_alert")
async def audit_analysis_cycle(params: dict | None) -> str:
    """审计告警分析周期任务：分析 -> 分发。"""
    if not settings.audit_alert.enabled:
        logger.info("audit alert skipped: audit alert disabled")
        return "disabled"
    dispatched = await _run_analysis()
    return f"done dispatched={dispatched}"


async def _run_analysis() -> int:
    """执行分析和分发，返回分发事件数。"""
    factory = get_session_factory()
    async with factory() as session:
        events = await audit_analyzer.analyze(session)
        if events:
            await alert_dispatcher.dispatch(session, events)
            await session.commit()
            logger.info("Audit alert: %d events dispatched", len(events))
            return len(events)
        logger.debug("Audit analysis: no events")
        return 0
