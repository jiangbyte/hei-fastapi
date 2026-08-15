""" Author: Charlie

由 HEI 代码生成器生成。
Author: jiangbyte

反馈请求与响应模型：创建/更新请求、分页查询条件与详情响应。
"""

from datetime import datetime

from pydantic import Field

from app.core.config.enums import AccountType
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireInt


class SysFeedbackCreateRequest(ApiSchema):
    """创建反馈请求。"""

    title: str = Field(min_length=1, max_length=255)
    content: str
    category: str
    contact: str | None = None
    attach_object_names: list[str] = Field(default_factory=list)


class SysFeedbackUpdateRequest(ApiSchema):
    """更新反馈请求（状态与回复）。"""

    id: str = Field(min_length=1, max_length=64)
    status: str
    reply: str | None = None


class SysFeedbackAdminPageQuery(PageQuery):
    """管理端反馈分页查询条件。"""

    title: str | None = None
    category: str | None = None
    status: str | None = None
    submitter_account_type: AccountType | None = None


class MyFeedbackPageQuery(PageQuery):
    """「我的反馈」分页查询条件（无额外过滤）。"""

    pass


class SysFeedbackAttachmentSchema(ApiSchema):
    """反馈附件信息。"""

    object_name: str
    id: str | None = None
    original_name: str | None = None
    content_type: str | None = None
    size: WireInt | None = None
    url: str | None = None


class SysFeedbackSchema(ApiSchema):
    """反馈详情响应，含附件与提交者资料。"""

    id: str
    title: str
    content: str
    category: str
    contact: str | None = None
    attach_object_names: list[str] = Field(default_factory=list)
    attachments: list[SysFeedbackAttachmentSchema] = Field(default_factory=list)
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
