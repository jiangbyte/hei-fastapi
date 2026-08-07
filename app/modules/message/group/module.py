"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:52
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="message.group",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.message.group.router:admin_router",
        ),
        RouteSpec(
            tags=("portal",),
            router="app.modules.message.group.router:portal_router",
        ),
    ),
    models=("app.modules.message.group.model",),
)
