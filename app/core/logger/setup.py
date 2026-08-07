""" Author: Charlie """

from __future__ import annotations

import logging
from pathlib import Path

from app.core.config.settings import settings
from app.platform.observability.logging import build_log_formatter

_CONFIGURED = False
_NOISY_LOGGERS = (
    "uvicorn.access",
    "gunicorn.access",
)


def setup_logging(*, force: bool = False) -> None:
    """为 API 与 worker 进程一次性配置根日志（structlog + stdlib）。"""
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    root = logging.getLogger()
    if not settings.observability.log_enabled:
        root.handlers.clear()
        root.addHandler(logging.NullHandler())
        root.setLevel(logging.CRITICAL + 1)
        _CONFIGURED = True
        return

    formatter = build_log_formatter()
    level = getattr(logging, settings.observability.log_level.upper(), logging.INFO)

    root.handlers.clear()

    stdout = logging.StreamHandler()
    stdout.setFormatter(formatter)
    root.addHandler(stdout)

    log_dir = (settings.observability.log_dir or "").strip()
    if log_dir:
        path = Path(log_dir)
        if not path.is_absolute():
            path = Path.cwd() / path
        try:
            from app.core.logger.file_handler import DailyFileHandler

            file_handler = DailyFileHandler(str(path))
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except Exception:
            logging.getLogger(__name__).exception("Failed to initialize file logging")

    root.setLevel(level)
    _quiet_noisy_loggers()
    _CONFIGURED = True


def _quiet_noisy_loggers() -> None:
    """优先使用应用访问日志，抑制框架访问日志。"""
    for name in _NOISY_LOGGERS:
        noisy = logging.getLogger(name)
        noisy.handlers.clear()
        noisy.propagate = False
        noisy.disabled = True
