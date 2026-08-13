""" Author: Charlie

框架事件总线 — 模块订阅生命周期事件，框架 emit。

预定义事件:
  - on_config_loaded(config_reader)     -- sys_config 加载完成后
  - on_storage_configured               -- 存储配置应用后
  - on_db_ready                         -- 数据库就绪后
  - on_permissions_synced(app)          -- 权限同步完成后
"""
from __future__ import annotations

import inspect
import logging
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger(__name__)

# 事件处理器类型：返回协程或 None 的可调用对象。
EventHandler = Callable[..., Coroutine[Any, Any, None] | None]

# 事件名到订阅处理器列表的注册表。
_subscribers: dict[str, list[EventHandler]] = {}


def subscribe(event_name: str, handler: EventHandler) -> None:
    """订阅事件：将处理器追加到该事件的处理器列表。"""
    _subscribers.setdefault(event_name, []).append(handler)


async def emit(event_name: str, **kwargs: Any) -> None:
    """异步发布事件，逐个调用并等待协程处理器，异常仅记录不抛出。"""
    for handler in _subscribers.get(event_name, []):
        try:
            result = handler(**kwargs)
            if inspect.isawaitable(result):
                await result
        except Exception:
            logger.exception("Error in event handler %s for event %s", handler, event_name)


def emit_sync(event_name: str, **kwargs: Any) -> None:
    """同步发布事件；协程处理器不会被等待，仅告警。"""
    for handler in _subscribers.get(event_name, []):
        try:
            result = handler(**kwargs)
            if inspect.iscoroutine(result):
                logger.warning(
                    "Sync emit %s called async handler %s; result not awaited",
                    event_name,
                    handler,
                )
        except Exception:
            logger.exception("Error in event handler %s for event %s", handler, event_name)
