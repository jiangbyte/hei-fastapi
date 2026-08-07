""" Author: Charlie """

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
