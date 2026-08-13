""" Author: Charlie

展示图周期任务：定时将 Redis 交互增量刷入数据库。
"""

import logging

from snailjob import ExecuteResult, ExecutorManager, JobArgs, job

from app.modules.sys.banner.service import flush_interaction_deltas
from app.platform.cache.redis import get_redis, init_redis
from app.platform.db.session import get_session_factory, init_engine
from app.platform.tasks.async_runner import worker_async_runner

logger = logging.getLogger(__name__)


@job("bannerFlushInteractions")
def flush_banner_interactions(_args: JobArgs) -> ExecuteResult:
    """周期任务：将展示图交互增量刷入数据库。"""
    try:
        count = worker_async_runner.run(_flush_banner_interactions())
        return ExecuteResult.success(count)
    except Exception as exc:
        logger.exception("Flush banner interactions failed")
        return ExecuteResult.failure(str(exc))


async def _flush_banner_interactions() -> int:
    """初始化引擎与 Redis 后执行增量刷新，Redis 不可用时跳过。"""
    init_engine()
    await init_redis()
    redis = get_redis()
    if redis is None:
        logger.info("Skip display image interaction flush because Redis is unavailable")
        return 0
    session_factory = get_session_factory()
    async with session_factory() as session:
        return await flush_interaction_deltas(session, redis)


ExecutorManager.register(flush_banner_interactions)
