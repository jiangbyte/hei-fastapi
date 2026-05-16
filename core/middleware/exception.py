import logging
from fastapi import Request, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from core.exception import BusinessException
from core.result import failure
from core.log import save_exception_log

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        logger.warning(f"Business exception: {exc.message}")
        if not getattr(request.state, '_exception_logged', False):
            await save_exception_log(request, exc, name=exc.message)
        return JSONResponse(
            status_code=200,
            content=failure(message=exc.message, code=exc.code)
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTP exception {exc.status_code}: {exc.detail}")
        if not getattr(request.state, '_exception_logged', False):
            await save_exception_log(request, exc, name=f"HTTP {exc.status_code}")
        return JSONResponse(
            status_code=exc.status_code,
            content=failure(message=exc.detail, code=exc.status_code)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        logger.error(f"Validation error for {request.method} {request.url.path}: {errors}")
        if not getattr(request.state, '_exception_logged', False):
            await save_exception_log(request, exc, name="请求参数校验失败")
        if errors:
            message = errors[0].get("msg", "请求参数格式错误")
        else:
            message = "请求参数格式错误"
        return JSONResponse(
            status_code=200,
            content=failure(message=message, code=400)
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global exception: {exc}", exc_info=True)
        if not getattr(request.state, '_exception_logged', False):
            await save_exception_log(request, exc)
        return JSONResponse(
            status_code=200,
            content=failure(message="服务器内部错误", code=500)
        )
