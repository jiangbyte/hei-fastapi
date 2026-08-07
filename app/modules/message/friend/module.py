"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:53
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="message.friend",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.message.friend.router:admin_router",
        ),
        RouteSpec(
            tags=("portal",),
            router="app.modules.message.friend.router:portal_router",
        ),
    ),
    models=("app.modules.message.friend.model",),
)
