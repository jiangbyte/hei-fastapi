""" Author: Charlie """

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
