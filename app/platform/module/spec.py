""" Author: Charlie """

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RouteSpec:
    """模块路由声明：全局挂 ``/api``；完整路径写在装饰器上。

    ``tags`` 仅用于 OpenAPI（如 admin / portal），不参与路径装配。
    """

    router: str
    tags: tuple[str, ...] = ()
    order: int = 100


@dataclass(frozen=True, slots=True)
class BeatScheduleSpec:
    name: str
    task: str
    schedule: float


@dataclass(frozen=True, slots=True)
class ServiceRegistration:
    """注册模块提供的框架服务实现。"""

    interface: str  # "data_scope_resolver" | "account_lookup"
    implementation: str  # "app.modules.x.impl:instance"


@dataclass(frozen=True, slots=True)
class ModuleSpec:
    name: str
    enabled: bool = True
    routes: tuple[RouteSpec, ...] = ()
    models: tuple[str, ...] = ()
    tasks: tuple[str, ...] = ()
    beat_schedules: tuple[BeatScheduleSpec, ...] = ()
    startup_hooks: tuple[str, ...] = ()
    shutdown_hooks: tuple[str, ...] = ()
    order: int = 100
    config_model: str = ""  # "app.modules.x.config:MySettings"
    config_from_db: bool = False
    services: tuple[ServiceRegistration, ...] = ()
    event_handlers: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()


def import_string(path: str) -> Any:
    module_path, separator, attr = path.partition(":")
    if not separator or not module_path or not attr:
        raise ValueError(f"Import path must use 'module:attribute' format: {path}")
    module = importlib.import_module(module_path)
    value: Any = module
    for part in attr.split("."):
        value = getattr(value, part)
    return value
