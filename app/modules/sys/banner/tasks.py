""" Author: Charlie """

import logging

from app.modules.sys.banner.service import flush_interaction_deltas
from app.platform.cache.redis import get_redis, init_redis
from app.platform.db.session import get_session_factory, init_engine
from app.platform.tasks.async_runner import worker_async_runner
from app.platform.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="banner.flush_interactions")
def flush_banner_interactions() -> int:
    return worker_async_runner.run(_flush_banner_interactions())


async def _flush_banner_interactions() -> int:
    init_engine()
    await init_redis()
    redis = get_redis()
    if redis is None:
        logger.info("Skip display image interaction flush because Redis is unavailable")
        return 0
    session_factory = get_session_factory()
    async with session_factory() as session:
        return await flush_interaction_deltas(session, redis)
