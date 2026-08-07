""" Author: Charlie """

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
