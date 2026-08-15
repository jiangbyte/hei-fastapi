""" Author: Charlie

应用工厂：组装中间件、异常处理、可观测性与路由，创建 FastAPI 应用。
"""

import logging

from fastapi import FastAPI

from app.core.config.settings import settings
from app.core.db.session import engine
from app.core.exceptions.handlers import (
    customize_openapi_error_responses,
    register_auth_root_callable,
    register_exception_handlers,
)
from app.core.logger.setup import setup_logging
from app.core.observability.manager import setup_observability
from app.core.schema.health import RootHealthResponse
from app.lifespan import lifespan
from app.middleware.asgi_core import (
    AccessLogMiddleware,
    AuthContextMiddleware,
    TraceMiddleware,
)
from app.middleware.asgi_rest import (
    AuthWhitelistMiddleware,
    OperationAuditMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.middleware.cors import add_cors

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用，组装中间件、路由与生命周期。"""
    setup_logging()

    # 延迟导入：确保 setup_logging() 先配置好，模块发现的日志才能正常输出
    from app.routers import get_api_router

    api_router = get_api_router()

    # 平台层回调装配：OpenAPI 认证路由识别与审计 outbox（避免平台依赖业务包）。
    from app.core.audit.queue import register_outbox_handlers
    from app.deps import auth as auth_deps
    from app.modules.sys.audit.outbox import claim_pending_outbox, enqueue_outbox

    for root in (
        auth_deps.get_current_session,
        auth_deps.get_current_account,
        auth_deps.get_optional_session,
    ):
        register_auth_root_callable(root)
    register_outbox_handlers(enqueue_outbox, claim_pending_outbox)

    # 事件订阅。
    from app.modules.sys.audit.event_handler import register as register_audit_event_handler

    register_audit_event_handler()

    app = FastAPI(
        title=settings.app.name,
        debug=False,
        docs_url="/docs" if settings.swagger.enabled else None,
        redoc_url="/redoc" if settings.swagger.enabled else None,
        openapi_url="/openapi.json" if settings.swagger.enabled else None,
        lifespan=lifespan,
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(OperationAuditMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthWhitelistMiddleware)
    app.add_middleware(AuthContextMiddleware)
    # 最外层应用中间件（位于 CORS 之后）：保证 request_id 贯穿访问日志。
    app.add_middleware(TraceMiddleware)
    add_cors(app)
    register_exception_handlers(app)
    customize_openapi_error_responses(app)
    setup_observability(app, engine=engine)

    @app.get("/", tags=["health"], response_model=RootHealthResponse)
    async def root() -> RootHealthResponse:
        return RootHealthResponse(status="ok", service=settings.app.name)

    app.include_router(api_router)
    logger.info("Application created with %d routes", len(app.routes))

    return app
