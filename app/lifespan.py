""" Author: Charlie

应用生命周期：启动/关闭时初始化与清理各平台组件。
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.audit.queue import start_operation_audit_queue, stop_operation_audit_queue
from app.core.cache.redis import close_redis, init_redis
from app.core.config.apply import apply_all_config
from app.core.config.reader import config_reader
from app.core.config.sync import start_config_sync_listener, stop_config_sync_listener
from app.core.db.session import close_engine, init_engine
from app.core.events import emit
from app.core.http.client import close_http_client, init_http_client
from app.core.observability.tracing import shutdown_tracing
from app.core.secrets.validate import validate_secrets_config
from app.core.security.auth_whitelist import get_auth_whitelist_patterns
from app.core.security.permission_registry import sync_permission_registry
from app.core.tasks.snailjob_client import start_executor, stop_executor

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期：启动初始化各组件，关闭时依次清理。"""
    logger.info("lifespan startup: app.routes count = %d", len(app.routes))

    init_engine()
    await init_redis()
    validate_secrets_config()
    await start_operation_audit_queue()

    await config_reader.load_all()
    apply_all_config()
    await start_config_sync_listener()

    get_auth_whitelist_patterns()
    await sync_permission_registry(app)
    await init_http_client()

    # 内嵌 SnailJob 执行器（单进程模型，后台线程）。
    start_executor()

    await emit("on_db_ready")

    try:
        yield
    finally:
        stop_executor()
        await stop_config_sync_listener()
        await stop_operation_audit_queue()
        await close_http_client()
        await close_redis()
        await close_engine()
        shutdown_tracing()
