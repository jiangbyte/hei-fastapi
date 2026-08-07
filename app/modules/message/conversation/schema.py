"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:54
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema, Id
from app.core.schema.wire import WireBool, WireInt


class MsgConversationCreateRequest(ApiSchema):
    conversation_type: str
    title: str | None = None
    avatar: str | None = None
    group_id: str | None = None
    owner_account_type: str | None = None
    owner_account_id: str | None = None
    status: str
    last_message_id: str | None = None
    last_message_at: datetime | None = None
    # last_message 仅为读模型展示字段，不入库
    extra: dict[str, Any]


class MsgConversationUpdateRequest(MsgConversationCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class MsgConversationAdminPageQuery(PageQuery):
    title: str | None = None
    status: str | None = None


class ConversationMemberSchema(ApiSchema):
    id: str
    conversation_id: str
    account_type: str
    account_id: str
    role: str
    unread_count: WireInt
    last_read_message_id: str | None = None
    last_read_at: datetime | None = None
    last_delivered_at: datetime | None = None
    is_muted: WireBool
    is_pinned: WireBool
    joined_at: datetime
    left_at: datetime | None = None
    extra: dict[str, Any]
    profile_name: str | None = None
    profile_avatar: str | None = None
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None


class MsgConversationSchema(ApiSchema):
    id: str
    conversation_type: str
    title: str | None = None
    avatar: str | None = None
    group_id: str | None = None
    owner_account_type: str | None = None
    owner_account_id: str | None = None
    status: str
    last_message_id: str | None = None
    last_message_at: datetime | None = None
    last_message: str | None = None
    extra: dict[str, Any]
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    unread_count: WireInt = 0
    members: list[ConversationMemberSchema] = Field(default_factory=list)


class CreateDirectConversationRequest(ApiSchema):
    account_type: str
    account_id: str


class MuteConversationRequest(ApiSchema):
    conversation_id: Id
    is_muted: WireBool


class PinConversationRequest(ApiSchema):
    conversation_id: Id
    is_pinned: WireBool
