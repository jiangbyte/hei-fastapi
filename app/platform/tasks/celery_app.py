""" Author: Charlie """

import logging

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from app.core.config.settings import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "hei-fastapi",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend or settings.redis.url,
    include=["app.worker.tasks"],
)
celery_app.conf.task_default_queue = "default"
celery_app.conf.worker_enable_remote_control = settings.celery.worker_remote_control_enabled
celery_app.conf.worker_cancel_long_running_tasks_on_connection_loss = (
    settings.celery.worker_cancel_long_running_tasks_on_connection_loss
)
# Redis broker：visibility_timeout 必须大于最长任务墙钟时间，否则任务运行中会重投递。
# 不要放入 redbeat_redis_options —— redis-py 不接受 visibility_timeout。
celery_app.conf.broker_transport_options = {
    "visibility_timeout": settings.celery.broker_visibility_timeout,
}
celery_app.conf.broker_connection_retry_on_startup = True
celery_app.conf.task_acks_late = True
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.task_compression = "gzip"
celery_app.conf.result_expires = settings.celery.broker_visibility_timeout
celery_app.conf.redbeat_redis_url = settings.redis.url
# 显式选项，避免 RedBeat 继承 broker_transport_options。
celery_app.conf.redbeat_redis_options = {"decode_responses": True}
celery_app.conf.redbeat_lock_key = "redbeat:lock"

from app.platform.tasks.redbeat_scheduler import sync_to_redbeat  # noqa: E402

sync_to_redbeat(celery_app)


@worker_process_init.connect
def _worker_process_init(**_: object) -> None:
    # 必须与 WorkerAsyncRunner 共用同一 loop：asyncio.run() 会把 Redis/DB
    # 连接绑定到临时 loop，任务执行前该 loop 已关闭。
    try:
        from app.core.logger.setup import setup_logging

        setup_logging()
        from app.platform.tasks.async_runner import worker_async_runner

        worker_async_runner.run(_startup_worker_infra())
    except Exception:
        logger.exception("Failed to initialize worker infrastructure")
        raise


@worker_process_shutdown.connect
def _worker_process_shutdown(**_: object) -> None:
    try:
        from app.platform.tasks.async_runner import worker_async_runner

        worker_async_runner.run(_shutdown_worker_infra())
        worker_async_runner.close()
    except Exception:
        logger.warning("Failed to shutdown worker infrastructure", exc_info=True)


async def _startup_worker_infra() -> None:
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


async def _shutdown_worker_infra() -> None:
    from app.platform.cache.redis import close_redis
    from app.platform.config.sync import stop_config_sync_listener_thread
    from app.platform.db.session import close_engine

    stop_config_sync_listener_thread()
    await close_redis()
    await close_engine()
