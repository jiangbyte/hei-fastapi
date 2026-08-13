""" Author: Charlie

IAM 账户组模块注册：声明路由与模型。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="iam.group",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.iam.group.router:router",
        ),
    ),
    models=("app.modules.iam.group.model",),
)
