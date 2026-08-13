""" Author: Charlie

由 HEI 代码生成器生成。
Author: jiangbyte

反馈模块装配：注册管理端与门户端的反馈路由及数据模型。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="message.feedback",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.message.feedback.router:admin_router",
        ),
        RouteSpec(
            tags=("portal",),
            router="app.modules.message.feedback.router:portal_router",
        ),
    ),
    models=("app.modules.message.feedback.model",),
)
