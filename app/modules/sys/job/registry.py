""" Author: Charlie

任务处理器注册表：业务模块通过 @job_handler(key) 注册处理器，
调度引擎按 sys_job.handler 解析并执行（对齐 hei-boot common-job JobHandler SPI）。
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TypeAlias

logger = logging.getLogger(__name__)

# 处理器签名：接收 params（dict 或 None），返回结果摘要字符串。
JobHandlerType: TypeAlias = Callable[[dict | None], Awaitable[str]]

HANDLERS: dict[str, JobHandlerType] = {}

# hei-boot 种子数据使用 Java JobHandler 全限定类名；映射到 Python 注册 key。
BOOT_HANDLER_ALIASES: dict[str, str] = {
    "github.jiangbyte.io.sys.modules.job.sample.SysJobSample": "sys_job_sample",
    "github.jiangbyte.io.sys.modules.banner.job.BannerStatusJob": "sys_banner_status_sync",
    "github.jiangbyte.io.sys.modules.banner.job.BannerStatusSyncJob": "sys_banner_status_sync",
    "github.jiangbyte.io.sys.modules.banner.job.BannerFlushInteractionsJob": "sys_banner_flush_interactions",
    "github.jiangbyte.io.sys.modules.audit.job.AuditAlertJob": "sys_audit_alert",
    "github.jiangbyte.io.iam.modules.account.job.AccountPurgeCancelledJob": "iam_account_purge_cancelled",
    "github.jiangbyte.io.sys.modules.job.cleanup.SysJobLogCleanupJob": "sys_job_log_cleanup",
}

_handlers_loaded = False


def job_handler(name: str) -> Callable[[JobHandlerType], JobHandlerType]:
    """装饰器：按 key 注册任务处理器（重复注册直接覆盖并告警）。"""

    def decorator(func: JobHandlerType) -> JobHandlerType:
        if name in HANDLERS:
            logger.warning("job handler %r already registered, overwriting", name)
        HANDLERS[name] = func
        return func

    return decorator


def load_handlers() -> None:
    """显式导入业务处理器模块，触发 @job_handler 注册（幂等）。

    调度器启动时调用一次；resolve() 首次解析前也会兜底调用，
    保证手动立即执行在未启动调度器的场景下同样可用。
    """
    global _handlers_loaded
    if _handlers_loaded:
        return
    _handlers_loaded = True
    from app.modules.iam.account import tasks as _account_tasks  # noqa: F401
    from app.modules.sys.audit import tasks as _audit_tasks  # noqa: F401
    from app.modules.sys.banner import tasks as _banner_tasks  # noqa: F401
    from app.modules.sys.job import sample as _sample_tasks  # noqa: F401
    from app.modules.sys.job import tasks as _job_tasks  # noqa: F401


def resolve(name: str) -> JobHandlerType | None:
    """按标识解析处理器，未注册返回 None（首次调用前兜底加载处理器）。"""
    load_handlers()
    key = BOOT_HANDLER_ALIASES.get(name, name)
    return HANDLERS.get(key)


def boot_handler_display(handler: str) -> str:
    """API 回显对齐 hei-boot：注册 key 映射为 Java JobHandler 全限定类名。"""
    if handler in BOOT_HANDLER_ALIASES:
        return handler
    for fqcn, key in BOOT_HANDLER_ALIASES.items():
        if key == handler:
            return fqcn
    return handler
