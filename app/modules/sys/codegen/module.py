""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="sys.codegen",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.codegen.router:router",
        ),
    ),
    models=("app.modules.sys.codegen.model",),
)
