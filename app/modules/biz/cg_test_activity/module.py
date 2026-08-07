"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-08-07 07:26:15
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="biz.cg_test_activity",
    enabled=False,
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.biz.cg_test_activity.router:router",
        ),
    ),
    models=("app.modules.biz.cg_test_activity.model",),
)
