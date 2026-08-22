""" Author: Charlie

Boot 对齐路由：默认 JSON 响应排除 null 字段（对齐 Jackson 未赋值字段不出现在 JSON）。
"""

from fastapi import APIRouter
from fastapi.routing import APIRoute, Mount


def enable_response_exclude_none(router: APIRouter) -> None:
    """递归为路由树启用 response_model_exclude_none。"""
    for route in router.routes:
        if isinstance(route, APIRoute):
            route.response_model_exclude_none = True
        elif isinstance(route, Mount) and isinstance(route.app, APIRouter):
            enable_response_exclude_none(route.app)


class BootAlignedAPIRouter(APIRouter):
    """默认排除响应中的 null 字段，与 hei-boot JSON 输出更接近。"""

    def add_api_route(self, path: str, endpoint, **kwargs):
        kwargs.setdefault("response_model_exclude_none", True)
        return super().add_api_route(path, endpoint, **kwargs)
