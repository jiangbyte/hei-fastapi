""" Author: Charlie

门户用户模块装配：注册门户端用户中心与公开主页路由及资料数据模型。
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="user.portal",
    routes=(
        RouteSpec(
            tags=("portal",),
            router="app.modules.user.portal.router:router",
        ),
    ),
    models=("app.modules.user.portal.model",),
)
