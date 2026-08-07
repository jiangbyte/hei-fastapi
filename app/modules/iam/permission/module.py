""" Author: Charlie """

from app.platform.module import ModuleSpec

# 权限辅助逻辑在 service.py；HTTP 接口在 iam.resource 下。
module = ModuleSpec(
    name="iam.permission",
)
