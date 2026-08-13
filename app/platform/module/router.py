""" Author: Charlie

API 路由装配：按模块清单导入各模块路由并按顺序挂载到统一的根路由。
"""

from __future__ import annotations

import logging
from functools import cache

from fastapi import APIRouter

from app.platform.module.discovery import load_module_specs
from app.platform.module.paths import API_ROOT_PREFIX
from app.platform.module.spec import ModuleSpec, RouteSpec, import_string

logger = logging.getLogger(__name__)

__all__ = ["API_ROOT_PREFIX", "build_api_router", "get_api_router"]


@cache
def get_api_router(package_name: str = "app.modules") -> APIRouter:
    """返回缓存的 API 根路由，避免重复装配。"""
    return build_api_router(load_module_specs(package_name))


def build_api_router(module_specs: list[ModuleSpec]) -> APIRouter:
    """按模块清单构建 API 根路由，子路由统一挂载 /api 前缀。"""
    api_router = APIRouter()
    route_specs: list[tuple[ModuleSpec, RouteSpec]] = [
        (module_spec, route_spec)
        for module_spec in module_specs
        for route_spec in module_spec.routes
    ]
    route_specs.sort(key=lambda item: (item[1].order, item[0].order, item[0].name))

    logger.info("Building API router with %d route specs", len(route_specs))
    for module_spec, route_spec in route_specs:
        route_router = import_string(route_spec.router)
        if not isinstance(route_router, APIRouter):
            raise TypeError(f"{module_spec.name} route {route_spec.router} is not an APIRouter")
        logger.debug(
            "Including router %s -> prefix=%s, tags=%s",
            route_spec.router,
            API_ROOT_PREFIX,
            route_spec.tags,
        )
        api_router.include_router(
            route_router,
            prefix=API_ROOT_PREFIX,
            tags=list(route_spec.tags),
        )
    logger.info("API router built with %d total routes", len(api_router.routes))
    return api_router
