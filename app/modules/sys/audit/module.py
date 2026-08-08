""" Author: Charlie """

from app.core.config.settings import settings
from app.platform.module import BeatScheduleSpec, ModuleSpec, RouteSpec

module = ModuleSpec(
    name="sys.audit",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.sys.audit.router:router",
        ),
    ),
    models=(
        "app.modules.sys.audit.model",
        "app.modules.sys.audit.alert_model",
        "app.modules.sys.audit.outbox",
    ),
    tasks=("app.modules.sys.audit.tasks",),
    beat_schedules=(
        BeatScheduleSpec(
            name="audit-analysis-cycle",
            task="audit.analysis_cycle",
            # 启动时读 settings；配置热更新由 sync_audit_interval_to_redbeat 覆盖
            schedule=float(settings.audit_alert.analysis_interval_seconds),
        ),
    ),
    event_handlers=("app.modules.sys.audit.event_handler:register",),
)
