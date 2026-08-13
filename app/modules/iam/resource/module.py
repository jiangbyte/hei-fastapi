""" Author: Charlie

IAM 资源模块注册：声明管理端与门户端路由及模型。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="iam.resource",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.iam.resource.router:router",
        ),
        RouteSpec(
            tags=("portal",),
            router="app.modules.iam.resource.portal.router:router",
        ),
    ),
    models=("app.modules.iam.resource.model",),
)
