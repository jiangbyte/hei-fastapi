""" Author: Charlie

展示图周期任务：交互增量刷库 + 按 start_at/end_at 同步状态。
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from snailjob import ExecuteResult, ExecutorManager, JobArgs, SnailLog, job
from sqlalchemy import or_, update

from app.core.config.enums import StatusEnum
from app.modules.sys.banner.model import SysBanner
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
        SnailLog.REMOTE.info(f"bannerFlushInteractions count={count}")
        return ExecuteResult.success(count)
    except Exception as exc:
        logger.exception("Flush banner interactions failed")
        SnailLog.REMOTE.error(str(exc))
        return ExecuteResult.failure(str(exc))


@job("bannerStatusJob")
def sync_banner_status(_args: JobArgs) -> ExecuteResult:
    """按 start_at / end_at 激活或过期 Banner（对齐 hei-boot bannerStatusJob）。"""
    try:
        result = worker_async_runner.run(_sync_banner_status())
        SnailLog.REMOTE.info(
            f"Banner status sync: expired={result['expired']}, activated={result['activated']}"
        )
        return ExecuteResult.success(result)
    except Exception as exc:
        logger.exception("Banner status sync failed")
        SnailLog.REMOTE.error(str(exc))
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


async def _sync_banner_status() -> dict[str, int]:
    """过期 ENABLED → DISABLED；到点且未过期的 DISABLED → ENABLED。"""
    init_engine()
    now = datetime.now(UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        expired_result = await session.execute(
            update(SysBanner)
            .where(
                SysBanner.status == StatusEnum.ENABLED.value,
                SysBanner.end_at.is_not(None),
                SysBanner.end_at < now,
            )
            .values(status=StatusEnum.DISABLED.value, updated_at=now)
        )
        activated_result = await session.execute(
            update(SysBanner)
            .where(
                SysBanner.status == StatusEnum.DISABLED.value,
                SysBanner.start_at.is_not(None),
                SysBanner.start_at <= now,
                or_(SysBanner.end_at.is_(None), SysBanner.end_at >= now),
            )
            .values(status=StatusEnum.ENABLED.value, updated_at=now)
        )
        await session.commit()
        expired = expired_result.rowcount or 0
        activated = activated_result.rowcount or 0
        logger.info("Banner status sync expired=%s activated=%s", expired, activated)
        return {"expired": expired, "activated": activated}


ExecutorManager.register(flush_banner_interactions)
ExecutorManager.register(sync_banner_status)
