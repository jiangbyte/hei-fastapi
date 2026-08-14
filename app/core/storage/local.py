""" Author: Charlie

本地文件存储：基于磁盘目录的存储引擎，支持路径安全校验与公开 URL 构建。
"""

import sys
from pathlib import Path

from app.core.config.settings import PROJECT_ROOT
from app.core.storage.config import DEFAULT_LOCAL_STORAGE_ROOT, StorageConfig
from app.core.storage.url import build_file_access_url


def _resolve_local_root(config: StorageConfig | None, fallback: str) -> str:
    """解析本地根目录：Windows 优先 windows_root，否则用 local_root 或回退值。"""
    if config is None:
        return fallback
    if sys.platform.startswith("win") and (config.windows_root or "").strip():
        return config.windows_root.strip()
    return (config.local_root or "").strip() or fallback


class LocalStorage:
    """本地磁盘存储引擎，对象名映射为根目录下的相对路径。"""

    def __init__(
        self,
        config: StorageConfig | None = None,
        root: str = DEFAULT_LOCAL_STORAGE_ROOT,
    ) -> None:
        self.config = config
        root = _resolve_local_root(config, root)
        root_path = Path(root)
        self.root = root_path if root_path.is_absolute() else PROJECT_ROOT / root_path
        self.root = self.root.resolve()

    def upload_bytes(
        self,
        object_name: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """写入字节内容并返回对象公开 URL。"""
        _ = content_type
        target = self.get_path(object_name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return self.get_object_url(object_name)

    def delete_object(self, object_name: str) -> None:
        """删除本地对象文件（不存在则忽略）。"""
        target = self.get_path(object_name)
        if target.exists():
            target.unlink()

    def get_object_url(self, object_name: str) -> str:
        """构建对象公开访问 URL。"""
        if self.config is None:
            return build_file_access_url(object_name)
        return build_file_access_url(
            object_name,
            base_url=self.config.base_url,
            public_path=self.config.public_path,
        )

    def get_presigned_url(self, object_name: str) -> str:
        """本地存储无签名 URL，直接返回公开 URL。"""
        return self.get_object_url(object_name)

    def get_path(self, object_name: str) -> Path:
        """把对象名解析为绝对路径并做越界校验。"""
        target = (self.root / object_name).resolve()
        if target != self.root and self.root not in target.parents:
            raise ValueError("Invalid object name")
        return target
