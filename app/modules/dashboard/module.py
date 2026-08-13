""" Author: Charlie

仪表盘模块装配：注册管理端仪表盘路由。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="dashboard",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.dashboard.router:router",
            order=5,
        ),
    ),
)
