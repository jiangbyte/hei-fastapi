""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="user.admin",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.user.admin.router:router",
        ),
    ),
    models=("app.modules.user.admin.model",),
)
