""" Author: Charlie """

from app.platform.module import BeatScheduleSpec, ModuleSpec, RouteSpec

module = ModuleSpec(
    name="sys.banner",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.banner.router:router",
        ),
        RouteSpec(
            tags=("portal",),
            router="app.modules.sys.banner.portal.router:router",
        ),
    ),
    models=("app.modules.sys.banner.model",),
    tasks=("app.modules.sys.banner.tasks",),
    beat_schedules=(
        BeatScheduleSpec(
            name="flush-banner-interactions-every-5-minutes",
            task="banner.flush_interactions",
            schedule=300.0,
        ),
    ),
)
