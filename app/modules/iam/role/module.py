""" Author: Charlie

IAM 角色模块注册：声明路由与模型。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="iam.role",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.iam.role.router:router",
        ),
    ),
    models=("app.modules.iam.role.model",),
)
