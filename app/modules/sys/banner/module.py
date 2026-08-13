""" Author: Charlie

展示图模块声明：注册管理端/公开端路由、模型与周期任务。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="sys.banner",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.banner.router:router",
        ),
        RouteSpec(
            tags=("portal",),
            router="app.modules.sys.banner.portal.router:router",
        ),
    ),
    models=("app.modules.sys.banner.model",),
    tasks=("app.modules.sys.banner.tasks",),
)
