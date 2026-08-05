from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="message.websocket",
    routes=(
        RouteSpec(
            version="v1",
            prefix="/admin",
            tags=("admin",),
            router="app.modules.message.websocket.handler:router",
        ),
        RouteSpec(
            version="v1",
            prefix="/portal",
            tags=("portal",),
            router="app.modules.message.websocket.handler:router",
        ),
    ),
)
