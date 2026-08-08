""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="iam.client",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.iam.client.router:router",
        ),
    ),
    models=("app.modules.iam.client.model",),
)
