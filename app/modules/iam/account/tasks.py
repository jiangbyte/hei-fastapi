""" Author: Charlie

账户定时任务：清理已注销且超过保留期的账户数据。
"""

import logging

from snailjob import ExecuteResult, ExecutorManager, JobArgs, SnailLog, job

from app.core.cache.redis import init_redis
from app.core.db.session import get_session_factory, init_engine
from app.core.tasks.async_runner import worker_async_runner
from app.modules.iam.account.service import AccountService

logger = logging.getLogger(__name__)


def _parse_retention_days(job_params: object) -> int | None:
    """从 SnailJob args 解析保留天数；无效则返回 None 走服务默认。"""
    if job_params is None or job_params == "":
        return None
    try:
        return int(str(job_params).strip())
    except (TypeError, ValueError):
        logger.warning("Invalid retention_days job_params=%r; using service default", job_params)
        return None


@job("accountPurgeCancelledAccounts")
def purge_cancelled_accounts(args: JobArgs) -> ExecuteResult:
    """SnailJob 入口：清理过期注销账户（可用 job_params 传 retention_days）。"""
    try:
        retention_days = _parse_retention_days(args.job_params)
        count = worker_async_runner.run(_purge_cancelled_accounts(retention_days=retention_days))
        SnailLog.REMOTE.info(f"accountPurgeCancelledAccounts count={count}")
        return ExecuteResult.success(count)
    except Exception as exc:
        logger.exception("Purge cancelled accounts failed")
        SnailLog.REMOTE.error(str(exc))
        return ExecuteResult.failure(str(exc))


async def _purge_cancelled_accounts(*, retention_days: int | None) -> int:
    """初始化引擎与 Redis 后执行过期注销账户清理。"""
    init_engine()
    await init_redis()
    session_factory = get_session_factory()
    async with session_factory() as session:
        count = await AccountService(session).purge_expired_cancelled_accounts(
            retention_days=retention_days
        )
        logger.info("Purged expired cancelled accounts", extra={"count": count})
        return count


ExecutorManager.register(purge_cancelled_accounts)
