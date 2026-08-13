""" Author: Charlie

文件模块声明：注册管理端/公开端/公共路由、模型与清理任务。
"""

from app.platform.module import ModuleSpec, RouteSpec

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
)
