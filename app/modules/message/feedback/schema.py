""" Author: Charlie

由 HEI 代码生成器生成。
Author: jiangbyte
"""
from datetime import datetime

from pydantic import Field

from app.core.config.enums import AccountType
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireInt


class MsgFeedbackCreateRequest(ApiSchema):
    title: str = Field(min_length=1, max_length=255)
    content: str
    category: str
    contact: str | None = None
    attach_object_names: list[str] = Field(default_factory=list)


class MsgFeedbackUpdateRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    status: str
    reply: str | None = None


class MsgFeedbackAdminPageQuery(PageQuery):
    title: str | None = None
    category: str | None = None
    status: str | None = None
    submitter_account_type: AccountType | None = None


class MyFeedbackPageQuery(PageQuery):
    pass


class MsgFeedbackAttachmentSchema(ApiSchema):
    object_name: str
    id: str | None = None
    original_name: str | None = None
    content_type: str | None = None
    size: WireInt | None = None
    url: str | None = None


class MsgFeedbackSchema(ApiSchema):
    id: str
    title: str
    content: str
    category: str
    contact: str | None = None
    attach_object_names: list[str] = Field(default_factory=list)
    attachments: list[MsgFeedbackAttachmentSchema] = Field(default_factory=list)
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
