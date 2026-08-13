""" Author: Charlie

管理端用户模块装配：注册管理端用户中心路由及资料数据模型。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="user.admin",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.user.admin.router:router",
        ),
    ),
    models=("app.modules.user.admin.model",),
)
