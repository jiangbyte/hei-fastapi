""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="sys.config",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.config.router:router",
        ),
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.config.storage_router:router",
        ),
    ),
    models=(
        "app.platform.db.models.sys_config",
        "app.platform.db.models.sys_storage_config",
    ),
)
