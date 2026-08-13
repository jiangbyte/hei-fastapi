""" Author: Charlie

IAM 关系模块注册：声明关系模型。
"""

from app.platform.module import ModuleSpec

module = ModuleSpec(
    name="iam.relation",
    models=("app.modules.iam.relation.model",),
)
