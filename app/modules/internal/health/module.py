""" Author: Charlie

内部健康检查模块装配：注册存活/就绪探针路由。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="internal.health",
    routes=(
        RouteSpec(
            tags=("internal",),
            router="app.modules.internal.health.router:router",
            order=10,
        ),
    ),
)
