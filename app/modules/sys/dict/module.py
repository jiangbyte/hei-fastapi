""" Author: Charlie

系统字典模块声明：注册管理端/公开端路由与字典模型。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="sys.dict",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.dict.router:router",
        ),
        RouteSpec(
            tags=("portal",),
            router="app.modules.sys.dict.portal.router:router",
        ),
    ),
    models=("app.modules.sys.dict.model",),
)
