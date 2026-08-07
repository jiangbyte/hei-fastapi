""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="user.portal",
    routes=(
        RouteSpec(
            tags=("portal",),
            router="app.modules.user.portal.router:router",
        ),
    ),
    models=("app.modules.user.portal.model",),
)
