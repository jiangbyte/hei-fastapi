""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="auth",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.auth.router:admin_router",
            order=10,
        ),
        RouteSpec(
            tags=("admin",),
            router="app.modules.auth.session_admin_router:router",
            order=11,
        ),
        RouteSpec(
            tags=("portal",),
            router="app.modules.auth.router:portal_router",
            order=10,
        ),
    ),
)
