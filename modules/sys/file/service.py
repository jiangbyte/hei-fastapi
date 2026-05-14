import io
import os
import platform
import base64
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)
from fastapi import Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from core.result import page_data, PageDataField
from core.exception import BusinessException
from core.utils.model_utils import strip_system_fields
from core.utils.snowflake_utils import generate_id
from core.auth import HeiAuthTool
from core.storage import LocalStorage, MinioStorage, S3Storage
from modules.sys.config.service import ConfigService
from .models import SysFile
from .dao import FileDao
from .params import FileVO, FilePageParam, FileIdParam

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}

ENGINE_LOCAL = "LOCAL"
ENGINE_MINIO = "MINIO"
ENGINE_ALIYUN = "ALIYUN"
ENGINE_S3 = "S3"
ENGINE_TENCENT = "TENCENT"


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.1f}MB"
    else:
        return f"{size_bytes / 1024 / 1024 / 1024:.1f}GB"


def _generate_thumbnail(data: bytes, suffix: str) -> Optional[str]:
    suffix = suffix.lower()
    if suffix not in IMAGE_EXTENSIONS:
        return None
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        img.thumbnail((300, 300))
        buf = io.BytesIO()
        img.save(buf, format=img.format or "JPEG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        mime = f"image/{img.format.lower() if img.format else 'jpeg'}"
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


class FileService:
    def __init__(self, db: Session):
        self.dao = FileDao(db)
        self._config_service = ConfigService(db)

    async def _get_current_user_id(self, request: Request) -> Optional[str]:
        try:
            return await HeiAuthTool.getLoginIdDefaultNull(request)
        except Exception as e:
            logger.warning("Failed to get current user ID: %s", e)
            return None

    async def _get_storage_config(self, engine: str) -> dict:
        """Read storage engine config from sys_config table."""
        if engine == ENGINE_LOCAL:
            is_windows = platform.system() == "Windows"
            key = "SYS_FILE_LOCAL_FOLDER_FOR_WINDOWS" if is_windows else "SYS_FILE_LOCAL_FOLDER_FOR_UNIX"
            folder = await self._config_service.get_value_by_key(key)
            if not folder:
                folder = "D:/hei-file-upload" if is_windows else "/data/hei-file-upload"
            return {"folder": folder}

        prefix = f"SYS_FILE_{engine}_"
        config_keys = {
            "endpoint": f"{prefix}END_POINT",
            "access_key": f"{prefix}ACCESS_KEY" if engine != ENGINE_ALIYUN else f"{prefix}ACCESS_KEY_ID",
            "secret_key": f"{prefix}SECRET_KEY" if engine != ENGINE_ALIYUN else f"{prefix}ACCESS_KEY_SECRET",
            "default_bucket": f"{prefix}DEFAULT_BUCKET_NAME",
        }

        values = await self._config_service.get_values_by_keys(list(config_keys.values()))
        cfg = {k: values.get(v) for k, v in config_keys.items()}

        if engine in (ENGINE_S3,):
            region_key = f"{prefix}REGION"
            region_val = await self._config_service.get_value_by_key(region_key)
            cfg["region"] = region_val

        return cfg

    async def _create_storage(self, engine: str):
        """Create a storage engine instance from DB config."""
        cfg = await self._get_storage_config(engine)

        if engine == ENGINE_LOCAL:
            return LocalStorage(cfg["folder"])
        elif engine == ENGINE_MINIO:
            return MinioStorage(
                endpoint=cfg.get("endpoint", ""),
                access_key=cfg.get("access_key", ""),
                secret_key=cfg.get("secret_key", ""),
                default_bucket=cfg.get("default_bucket", "hei-files"),
            )
        elif engine == ENGINE_S3:
            return S3Storage(
                endpoint=cfg.get("endpoint", ""),
                access_key=cfg.get("access_key", ""),
                secret_key=cfg.get("secret_key", ""),
                default_bucket=cfg.get("default_bucket", "hei-files"),
                region=cfg.get("region", "us-east-1"),
            )
        elif engine == ENGINE_ALIYUN:
            from core.storage.s3_storage import S3Storage as AliyunOSSStorage
            return AliyunOSSStorage(
                endpoint=cfg.get("endpoint", ""),
                access_key=cfg.get("access_key", ""),
                secret_key=cfg.get("secret_key", ""),
                default_bucket=cfg.get("default_bucket", "hei-files"),
                path_style=False,
            )
        elif engine == ENGINE_TENCENT:
            from core.storage.s3_storage import S3Storage as TencentCOSStorage
            return TencentCOSStorage(
                endpoint=cfg.get("endpoint", ""),
                access_key=cfg.get("access_key", ""),
                secret_key=cfg.get("secret_key", ""),
                default_bucket=cfg.get("default_bucket", "hei-files"),
                path_style=False,
            )
        else:
            raise BusinessException(f"不支持的存储引擎: {engine}")

    async def _get_engine(self, engine: Optional[str] = None) -> str:
        if engine:
            return engine.upper()
        default = await self._config_service.get_value_by_key("SYS_DEFAULT_FILE_ENGINE")
        return default or ENGINE_LOCAL

    def _generate_file_key(self, file_id: str, suffix: str) -> str:
        now = datetime.now()
        return f"{now.year}/{now.month:02d}/{now.day:02d}/{file_id}{suffix}"

    async def upload(self, file: UploadFile, request: Request,
                     engine: Optional[str] = None) -> dict:
        engine = await self._get_engine(engine)
        data = await file.read()
        size_bytes = len(data)
        suffix = os.path.splitext(file.filename or "unknown")[1].lower()
        file_id = generate_id()
        obj_name = f"{file_id}{suffix}"
        file_key = self._generate_file_key(file_id, suffix)

        storage = await self._create_storage(engine)
        bucket = storage.get_default_bucket()
        storage.store(bucket, file_key, data)

        thumbnail = _generate_thumbnail(data, suffix) if suffix in IMAGE_EXTENSIONS else None

        user_id = await self._get_current_user_id(request)
        if user_id is None:
            logger.warning("created_by is None for upload, auth header: %s", request.headers.get("Authorization", "MISSING")[:40])
        download_path = f"{request.base_url}api/v1/sys/file/download?id={file_id}"
        entity = SysFile(
            id=file_id,
            engine=engine,
            bucket=bucket,
            file_key=file_key,
            name=file.filename,
            suffix=suffix,
            size_kb=size_bytes // 1024 if size_bytes > 0 else 0,
            size_info=_format_size(size_bytes),
            obj_name=obj_name,
            storage_path=storage.get_url(bucket, file_key),
            download_path=download_path,
            is_download_auth=0,
            thumbnail=thumbnail,
            created_by=user_id,
        )
        self.dao.insert(entity, user_id=user_id)
        return {
            "id": file_id,
            "name": file.filename,
            "engine": engine,
            "download_path": entity.download_path,
            "size_info": entity.size_info,
        }

    async def download(self, param: FileIdParam):
        entity = self.dao.find_by_id(param.id)
        if not entity:
            raise BusinessException("文件不存在")

        storage = await self._create_storage(entity.engine)
        data = storage.get_bytes(entity.bucket, entity.file_key)
        filename = entity.name or f"{entity.id}{entity.suffix or ''}"

        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename, safe='')}",
                "Content-Length": str(len(data)),
            },
        )

    def page(self, param: FilePageParam) -> dict:
        result = self.dao.find_page_by_filters(param)
        records = result[PageDataField.RECORDS]
        total = result[PageDataField.TOTAL]
        vo_list = []
        for r in records:
            vo = FileVO.model_validate(r).model_dump()
            if vo.get("created_at") and hasattr(vo["created_at"], "strftime"):
                vo["created_at"] = vo["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            vo_list.append(vo)
        from core.db.base_service import batch_enrich_creator_updater
        batch_enrich_creator_updater(vo_list, self.dao.db)
        return page_data(records=vo_list, total=total, page=param.current, size=param.size)

    def detail(self, param: FileIdParam) -> Optional[dict]:
        entity = self.dao.find_by_id(param.id)
        if not entity:
            return None
        vo = FileVO.model_validate(entity).model_dump()
        if vo.get("created_at") and hasattr(vo["created_at"], "strftime"):
            vo["created_at"] = vo["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        from core.db.base_service import enrich_creator_updater
        enrich_creator_updater(vo, self.dao.db)
        return vo

    def remove(self, param):
        self.dao.delete_by_ids(param.ids)

    async def remove_absolute(self, param):
        entities = self.dao.find_by_ids(param.ids)
        storage_cache = {}
        for entity in entities:
            engine = entity.engine
            if engine not in storage_cache:
                storage_cache[engine] = await self._create_storage(entity.engine)
            storage_cache[engine].delete(entity.bucket, entity.file_key)
        self.dao.delete_absolute_by_ids(param.ids)
