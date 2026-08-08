""" Author: Charlie """

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from app.core.config.enums import AccountType, StatusEnum
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireInt
from app.modules.sys.banner.enums import BannerLinkType

_ALLOWED_ACCOUNT_TYPES = {item.value for item in AccountType}


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
    target_account_types: list[str] = Field(default_factory=list)
    sort: WireInt = 0
    status: StatusEnum = StatusEnum.ENABLED
    start_at: datetime | None = None
    end_at: datetime | None = None

    @field_validator("target_account_types", mode="before")
    @classmethod
    def normalize_target_account_types(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            raise ValueError("目标账户类型必须是数组")
        return [str(item).strip().upper() for item in value if str(item).strip()]

    @model_validator(mode="after")
    def validate_target_account_types(self):
        types = list(dict.fromkeys(self.target_account_types))
        if not types:
            raise ValueError("必须选择目标账户类型")
        invalid = [item for item in types if item not in _ALLOWED_ACCOUNT_TYPES]
        if invalid:
            raise ValueError(f"目标账户类型无效: {', '.join(invalid)}")
        self.target_account_types = types
        return self


class BannerUpdateRequest(BannerCreateRequest):
    id: str = Field(min_length=1, max_length=64)


class BannerAdminPageQuery(PageQuery):
    target_account_type: AccountType | None = None
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
    target_account_types: list[str] = Field(default_factory=list)
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
