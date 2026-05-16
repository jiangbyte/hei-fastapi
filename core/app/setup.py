import logging

from fastapi import FastAPI

from config.settings import settings
from .lifespan import lifespan
from .router import setup_routers
from core.middleware import setup_cors, setup_exception_handlers, AuthMiddleware, TraceMiddleware
from core.log.utils import TraceIdFilter


def create_app() -> FastAPI:
    logging.getLogger().addFilter(TraceIdFilter())

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        lifespan=lifespan,
    )

    app.add_middleware(TraceMiddleware)
    app.add_middleware(AuthMiddleware)

    setup_cors(app)
    setup_exception_handlers(app)
    setup_routers(app)

    return app


app = create_app()
