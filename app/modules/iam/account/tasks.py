""" Author: Charlie """

import logging

from app.modules.iam.account.service import AccountService
from app.platform.cache.redis import init_redis
from app.platform.db.session import get_session_factory, init_engine
from app.platform.tasks.async_runner import worker_async_runner
from app.platform.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="account.purge_cancelled_accounts")
def purge_cancelled_accounts() -> int:
    return worker_async_runner.run(_purge_cancelled_accounts())


async def _purge_cancelled_accounts() -> int:
    init_engine()
    await init_redis()
    session_factory = get_session_factory()
    async with session_factory() as session:
        count = await AccountService(session).purge_expired_cancelled_accounts()
        logger.info("Purged expired cancelled accounts", extra={"count": count})
        return count
