""" Author: Charlie

IAM 职位模块注册：声明路由与模型。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="iam.position",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.iam.position.router:router",
        ),
    ),
    models=("app.modules.iam.position.model",),
)
