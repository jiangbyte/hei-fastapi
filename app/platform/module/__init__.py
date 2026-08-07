""" Author: Charlie """

from app.platform.module.discovery import clear_module_specs_cache, load_module_specs
from app.platform.module.hooks import run_event_handlers, run_shutdown_hooks, run_startup_hooks
from app.platform.module.loader import (
    collect_beat_schedule,
    load_declared_models,
    load_declared_tasks,
)
from app.platform.module.router import build_api_router, get_api_router
from app.platform.module.spec import (
    BeatScheduleSpec,
    ModuleSpec,
    RouteSpec,
    ServiceRegistration,
)

__all__ = [
    "BeatScheduleSpec",
    "build_api_router",
    "clear_module_specs_cache",
    "collect_beat_schedule",
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
