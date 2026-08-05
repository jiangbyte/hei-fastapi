from datetime import datetime

from pydantic import Field

from app.core.config.enums import StorageProvider
from app.core.response.pagination import PageQuery
from app.core.schema.base import ApiSchema


class SysFileSchema(ApiSchema):
    id: str
    object_name: str
    original_name: str
    storage_config_id: str
    storage_provider: StorageProvider
    bucket: str | None = None
    content_type: str
    size: int
    url: str
    created_at: datetime = Field(examples=["2026-06-17T12:00:00Z"])
    created_by: str | None = None
    created_name: str | None = None
    updated_at: datetime = Field(examples=["2026-06-17T12:00:00Z"])
    updated_by: str | None = None
    updated_name: str | None = None


class FileUploadRequest(ApiSchema):
    """文件上传请求载荷，封装上传原文件信息和内容类型。"""

    filename: str
    content: bytes
    content_type: str
    storage_config_id: str | None = None
    storage_provider: StorageProvider | None = None
    category: str = ""
    object_name: str | None = None


class FileRecordCreate(ApiSchema):
    """文件元数据创建载荷，统一仓储层落库参数。"""

    object_name: str
    original_name: str
    storage_config_id: str
    storage_provider: StorageProvider
    bucket: str | None = None
    content_type: str
    size: int
    url: str


class FileUpdateRequest(ApiSchema):
    id: str = Field(min_length=1, max_length=64)
    original_name: str = Field(min_length=1, max_length=255)


class FileAdminPageQuery(PageQuery):
    original_name: str | None = Field(default=None, max_length=255)
    object_name: str | None = Field(default=None, max_length=255)
    storage_config_id: str | None = Field(default=None, max_length=64)
    storage_provider: StorageProvider | None = None
    content_type: str | None = Field(default=None, max_length=128)


class ObjectNameQuery(ApiSchema):
    object_name: str = Field(min_length=1, max_length=255)


class FileUrlRequest(ObjectNameQuery):
    pass


class FileUrlResponse(ApiSchema):
    object_name: str
    url: str
