from datetime import datetime

from pydantic import Field

from app.modules.sys.banner.enums import (
    BannerCategory,
    BannerDisplayScope,
    BannerLinkType,
    BannerPosition,
    BannerType,
)
from app.core.config.enums import StatusEnum
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema


class BannerCreateRequest(ApiSchema):
    title: str = Field(min_length=1, max_length=255)
    image: str = Field(min_length=1, max_length=500)
    url: str | None = Field(default=None, max_length=500)
    link_type: BannerLinkType = BannerLinkType.URL
    summary: str | None = Field(default=None, max_length=500)
    description: str | None = None
    category: BannerCategory
    type: BannerType
    position: BannerPosition
    display_scope: BannerDisplayScope
    sort: int = 0
    status: StatusEnum = StatusEnum.ENABLED
    start_at: datetime | None = None
    end_at: datetime | None = None


class BannerUpdateRequest(BannerCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class BannerAdminPageQuery(PageQuery):
    display_scope: BannerDisplayScope | None = None
    category: BannerCategory | None = None
    type: BannerType | None = None
    position: BannerPosition | None = None
    status: str | None = Field(default=None, max_length=32)


class BannerPublicListQuery(ApiSchema):
    position: BannerPosition
    category: BannerCategory | None = None
    type: BannerType | None = None


class SysBannerSchema(ApiSchema):
    id: str
    title: str
    image: str
    url: str | None = None
    link_type: BannerLinkType
    summary: str | None = None
    description: str | None = None
    category: BannerCategory
    type: BannerType
    position: BannerPosition
    display_scope: BannerDisplayScope
    sort: int
    interaction_count: int
    status: StatusEnum | str
    start_at: datetime | None = None
    end_at: datetime | None = None
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None
    created_name: str | None = None
    updated_name: str | None = None
