""" Author: Charlie

审计分析任务。
"""
import logging

from snailjob import ExecuteResult, ExecutorManager, JobArgs, job

from app.core.config.settings import settings
from app.modules.sys.audit.alert import alert_dispatcher
from app.modules.sys.audit.analyzer import audit_analyzer
from app.platform.db.session import get_session_factory
from app.platform.tasks.async_runner import worker_async_runner

logger = logging.getLogger(__name__)


@job("auditAnalysisCycle")
def audit_analysis_cycle(_args: JobArgs) -> ExecuteResult:
    """审计告警分析周期任务：分析 -> 分发，由 SnailJob 调度。"""
    if not settings.audit_alert.enabled:
        return ExecuteResult.success("audit alert disabled")
    try:
        # 必须走 worker 持久 loop；asyncio.run() 会与已绑定的 DB 连接冲突
        worker_async_runner.run(_run_analysis())
        return ExecuteResult.success()
    except Exception as exc:
        logger.exception("Audit analysis cycle failed")
        return ExecuteResult.failure(str(exc))


async def _run_analysis() -> None:
    """执行分析和分发。"""
    factory = get_session_factory()
    async with factory() as session:
        events = await audit_analyzer.analyze(session)
        if events:
            await alert_dispatcher.dispatch(session, events)
            await session.commit()
            logger.info("Audit alert: %d events dispatched", len(events))
        else:
            logger.debug("Audit analysis: no events")


ExecutorManager.register(audit_analysis_cycle)
