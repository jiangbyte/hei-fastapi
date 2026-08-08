""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="sys.weak_password",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.weak_password.router:router",
        ),
    ),
    models=("app.platform.db.models.sys_weak_password",),
)
