""" Author: Charlie

IAM 账户模块注册：声明路由、模型、定时任务与 account_lookup 服务实现。
"""

from app.platform.module import ModuleSpec, RouteSpec, ServiceRegistration

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
    services=(
        ServiceRegistration(
            interface="account_lookup",
            implementation="app.modules.iam.account.lookup:account_lookup",
        ),
    ),
)
