""" Author: Charlie

账户定时任务：清理已注销且超过保留期的账户数据。
"""

import logging

from snailjob import ExecuteResult, ExecutorManager, JobArgs, job

from app.modules.iam.account.service import AccountService
from app.platform.cache.redis import init_redis
from app.platform.db.session import get_session_factory, init_engine
from app.platform.tasks.async_runner import worker_async_runner

logger = logging.getLogger(__name__)


@job("accountPurgeCancelledAccounts")
def purge_cancelled_accounts(_args: JobArgs) -> ExecuteResult:
    """SnailJob 入口：清理过期注销账户。"""
    try:
        count = worker_async_runner.run(_purge_cancelled_accounts())
        return ExecuteResult.success(count)
    except Exception as exc:
        logger.exception("Purge cancelled accounts failed")
        return ExecuteResult.failure(str(exc))


async def _purge_cancelled_accounts() -> int:
    """初始化引擎与 Redis 后执行过期注销账户清理。"""
    init_engine()
    await init_redis()
    session_factory = get_session_factory()
    async with session_factory() as session:
        count = await AccountService(session).purge_expired_cancelled_accounts()
        logger.info("Purged expired cancelled accounts", extra={"count": count})
        return count


ExecutorManager.register(purge_cancelled_accounts)
