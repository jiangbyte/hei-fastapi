""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="internal.health",
    routes=(
        RouteSpec(
            tags=("internal",),
            router="app.modules.internal.health.router:router",
            order=10,
        ),
    ),
)
