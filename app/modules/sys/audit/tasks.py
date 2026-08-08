""" Author: Charlie

审计分析任务。
"""
import logging

from app.core.config.settings import settings
from app.modules.sys.audit.alert import alert_dispatcher
from app.modules.sys.audit.analyzer import audit_analyzer
from app.platform.db.session import get_session_factory
from app.platform.tasks.async_runner import worker_async_runner
from app.platform.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="audit.analysis_cycle", bind=True, max_retries=1, default_retry_delay=60)
def audit_analysis_cycle(self):
    """审计告警分析周期任务：分析 -> 分发，由 RedBeat 调度。"""
    if not settings.audit_alert.enabled:
        return
    try:
        # 必须走 worker 持久 loop；asyncio.run() 会与已绑定的 DB 连接冲突
        return worker_async_runner.run(_run_analysis())
    except Exception:
        logger.exception("Audit analysis cycle failed")
        raise self.retry() from None


async def _run_analysis():
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
