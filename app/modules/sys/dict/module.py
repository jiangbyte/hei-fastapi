""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="sys.dict",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.dict.router:router",
        ),
        RouteSpec(
            tags=("portal",),
            router="app.modules.sys.dict.portal.router:router",
        ),
    ),
    models=("app.modules.sys.dict.model",),
)
