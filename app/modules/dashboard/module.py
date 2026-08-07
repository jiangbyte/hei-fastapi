""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="dashboard",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.dashboard.router:router",
            order=5,
        ),
    ),
)
