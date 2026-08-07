""" Author: Charlie """

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="message.im",
    order=50,
    config_model="app.modules.message.im.config:ImSettings",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.message.im.http_router:admin_router",
        ),
        RouteSpec(
            tags=("portal",),
            router="app.modules.message.im.http_router:portal_router",
        ),
    ),
    startup_hooks=("app.modules.message.im.server:start_im_realtime",),
    shutdown_hooks=("app.modules.message.im.server:stop_im_realtime",),
    depends_on=(),
)
