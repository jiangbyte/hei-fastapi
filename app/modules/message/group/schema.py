"""
由 HEI 代码生成器生成。
Author: Charlie
生成时间：2026-07-23 16:28:52
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireBool, WireInt


class MsgGroupCreateRequest(ApiSchema):
    name: str
    avatar: str | None = None
    description: str | None = None
    owner_account_type: str
    owner_account_id: str
    status: str
    join_mode: str
    max_members: WireInt
    member_count: WireInt
    extra: dict[str, Any]


class MsgGroupUpdateRequest(MsgGroupCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class MsgGroupAdminPageQuery(PageQuery):
    name: str | None = None
    status: str | None = None


class MsgGroupSchema(ApiSchema):
    id: str
    name: str
    avatar: str | None = None
    description: str | None = None
    owner_account_type: str
    owner_account_id: str
    status: str
    join_mode: str
    max_members: WireInt
    member_count: WireInt
    extra: dict[str, Any]
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    is_member: WireBool = False
    has_pending_request: WireBool = False


# ==================== 创建群组（当前用户） ====================


class GroupCreateRequest(ApiSchema):
    name: str = Field(min_length=1, max_length=128)
    avatar: str | None = None
    description: str | None = None
    join_mode: str = "APPROVAL"
    max_members: WireInt = 200


class GroupUpdateRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    name: str | None = None
    avatar: str | None = None
    description: str | None = None
    join_mode: str | None = None
    max_members: WireInt | None = None


class GroupDetailRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)


# ==================== 群组成员 ====================


class GroupMemberSchema(ApiSchema):
    id: str
    group_id: str
    account_type: str
    account_id: str
    role: str
    nickname: str | None = None
    is_muted: WireBool = False
    joined_at: datetime
    left_at: datetime | None = None
    extra: dict[str, Any]
    profile_name: str | None = None
    profile_avatar: str | None = None


class GroupMemberAddRequest(ApiSchema):
    group_id: str = Field(min_length=1, max_length=64)
    members: list[dict[str, str]] = Field(
        min_length=1
    )  # [{"account_type": "ADMIN", "account_id": "xxx"}]


class GroupMemberRemoveRequest(ApiSchema):
    group_id: str = Field(min_length=1, max_length=64)
    account_type: str
    account_id: str


class SetMemberRoleRequest(ApiSchema):
    group_id: str = Field(min_length=1, max_length=64)
    account_type: str
    account_id: str
    role: str


class GroupMemberListRequest(ApiSchema):
    group_id: str = Field(min_length=1, max_length=64)


class GroupSearchQuery(ApiSchema):
    keyword: str = Field(min_length=1)


# ==================== 入群申请 ====================


class GroupJoinRequestCreate(ApiSchema):
    group_id: str = Field(min_length=1, max_length=64)
    message: str | None = None


class GroupJoinRequestHandle(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    status: str  # ACCEPTED / REJECTED


class GroupJoinRequestSchema(ApiSchema):
    id: str
    group_id: str
    applicant_type: str
    applicant_id: str
    message: str | None = None
    status: str
    handled_by_type: str | None = None
    handled_by_id: str | None = None
    handled_at: datetime | None = None
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    applicant_name: str | None = None
    applicant_avatar: str | None = None
    group_name: str | None = None
