""" Author: Charlie

IAM 部门模块注册：声明路由、模型与 data_scope_resolver 服务实现。
"""

from app.platform.module import ModuleSpec, RouteSpec, ServiceRegistration

module = ModuleSpec(
    name="iam.dept",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.iam.dept.router:router",
        ),
    ),
    models=("app.modules.iam.dept.model",),
    services=(
        ServiceRegistration(
            interface="data_scope_resolver",
            implementation="app.modules.iam.dept.resolver:resolver",
        ),
    ),
)
