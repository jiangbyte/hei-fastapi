""" Author: Charlie

应用工厂：组装中间件、异常处理、可观测性与路由，创建 FastAPI 应用。
"""

import logging

from fastapi import FastAPI

from app.core.config.settings import settings
from app.core.exceptions.handlers import (
    customize_openapi_error_responses,
    register_exception_handlers,
)
from app.core.logger.setup import setup_logging
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
from app.platform.db.session import engine
from app.platform.module import load_module_specs
from app.platform.module.services import register_services
from app.platform.observability.manager import setup_observability

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用，组装中间件、路由与生命周期。"""
    setup_logging()

    # 延迟导入：确保 setup_logging() 先配置好，模块发现的日志才能正常输出
    from app.platform.module import get_api_router

    api_router = get_api_router()

    # 部分测试客户端与嵌入场景不会触发 ASGI lifespan。
    # 构造时也注册服务接口；启动阶段会再次注册。
    register_services(load_module_specs())

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
