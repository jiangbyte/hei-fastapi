""" Author: Charlie

系统配置模块声明：注册管理端路由与配置模型。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="sys.config",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.config.router:router",
        ),
    ),
    models=("app.platform.db.models.sys_config",),
)
