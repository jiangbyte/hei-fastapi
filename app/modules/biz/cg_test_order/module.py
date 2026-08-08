"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-08-08 21:09:54
"""

from app.platform.module import ModuleSpec, RouteSpec

module = ModuleSpec(
    name="biz.cg_test_order",
    routes=(
        RouteSpec(
            tags=("admin",),
            router="app.modules.biz.cg_test_order.router:router",
        ),
    ),
    models=("app.modules.biz.cg_test_order.model",),
)
