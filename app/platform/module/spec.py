""" Author: Charlie

模块清单数据结构：定义路由、定时任务、服务注册与模块元信息等声明类型。
"""

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
class ServiceRegistration:
    """注册模块提供的框架服务实现。"""

    interface: str  # "data_scope_resolver" | "account_lookup"
    implementation: str  # "app.modules.x.impl:instance"


@dataclass(frozen=True, slots=True)
class ModuleSpec:
    """模块清单：声明路由、模型、任务、钩子、依赖与配置等元信息。"""

    name: str
    enabled: bool = True
    routes: tuple[RouteSpec, ...] = ()
    models: tuple[str, ...] = ()
    tasks: tuple[str, ...] = ()
    startup_hooks: tuple[str, ...] = ()
    shutdown_hooks: tuple[str, ...] = ()
    order: int = 100
    config_model: str = ""  # "app.modules.x.config:MySettings"
    config_from_db: bool = False
    services: tuple[ServiceRegistration, ...] = ()
    event_handlers: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()


def import_string(path: str) -> Any:
    """按 ``module:attribute`` 字符串导入并返回对象（支持多级属性）。"""
    module_path, separator, attr = path.partition(":")
    if not separator or not module_path or not attr:
        raise ValueError(f"Import path must use 'module:attribute' format: {path}")
    module = importlib.import_module(module_path)
    value: Any = module
    for part in attr.split("."):
        value = getattr(value, part)
    return value
