from datetime import datetime

from pydantic import Field

from app.core.config.enums import AccountType
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema


class SessionAnalysisResponse(ApiSchema):
    online_account_count: int
    online_token_count: int
    admin_account_count: int
    portal_account_count: int
    one_hour_new_count: int
    max_token_count: int


class SessionPageQuery(PageQuery):
    account_type: AccountType | None = None
    account_id: str | None = Field(default=None, max_length=64)
    account: str | None = Field(default=None, max_length=128)
    ip: str | None = Field(default=None, max_length=64)


class SessionTokenInfo(ApiSchema):
    token: str
    device_label: str | None = None
    client_ip: str | None = None
    user_agent: str | None = None
    login_at: datetime | None = None
    last_active_at: datetime | None = None
    expires_at: datetime | None = None


class SessionAccountItem(ApiSchema):
    account_id: str
    account_type: AccountType | str
    account: str
    name: str | None = None
    nickname: str | None = None
    avatar: str | None = None
    latest_login_ip: str | None = None
    latest_login_time: datetime | None = None
    token_count: int
    first_login_at: datetime | None = None
    latest_active_at: datetime | None = None
    tokens: list[SessionTokenInfo] = Field(default_factory=list)


class SessionTokensQuery(ApiSchema):
    account_type: AccountType
    account_id: str = Field(min_length=1, max_length=64)


class SessionExitRequest(ApiSchema):
    targets: list[SessionTokensQuery] = Field(min_length=1)


class SessionTokenExitRequest(ApiSchema):
    tokens: list[str] = Field(min_length=1)
