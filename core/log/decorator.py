import functools
import json
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import Request

from core.db import SessionLocal
from core.utils import get_client_ip, get_city_info, generate_id
from core.utils.trace_utils import get_trace_id
from .utils import parse_user_agent, extract_params_json, get_result_json, generate_log_signature

logger = logging.getLogger(__name__)


def _get_request(*args, **kwargs) -> Optional[Request]:
    request = kwargs.get('request')
    if request:
        return request
    for arg in args:
        if isinstance(arg, Request):
            return arg
    return None


async def _get_op_user(request: Request) -> Optional[str]:
    """Get the current operator's username from the active user."""
    try:
        from core.auth import HeiAuthTool
        user_id = await HeiAuthTool.getLoginIdDefaultNull(request)
        if not user_id:
            return None

        from modules.sys.user.service import UserService
        from core.db import SessionLocal
        db = SessionLocal()
        try:
            entity = UserService(db).find_by_id(user_id)
            return entity.username if entity else None
        finally:
            db.close()
    except Exception:
        return None


def sys_log(name: str = "未命名"):
    """
    Decorator to record operation log on route handlers.
    Logs both success (OPERATE) and exception (EXCEPTION) outcomes.

    Usage:
        @router.get("/api/v1/sys/xxx")
        @SysLog("日志名称")
        @HeiCheckPermission("sys:xxx:page")
        async def handler(request: Request, ...):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = _get_request(*args, **kwargs)
            if not request:
                return await func(*args, **kwargs)

            start_time = datetime.now()
            params_json = extract_params_json(request, kwargs)

            try:
                result = await func(*args, **kwargs)
                await _save_log(
                    request=request,
                    func=func,
                    name=name,
                    category="OPERATE",
                    exe_status="SUCCESS",
                    exe_message=None,
                    params_json=params_json,
                    result_json=get_result_json(result),
                    start_time=start_time,
                )
                return result
            except Exception as e:
                await _save_log(
                    request=request,
                    func=func,
                    name=name,
                    category="EXCEPTION",
                    exe_status="FAIL",
                    exe_message=str(e)[:2000],
                    params_json=params_json,
                    result_json=None,
                    start_time=start_time,
                )
                request.state._exception_logged = True
                raise
        return wrapper
    return decorator


async def _save_log(request: Request, func, name: str, category: str,
              exe_status: str, exe_message: Optional[str],
              params_json: str, result_json: Optional[str],
              start_time: datetime) -> None:
    """Persist the log entry to database."""
    from modules.sys.log.service import LogService
    from modules.sys.log.models import SysLog as LogModel
    db = SessionLocal()
    try:
        now = datetime.now()
        user_agent = request.headers.get("user-agent", "")
        browser, os_name = parse_user_agent(user_agent)
        op_user = await _get_op_user(request)

        op_ip = get_client_ip(request)
        entry = LogModel(
            id=generate_id(),
            category=category,
            name=name,
            exe_status=exe_status,
            exe_message=exe_message,
            trace_id=get_trace_id(),
            op_ip=op_ip,
            op_address=get_city_info(op_ip),
            op_browser=browser,
            op_os=os_name,
            class_name=func.__module__,
            method_name=func.__qualname__,
            req_method=request.method,
            req_url=str(request.url),
            param_json=params_json,
            result_json=result_json,
            op_time=start_time,
            op_user=op_user,
            sign_data="",
        )

        sign_data = generate_log_signature({
            "category": category,
            "name": name,
            "exe_status": exe_status,
            "op_ip": entry.op_ip,
            "op_time": start_time.isoformat(),
            "op_user": op_user,
            "trace_id": entry.trace_id,
        })
        entry.sign_data = sign_data

        service = LogService(db)
        service.dao.insert(entry)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to save operation log: {e}")
        db.rollback()
    finally:
        db.close()


async def save_exception_log(request: Request, exc: Exception, name: Optional[str] = None) -> None:
    """Save an unhandled exception to the database (sys_log table).

    Designed to be called from global exception handlers so that ALL
    exceptions are recorded in the database, even for handlers without
    the @SysLog decorator.  Creates its own DB session so it is
    independent of the request's transaction.
    """
    from modules.sys.log.service import LogService
    from modules.sys.log.models import SysLog as LogModel
    db = SessionLocal()
    try:
        now = datetime.now()
        user_agent = request.headers.get("user-agent", "")
        browser, os_name = parse_user_agent(user_agent)
        op_user = await _get_op_user(request)
        op_ip = get_client_ip(request)
        log_name = name or f"{request.method} {request.url.path}"

        entry = LogModel(
            id=generate_id(),
            category="EXCEPTION",
            name=log_name,
            exe_status="FAIL",
            exe_message=str(exc)[:2000],
            trace_id=get_trace_id(),
            op_ip=op_ip,
            op_address=get_city_info(op_ip),
            op_browser=browser,
            op_os=os_name,
            class_name=type(exc).__module__,
            method_name=type(exc).__qualname__,
            req_method=request.method,
            req_url=str(request.url),
            param_json="",
            result_json=None,
            op_time=now,
            op_user=op_user,
            sign_data="",
        )

        sign_data = generate_log_signature({
            "category": "EXCEPTION",
            "name": log_name,
            "exe_status": "FAIL",
            "op_ip": entry.op_ip,
            "op_time": now.isoformat(),
            "op_user": op_user,
            "trace_id": entry.trace_id,
        })
        entry.sign_data = sign_data

        service = LogService(db)
        service.dao.insert(entry)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to save exception log: {e}")
        db.rollback()
    finally:
        db.close()


def record_auth_log(request: Request, name: str, category: str,
                    exe_status: str = "SUCCESS",
                    exe_message: Optional[str] = None,
                    op_user: Optional[str] = None) -> None:
    """Public API for recording auth-related logs (login/logout) programmatically.

    Unlike the ``@sys_log`` decorator, this does NOT need a function context
    and accepts the operator name directly — which is essential for login
    events where there is no active auth token yet.
    """
    from modules.sys.log.service import LogService
    from modules.sys.log.models import SysLog as LogModel
    db = SessionLocal()
    try:
        now = datetime.now()
        user_agent = request.headers.get("user-agent", "")
        browser, os_name = parse_user_agent(user_agent)
        op_ip = get_client_ip(request)
        entry = LogModel(
            id=generate_id(),
            category=category,
            name=name,
            exe_status=exe_status,
            exe_message=exe_message,
            trace_id=get_trace_id(),
            op_ip=op_ip,
            op_address=get_city_info(op_ip),
            op_browser=browser,
            op_os=os_name,
            class_name="",
            method_name="",
            req_method=request.method,
            req_url=str(request.url),
            param_json="",
            result_json=None,
            op_time=now,
            op_user=op_user,
            sign_data="",
        )
        sign_data = generate_log_signature({
            "category": category, "name": name, "exe_status": exe_status,
            "op_ip": entry.op_ip, "op_time": now.isoformat(),
            "op_user": op_user, "trace_id": entry.trace_id,
        })
        entry.sign_data = sign_data
        service = LogService(db)
        service.dao.insert(entry)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to save auth log: {e}")
        db.rollback()
    finally:
        db.close()
