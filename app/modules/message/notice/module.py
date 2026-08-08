""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="message.notice",
    routes=(
        RouteSpec(tags=("admin",), router="app.modules.message.notice.router:admin_router"),
        RouteSpec(tags=("portal",), router="app.modules.message.notice.router:portal_router"),
    ),
    models=("app.modules.message.notice.model",),
)
