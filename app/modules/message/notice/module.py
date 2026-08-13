""" Author: Charlie

消息通知模块装配：注册管理端与门户端的通知路由及数据模型。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="message.notice",
    routes=(
        RouteSpec(tags=("admin",), router="app.modules.message.notice.router:admin_router"),
        RouteSpec(tags=("portal",), router="app.modules.message.notice.router:portal_router"),
    ),
    models=("app.modules.message.notice.model",),
)
