""" Author: Charlie """

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
