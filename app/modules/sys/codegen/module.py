""" Author: Charlie

代码生成模块声明：注册管理端路由与生成方案模型。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="sys.codegen",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.codegen.router:router",
        ),
    ),
    models=("app.modules.sys.codegen.model",),
)
