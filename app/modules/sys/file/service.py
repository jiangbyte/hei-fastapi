import asyncio
import logging
import re
from datetime import UTC, datetime
from pathlib import PurePosixPath
from uuid import uuid4

from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.enums import AccountType, StorageProvider
from app.core.config.settings import settings
from app.core.exceptions.business import BusinessError, NotFoundError
from app.core.response.pagination import PageData, PageQuery, build_page
from app.core.schema.base import IdQuery, IdsRequest, to_schema, to_schema_list
from app.core.security.data_scope import build_data_scope_filter
from app.core.security.session import SessionPayload
from app.modules.sys.file.model import SysFile
from app.modules.sys.file.repository import FileRepository
from app.modules.sys.file.schema import (
    FileAdminPageQuery,
    FileRecordCreate,
    FileUpdateRequest,
    FileUploadRequest,
    ObjectNameQuery,
    SysFileSchema,
)
from app.modules.user.utils.profile import get_profiles_batch
from app.platform.db.transaction import transactional
from app.platform.observability.metrics import record_file_upload_rejected
from app.platform.storage.config import StorageConfig
from app.platform.storage.local import LocalStorage
from app.platform.storage.manager import get_storage, resolve_storage_config
from app.platform.storage.url import is_external_url, normalize_object_name

logger = logging.getLogger(__name__)


