""" Author: Charlie """

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
from app.platform.tasks.celery_app import celery_app

router = APIRouter()


@router.get("/v1/internal/health/live", response_model=LiveHealthResponse)
async def live() -> LiveHealthResponse:
    """存活探针，仅表示应用进程仍在运行。"""
    return LiveHealthResponse(status="live")


@router.get("/v1/internal/health/ready", response_model=ReadyHealthResponse)
async def ready(response: Response) -> ReadyHealthResponse:
    """就绪探针，聚合数据库、Redis、消息队列和存储配置的可用性检查。"""
    checks = ReadyChecksResponse(
        database=HealthCheckItem(enabled=True, ok=False, detail=None),
        redis=HealthCheckItem(enabled=True, ok=False, detail=None),
        config_sync=HealthCheckItem(enabled=False, ok=False, detail=None),
        celery_broker=HealthCheckItem(
            enabled=bool(settings.celery.broker_url),
            ok=False,
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
    if not checks.celery_broker.enabled:
        checks.celery_broker.detail = "celery broker not configured"
    else:
        try:
            connection = celery_app.connection_for_read()
            with connection.ensure_connection(max_retries=1):
                pass
            checks.celery_broker.ok = True
            checks.celery_broker.detail = "connection ok"
        except Exception as exc:
            checks.celery_broker.detail = _safe_detail(exc)
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
            checks.celery_broker,
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
    if settings.app.debug:
        return str(exc)
    return exc.__class__.__name__
