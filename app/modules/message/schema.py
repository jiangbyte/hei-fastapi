""" Author: Charlie """

from pydantic import Field

from app.core.schema.base import ApiSchema


class AccountRef(ApiSchema):
    account_type: str = Field(min_length=1, max_length=32)
    account_id: str = Field(min_length=1, max_length=64)
