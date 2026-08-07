""" Author: Charlie """

from app.platform.module import BeatScheduleSpec, ModuleSpec, RouteSpec, ServiceRegistration

module = ModuleSpec(
    name="iam.account",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.iam.account.router:router",
        ),
    ),
    models=(
        "app.modules.iam.account.model",
        "app.modules.iam.account.password_history",
    ),
    tasks=("app.modules.iam.account.tasks",),
    beat_schedules=(
        BeatScheduleSpec(
            name="purge-cancelled-accounts-daily",
            task="account.purge_cancelled_accounts",
            schedule=86400.0,
        ),
    ),
    services=(
        ServiceRegistration(
            interface="account_lookup",
            implementation="app.modules.iam.account.lookup:account_lookup",
        ),
    ),
)
