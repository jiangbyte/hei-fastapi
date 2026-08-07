""" Author: Charlie """

from app.platform.module import ModuleSpec

module = ModuleSpec(
    name="iam.relation",
    models=("app.modules.iam.relation.model",),
)