class FileService:
    """文件服务，负责对象存储写入与文件元数据落库的一致性编排。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = FileRepository(db)

    def build_object_name(self, filename: str, category: str = "uploads") -> str:
        """构造对象存储路径，按日期分片 + UUID，不暴露原始文件名。"""
        safe_name = PurePosixPath(filename).name
        suffix = PurePosixPath(safe_name).suffix.lower()
        now = datetime.now(UTC)
        category = self._normalize_category(category)
        prefix = f"{category}/" if category else ""
        return (
            f"{prefix}{now:%Y}/{now:%m}/{now:%d}/"
            f"{uuid4().hex}{suffix}"
        )

    async def upload(self, payload: FileUploadRequest) -> SysFileSchema:
        """上传文件并创建元数据记录，参数通过对象统一承载。"""
        self._validate_upload(payload)
        storage_config = self._resolve_upload_storage_config(payload)
        storage = self._get_storage(storage_config)
        object_name = payload.object_name or self.build_object_name(
            payload.filename,
            payload.category or "uploads",
        )
        object_name = self._validate_object_name(object_name)
        url = await asyncio.to_thread(
            storage.upload_bytes,
            object_name,
            payload.content,
            content_type=payload.content_type,
        )
        async with transactional(self.db):
            entity = await self.repo.create(
                FileRecordCreate(
                    object_name=object_name,
                    original_name=PurePosixPath(payload.filename).name,
                    storage_config_id=storage_config.id,
                    storage_provider=storage_config.provider,
                    bucket=(
                        storage_config.bucket
                        if storage_config.provider != StorageProvider.LOCAL
                        else None
                    ),
                    content_type=payload.content_type,
                    size=len(payload.content),
                    url=url,
                )
            )
            return self._with_resolved_url(to_schema(SysFileSchema, entity))

    async def update(self, payload: FileUpdateRequest) -> None:
        async with transactional(self.db):
            await self.repo.update(payload)

    async def delete(self, payload: IdsRequest) -> None:
        """按文件 ID 批量删除对象存储文件和文件元数据。"""
        unique_ids = list(dict.fromkeys(payload.ids))
        entities = await self.repo.list_by_ids(unique_ids)
        if len(entities) != len(unique_ids):
            raise NotFoundError("File not found")
        async with transactional(self.db):
            for entity in entities:
                storage = self._get_storage(self._resolve_entity_storage_config(entity))
                await asyncio.to_thread(storage.delete_object, entity.object_name)
            await self.repo.delete_many(unique_ids)

    async def delete_by_object_name(self, object_name: str) -> None:
        """按对象存储路径删除文件和元数据，供业务表引用清理使用。"""
        normalized = normalize_object_name(object_name)
        if not normalized or is_external_url(normalized):
            raise NotFoundError("File not found")
        entity = await self.repo.get_by_object_name(normalized)
        if entity is None:
            raise NotFoundError("File not found")
        storage = self._get_storage(self._resolve_entity_storage_config(entity))
        async with transactional(self.db):
            await asyncio.to_thread(storage.delete_object, normalized)
            await self.repo.delete(entity)

    async def detail(self, query: IdQuery) -> SysFileSchema:
        schema = self._with_resolved_url(
            to_schema(SysFileSchema, await self.repo.get_required(query.id))
        )
        await self._resolve_creator_names([schema])
        return schema

    async def list_by_ids(self, payload: IdsRequest) -> list[SysFileSchema]:
        unique_ids = list(dict.fromkeys(payload.ids))
        entities = await self.repo.list_by_ids(unique_ids)
        entity_map = {entity.id: entity for entity in entities}
        if len(entity_map) != len(unique_ids):
            raise NotFoundError("File not found")
        return [
            self._with_resolved_url(to_schema(SysFileSchema, entity_map[file_id]))
            for file_id in unique_ids
        ]

    async def download_by_id(self, query: IdQuery) -> Response:
        entity = await self.repo.get_required(query.id)
        return await self.response(entity.object_name)

    async def get_url(self, query: ObjectNameQuery) -> str:
        """优先返回已落库的稳定 URL，不存在时退化为存储层实时构造。"""
        normalized = normalize_object_name(query.object_name)
        if not normalized:
            raise NotFoundError("File not found")
        if is_external_url(normalized):
            return normalized
        entity = await self.repo.get_by_object_name(normalized)
        storage = self._get_storage(self._resolve_entity_storage_config(entity))
        return str(storage.get_object_url(normalized))

    async def get_presigned_url(self, query: ObjectNameQuery) -> str:
        """获取对象的签名访问地址。"""
        normalized = normalize_object_name(query.object_name)
        if not normalized:
            raise NotFoundError("File not found")
        if is_external_url(normalized):
            return normalized
        entity = await self.repo.get_by_object_name(normalized)
        storage = self._get_storage(self._resolve_entity_storage_config(entity))
        return str(storage.get_presigned_url(normalized))

    async def response(self, query: ObjectNameQuery) -> Response:
        normalized = normalize_object_name(query.object_name)
        if not normalized:
            raise NotFoundError("File not found")
        entity = await self.repo.get_by_object_name(normalized)
        storage = self._get_storage(self._resolve_entity_storage_config(entity))
        if isinstance(storage, LocalStorage):
            path = storage.get_path(normalized)
            if not path.exists() or not path.is_file():
                raise NotFoundError("File not found")
            return FileResponse(
                path,
                media_type=entity.content_type if entity else None,
                filename=entity.original_name if entity else None,
                headers={"X-Content-Type-Options": "nosniff"},
            )
        return RedirectResponse(
            url=storage.get_object_url(normalized),
            headers={"X-Content-Type-Options": "nosniff"},
        )

    async def page(
        self,
        query: FileAdminPageQuery | PageQuery,
        session: SessionPayload | None = None,
    ) -> PageData[SysFileSchema]:
        """分页列出文件元数据记录。"""
        page_query = (
            query
            if isinstance(query, FileAdminPageQuery)
            else FileAdminPageQuery(pagination=query)
        )
        data_scope_filter = None
        if session is not None:
            data_scope_filter = await build_data_scope_filter(
                self.db,
                session,
                "sys:file:page",
                owner_column=SysFile.created_by,
            )
        items, total = await self.repo.list_files(
            page_query,
            data_scope_filter,
        )
        schemas = [
            self._with_resolved_url(schema)
            for schema in to_schema_list(SysFileSchema, items)
        ]
        await self._resolve_creator_names(schemas)
        return build_page(page_query.pagination, total, schemas)

    def _with_resolved_url(self, schema: SysFileSchema) -> SysFileSchema:
        storage_config = resolve_storage_config(
            schema.storage_config_id,
            provider=schema.storage_provider,
        )
        resolved_url = self._get_storage(storage_config).get_object_url(schema.object_name)
        schema.url = str(resolved_url) or schema.url
        return schema

    async def _resolve_creator_names(self, items: list[SysFileSchema]) -> None:
        """批量查询 created_by / updated_by 对应的昵称，写入 created_name / updated_name。"""
        account_ids: set[str] = set()
        for item in items:
            if item.created_by:
                account_ids.add(item.created_by)
            if item.updated_by:
                account_ids.add(item.updated_by)
        if not account_ids:
            return
        profiles = await get_profiles_batch(self.db, AccountType.ADMIN, list(account_ids))
        for item in items:
            if item.created_by and item.created_by in profiles:
                item.created_name = getattr(profiles[item.created_by], "nickname", None)
            if item.updated_by and item.updated_by in profiles:
                item.updated_name = getattr(profiles[item.updated_by], "nickname", None)

    def _resolve_upload_storage_config(self, payload: FileUploadRequest) -> StorageConfig:
        return resolve_storage_config(
            payload.storage_config_id,
            provider=payload.storage_provider,
        )

    def _resolve_entity_storage_config(self, entity: SysFile | None) -> StorageConfig:
        if entity is None:
            return resolve_storage_config()
        return resolve_storage_config(
            entity.storage_config_id,
            provider=entity.storage_provider,
        )

    def _get_storage(self, config: StorageConfig):
        return get_storage(config.id)

    def _validate_upload(self, payload: FileUploadRequest) -> None:
        safe_name = PurePosixPath(payload.filename).name
        logger.info(
            "upload validation | filename=%s suffix=%s "
            "allowed_extensions=%s denied_extensions=%s "
            "content_type=%s allowed_content_types=%s",
            payload.filename, PurePosixPath(safe_name).suffix.lower(),
            settings.storage.upload_allowed_extensions,
            settings.storage.upload_denied_extensions,
            payload.content_type, settings.storage.upload_allowed_content_types,
        )
        suffix = PurePosixPath(safe_name).suffix.lower()
        if not safe_name or safe_name in {".", ".."}:
            self._reject_upload("invalid_filename", "Invalid filename")
        if len(payload.content) > settings.storage.upload_max_bytes:
            self._reject_upload("too_large", "File is too large")
        denied_extensions = {item.lower() for item in settings.storage.upload_denied_extensions}
        if suffix and suffix in denied_extensions:
            self._reject_upload("denied_extension", "File extension is not allowed")
        allowed_extensions = {
            item.lower() for item in settings.storage.upload_allowed_extensions if item
        }
        if allowed_extensions and suffix not in allowed_extensions:
            self._reject_upload("extension_not_allowed", "File extension is not allowed")
        allowed_content_types = {
            item.lower() for item in settings.storage.upload_allowed_content_types if item
        }
        if allowed_content_types and payload.content_type.lower() not in allowed_content_types:
            self._reject_upload("content_type_not_allowed", "File content type is not allowed")
        self._validate_content_magic_bytes(payload)
        self._normalize_category(payload.category)
        if payload.object_name:
            self._validate_object_name(payload.object_name)

    def _validate_content_magic_bytes(self, payload: FileUploadRequest) -> None:
        """Validate file content magic bytes against declared content type.

        Only checks content types that have known magic signatures in the
        registry below.  Types that were explicitly allowed in the config
        table (``upload_allowed_content_types``) but *lack* a registered
        magic signature are silently skipped — this keeps the validator
        compatible with custom / future types without false positives.
        """
        content = getattr(payload, "content", None)
        if not content or not isinstance(content, (bytes, bytearray)):
            return
        if len(content) < 12:
            return
        header = content[:12]

        # Registry: (magic_prefix, content_type_prefix)
        magic_registry: dict[str, bytes] = {
            "image/jpeg": b"\xff\xd8\xff",
            "image/png": b"\x89PNG\r\n\x1a\n",
            "image/gif": b"GIF",
            "image/webp": b"RIFF",
            "application/pdf": b"%PDF",
        }

        ct = (payload.content_type or "").lower()

        # 在注册表中查找匹配的 content-type 前缀
        known_prefix = None
        for ctype_prefix in magic_registry:
            if ct.startswith(ctype_prefix):
                known_prefix = ctype_prefix
                break

        if known_prefix is None:
            # 该 content-type 在注册表中没有魔数规则 → 跳过检查
            return

        expected_magic = magic_registry[known_prefix]
        if not header.startswith(expected_magic):
            self._reject_upload(
                "content_magic_mismatch",
                f"文件内容类型与声明不符（期望 {payload.content_type}）",
            )

    def _normalize_category(self, category: str) -> str:
        value = str(category or "").strip().strip("/")
        if not value:
            return "" 
        if len(value) > settings.storage.upload_category_max_length:
            self._reject_upload("invalid_category", "Upload category is too long")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9/_-]*", value):
            self._reject_upload("invalid_category", "Upload category is invalid")
        if any(part in {"", ".", ".."} for part in value.split("/")):
            self._reject_upload("invalid_category", "Upload category is invalid")
        return value

    def _validate_object_name(self, object_name: str) -> str:
        normalized = normalize_object_name(object_name)
        if not normalized or is_external_url(normalized):
            self._reject_upload("invalid_object_name", "Object name is invalid")
        if any(part in {"", ".", ".."} for part in normalized.split("/")):
            self._reject_upload("invalid_object_name", "Object name is invalid")
        return normalized

    def _reject_upload(self, reason: str, message: str) -> None:
        record_file_upload_rejected(reason)
        raise BusinessError(message)
