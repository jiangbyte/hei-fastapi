""" Author: Charlie

模块系统公共入口：对外暴露模块发现、路由装配、模型/任务加载与钩子执行等能力。
"""

from app.platform.module.discovery import clear_module_specs_cache, load_module_specs
from app.platform.module.hooks import run_event_handlers, run_shutdown_hooks, run_startup_hooks
from app.platform.module.loader import (
    load_declared_models,
    load_declared_tasks,
)
from app.platform.module.router import build_api_router, get_api_router
from app.platform.module.spec import (
    ModuleSpec,
    RouteSpec,
    ServiceRegistration,
)

__all__ = [
    "build_api_router",
    "clear_module_specs_cache",
    "get_api_router",
    "load_declared_models",
    "load_declared_tasks",
    "load_module_specs",
    "ModuleSpec",
    "RouteSpec",
    "run_event_handlers",
    "run_shutdown_hooks",
    "run_startup_hooks",
    "ServiceRegistration",
]
