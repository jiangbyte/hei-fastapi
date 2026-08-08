""" Author: Charlie """

from datetime import datetime

from pydantic import Field

from app.core.config.enums import StatusEnum
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireInt
from app.modules.sys.banner.enums import BannerDisplayScope, BannerLinkType


class BannerCreateRequest(ApiSchema):
    title: str = Field(min_length=1, max_length=255)
    image: str = Field(min_length=1, max_length=500)
    url: str | None = Field(default=None, max_length=500)
    link_type: BannerLinkType = BannerLinkType.URL
    summary: str | None = Field(default=None, max_length=500)
    description: str | None = None
    category: str = Field(min_length=1, max_length=32)
    type: str = Field(min_length=1, max_length=32)
    position: str = Field(min_length=1, max_length=32)
    display_scope: BannerDisplayScope
    sort: WireInt = 0
    status: StatusEnum = StatusEnum.ENABLED
    start_at: datetime | None = None
    end_at: datetime | None = None


class BannerUpdateRequest(BannerCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class BannerAdminPageQuery(PageQuery):
    display_scope: BannerDisplayScope | None = None
    category: str | None = Field(default=None, max_length=32)
    type: str | None = Field(default=None, max_length=32)
    position: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, max_length=32)


class BannerPublicListQuery(ApiSchema):
    position: str = Field(min_length=1, max_length=32)
    category: str | None = Field(default=None, max_length=32)
    type: str | None = Field(default=None, max_length=32)


class SysBannerSchema(ApiSchema):
    id: str
    title: str
    image: str
    image_url: str | None = None
    url: str | None = None
    link_type: BannerLinkType | str
    summary: str | None = None
    description: str | None = None
    category: str
    type: str
    position: str
    display_scope: BannerDisplayScope | str
    sort: WireInt
    interaction_count: WireInt
    status: StatusEnum | str
    start_at: datetime | None = None
    end_at: datetime | None = None
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    created_name: str | None = None
    updated_name: str | None = None
