""" Author: Charlie """

from datetime import datetime

from pydantic import Field

from app.core.schema.base import ApiSchema
from app.core.schema.wire import WireBool, WireInt


class StorageConfigCreateRequest(ApiSchema):
    name: str = Field(min_length=1, max_length=255)
    provider: str = Field(min_length=1, max_length=32)
    bucket: str | None = Field(default=None, max_length=255)
    endpoint: str | None = Field(default=None, max_length=500)
    access_key: str | None = Field(default=None, max_length=255)
    secret_key: str | None = Field(default=None, max_length=255)
    region: str | None = Field(default=None, max_length=100)
    use_ssl: WireBool = False
    base_url: str | None = Field(default=None, max_length=500)
    public_path: str = "/api/v1/files"
    local_root: str = ".runtime/storage"
    is_default: WireBool = False
    remark: str | None = Field(default=None, max_length=255)
    sort_code: WireInt = 0


class StorageConfigUpdateRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    name: str | None = Field(default=None, max_length=255)
    provider: str | None = Field(default=None, max_length=32)
    bucket: str | None = Field(default=None, max_length=255)
    endpoint: str | None = Field(default=None, max_length=500)
    access_key: str | None = Field(default=None, max_length=255)
    secret_key: str | None = Field(default=None, max_length=255)
    region: str | None = Field(default=None, max_length=100)
    use_ssl: WireBool | None = None
    base_url: str | None = Field(default=None, max_length=500)
    public_path: str | None = Field(default=None, max_length=255)
    local_root: str | None = Field(default=None, max_length=500)
    is_default: WireBool | None = None
    remark: str | None = Field(default=None, max_length=255)
    sort_code: WireInt | None = None


class StorageConfigSetDefaultRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)


class SysStorageConfigSchema(ApiSchema):
    id: str
    name: str
    provider: str
    bucket: str | None = None
    endpoint: str | None = None
    access_key: str | None = None
    secret_key: str | None = None
    access_key_set: WireBool = False
    secret_key_set: WireBool = False
    region: str | None = None
    use_ssl: WireBool = False
    base_url: str | None = None
    public_path: str = "/api/v1/files"
    local_root: str = ".runtime/storage"
    is_default: WireBool = False
    remark: str | None = None
    sort_code: WireInt = 0
    created_at: datetime
    created_by: str | None = None
    updated_at: datetime
    updated_by: str | None = None
