from datetime import datetime

from pydantic import Field

from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema


class SendMessageRequest(ApiSchema):
    conversation_id: str | None = Field(default=None, min_length=1, max_length=64)
    group_id: str | None = Field(default=None, min_length=1, max_length=64)
    participant_refs: list[dict] = Field(default_factory=list, description="[{'account_type':..,'account_id':..}] for creating direct thread on the fly")
    title: str | None = Field(default=None, max_length=255)
    parent_id: str | None = Field(default=None, max_length=64)
    content: str = Field(min_length=1)
    content_type: str = Field(default="TEXT", max_length=32)
    msg_type: str = Field(default="TEXT", max_length=32)
    sender_name: str | None = Field(default=None, max_length=128)
    attachments: list["MessageAttachmentInput"] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict)


class MessageAttachmentInput(ApiSchema):
    file_id: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    url: str = Field(min_length=1, max_length=1024)
    content_type: str | None = Field(default=None, max_length=128)
    size: int | None = Field(default=None, ge=0)
    attachment_type: str = Field(default="FILE", max_length=32)
    thumbnail_url: str | None = Field(default=None, max_length=1024)
    sort: int = 0
    extra: dict = Field(default_factory=dict)


class MessagePageQuery(PageQuery):
    conversation_id: str = Field(min_length=1, max_length=64)


class MessageUnreadCountQuery(ApiSchema):
    conversation_id: str = Field(min_length=1, max_length=64)


class MessageReadRequest(ApiSchema):
    conversation_id: str = Field(min_length=1, max_length=64)
    terminal_id: str | None = None


class MessageSchema(ApiSchema):
    id: str
    conversation_id: str
    msg_type: str
    parent_id: str | None = None
    sender_type: str
    sender_account_type: str | None = None
    sender_account_id: str | None = None
    sender_name: str | None = None
    sender_avatar: str | None = None
    sender_nickname: str | None = None
    content: str
    content_type: str
    reply_count: int = 0
    is_revoked: bool = False
    revoked_at: datetime | None = None
    extra: dict
    created_at: datetime
    attachments: list["MessageAttachmentSchema"] = Field(default_factory=list)


class MessageAttachmentSchema(ApiSchema):
    id: str
    message_id: str
    file_id: str | None = None
    name: str
    url: str
    content_type: str | None = None
    size: int | None = None
    attachment_type: str
    thumbnail_url: str | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None
    sort: int
    extra: dict


class RevokeMessageRequest(ApiSchema):
    message_id: str = Field(min_length=1, max_length=64)


class UnreadCountResponse(ApiSchema):
    unread_count: int = 0
