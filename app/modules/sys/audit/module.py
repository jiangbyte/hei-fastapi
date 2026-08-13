""" Author: Charlie

审计模块声明：注册路由、模型、周期任务与事件处理器。
"""

from app.platform.module import ModuleSpec, RouteSpec

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
    event_handlers=("app.modules.sys.audit.event_handler:register",),
)
