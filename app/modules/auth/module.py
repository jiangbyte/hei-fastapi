""" Author: Charlie

认证模块：声明 admin / portal 端路由的挂载规格，供平台模块加载器注册。
"""

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
