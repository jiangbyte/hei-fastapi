""" Author: Charlie

内部健康检查路由：存活探针与聚合各依赖可用性的就绪探针。
"""

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.core.config.settings import settings
from app.core.schema.health import (
    HealthCheckItem,
    LiveHealthResponse,
    ReadyChecksResponse,
    ReadyHealthResponse,
)
from app.platform.cache.redis import get_redis
from app.platform.config.sync import get_config_sync_state
from app.platform.db.session import get_session_factory
from app.platform.storage.manager import get_storage
from app.platform.tasks.snailjob_client import probe_snailjob_server

router = APIRouter()


@router.get("/v1/internal/health/live", response_model=LiveHealthResponse)
async def live() -> LiveHealthResponse:
    """存活探针，仅表示应用进程仍在运行。"""
    return LiveHealthResponse(status="live")


@router.get("/v1/internal/health/ready", response_model=ReadyHealthResponse)
async def ready(response: Response) -> ReadyHealthResponse:
    """就绪探针，聚合数据库、Redis、消息队列和存储配置的可用性检查。"""
    snail_configured = bool(settings.snail_job.server_host)
    checks = ReadyChecksResponse(
        database=HealthCheckItem(enabled=True, ok=False, detail=None),
        redis=HealthCheckItem(enabled=True, ok=False, detail=None),
        config_sync=HealthCheckItem(enabled=False, ok=False, detail=None),
        # API 进程不依赖 SnailJob Server 才可服务；配置齐全即视为 ok，探活写入 detail。
        snail_job=HealthCheckItem(
            enabled=snail_configured,
            ok=snail_configured,
            detail=None,
        ),
        storage=HealthCheckItem(enabled=True, ok=False, detail=None),
    )
    try:
        async with get_session_factory()() as session:
            await session.execute(text("SELECT 1"))
        checks.database.ok = True
        checks.database.detail = "connection ok"
    except Exception as exc:
        checks.database.detail = _safe_detail(exc)
    redis = get_redis()
    if redis is None:
        checks.redis.detail = "redis not initialized"
    else:
        try:
            await redis.ping()
            checks.redis.ok = True
            checks.redis.detail = "connection ok"
        except Exception as exc:
            checks.redis.detail = _safe_detail(exc)
    sync_state = get_config_sync_state()
    checks.config_sync.enabled = sync_state.enabled
    checks.config_sync.ok = not sync_state.enabled or sync_state.running
    checks.config_sync.detail = (
        f"channel={sync_state.channel}, last_event_at={sync_state.last_event_at}"
        if sync_state.running
        else sync_state.last_error or "listener not running"
    )
    if not checks.snail_job.enabled:
        checks.snail_job.detail = "snailjob server host not configured"
    else:
        reachable, probe_detail = probe_snailjob_server()
        checks.snail_job.detail = probe_detail if reachable else f"configured; {probe_detail}"
    try:
        storage = get_storage()
        checks.storage.ok = True
        checks.storage.detail = f"{storage.__class__.__name__} configured"
    except Exception as exc:
        checks.storage.detail = _safe_detail(exc)
    overall = all(
        component.ok
        for component in [
            checks.database,
            checks.redis,
            checks.config_sync,
            checks.snail_job,
            checks.storage,
        ]
        if component.enabled
    )
    if not overall:
        response.status_code = 503
    return ReadyHealthResponse(
        status="ready" if overall else "not_ready",
        checks=checks,
    )


def _safe_detail(exc: Exception) -> str:
    """按调试开关决定异常详情：调试返回完整信息，否则仅返回类型名。"""
    if settings.app.debug:
        return str(exc)
    return exc.__class__.__name__
