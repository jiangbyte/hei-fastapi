""" Author: Charlie """

from app.platform.module import BeatScheduleSpec, ModuleSpec, RouteSpec

module = ModuleSpec(
    name="sys.file",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.file.router:router",
        ),
        RouteSpec(
            tags=("portal",),
            router="app.modules.sys.file.portal.router:router",
        ),
        RouteSpec(
            tags=("public",),
            router="app.modules.sys.file.public_router:router",
            order=10,
        ),
    ),
    models=("app.modules.sys.file.model",),
    tasks=("app.modules.sys.file.tasks",),
    beat_schedules=(
        BeatScheduleSpec(
            name="sys-file-cleanup-local-orphans",
            task="sys.file.cleanup_local_orphans",
            schedule=3600.0,
        ),
    ),
)
