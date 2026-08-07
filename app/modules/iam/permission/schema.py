""" Author: Charlie """

from app.core.schema.base import ApiSchema


class PermissionTreeSelectorResponse(ApiSchema):
    resources: list[str]
