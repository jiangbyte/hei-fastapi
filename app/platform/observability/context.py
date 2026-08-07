""" Author: Charlie

请求级日志上下文辅助（stdlib ContextVar + structlog）。
"""
from __future__ import annotations

import structlog


def bind_request_log_context(**values: object) -> None:
    """将字段绑定到当前请求/任务的 structlog contextvars。"""
    cleaned = {key: value for key, value in values.items() if value not in (None, "")}
    if cleaned:
        structlog.contextvars.bind_contextvars(**cleaned)


def clear_request_log_context() -> None:
    structlog.contextvars.clear_contextvars()
