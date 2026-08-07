""" Author: Charlie

由 HEI 代码生成器生成。
Author: jiangbyte
"""
from datetime import datetime

from pydantic import Field

from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema


class MsgFeedbackCreateRequest(ApiSchema):
    content: str
    category: str
    contact: str | None = None
    attach_urls: list[str] = Field(default_factory=list)


class MsgFeedbackUpdateRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    status: str
    reply: str | None = None


class MsgFeedbackAdminPageQuery(PageQuery):
    content: str | None = None
    category: str | None = None
    status: str | None = None


class MyFeedbackPageQuery(PageQuery):
    pass


class MsgFeedbackSchema(ApiSchema):
    id: str
    content: str
    category: str
    contact: str | None = None
    attach_urls: list[str] = Field(default_factory=list)
    status: str
    reply: str | None = None
    replied_by: str | None = None
    replied_at: datetime | None = None
    submitter_account_type: str
    submitter_account_id: str
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    created_name: str | None = None
    updated_name: str | None = None
    submitter_avatar: str | None = None
    submitter_nickname: str | None = None
