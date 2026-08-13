""" Author: Charlie

SnailJob Python 执行器：应用配置、加载模块任务并启动客户端主循环。
"""

from __future__ import annotations

import logging
import socket

from snailjob.config import configure_settings
from snailjob.main import client_main

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


def apply_snailjob_settings() -> None:
    """把应用 Settings 写入 snail-job-python 全局配置。"""
    sj = settings.snail_job
    configure_settings(
        snail_server_host=sj.server_host,
        snail_server_port=sj.server_port,
        snail_host_ip=sj.host_ip or "127.0.0.1",
        snail_host_port=sj.host_port,
        snail_namespace=sj.namespace,
        snail_group_name=sj.group_name,
        snail_token=sj.token,
        snail_labels=sj.labels,
    )


async def startup_worker_infra() -> None:
    """初始化 worker 基础设施：引擎、Redis、配置与同步监听。"""
    from app.platform.cache.redis import init_redis
    from app.platform.config.apply import apply_all_config
    from app.platform.config.reader import config_reader
    from app.platform.config.sync import start_config_sync_listener_thread
    from app.platform.db.session import init_engine

    init_engine()
    await init_redis()
    await config_reader.load_all()
    apply_all_config()
    start_config_sync_listener_thread()


async def shutdown_worker_infra() -> None:
    """优雅关闭 worker 基础设施：同步监听、Redis 与引擎。"""
    from app.platform.cache.redis import close_redis
    from app.platform.config.sync import stop_config_sync_listener_thread
    from app.platform.db.session import close_engine

    stop_config_sync_listener_thread()
    await close_redis()
    await close_engine()


def probe_snailjob_server(timeout_seconds: float = 2.0) -> tuple[bool, str]:
    """对 SnailJob Server 做 TCP 探活，返回 (reachable, detail)。"""
    host = settings.snail_job.server_host
    port = settings.snail_job.server_port
    if not host:
        return False, "snailjob server host not configured"
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True, f"tcp {host}:{port} ok"
    except OSError as exc:
        return False, f"tcp {host}:{port} failed: {exc.__class__.__name__}"


def run_executor() -> None:
    """启动 SnailJob 执行器：配置 → 基础设施 → 加载任务 → client_main。"""
    from app.core.logger.setup import setup_logging
    from app.platform.tasks.async_runner import worker_async_runner

    setup_logging()
    apply_snailjob_settings()
    worker_async_runner.run(startup_worker_infra())

    # 导入模块 tasks，触发 @job 装饰器与 ExecutorManager.register
    import app.worker.tasks  # noqa: F401

    logger.info(
        "SnailJob executor starting group=%s server=%s:%s client=%s:%s",
        settings.snail_job.group_name,
        settings.snail_job.server_host,
        settings.snail_job.server_port,
        settings.snail_job.host_ip,
        settings.snail_job.host_port,
    )
    try:
        client_main()
    finally:
        try:
            worker_async_runner.run(shutdown_worker_infra())
        except Exception:
            logger.warning("Failed to shutdown worker infrastructure", exc_info=True)
        worker_async_runner.close()
