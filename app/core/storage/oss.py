""" Author: Charlie

阿里云 OSS 存储：基于 oss2 SDK 的上传、删除与签名 URL。
"""

from urllib.parse import urljoin

from app.core.storage.config import StorageConfig
from app.core.storage.url import quote_object_name


class OSSStorage:
    """阿里云 OSS 存储引擎。"""

    def __init__(self, config: StorageConfig) -> None:
        import oss2

        self.config = config
        endpoint = config.endpoint.rstrip("/")
        auth = oss2.Auth(config.access_key, config.secret_key)
        self.bucket_name = config.bucket
        self.bucket = oss2.Bucket(auth, endpoint, self.bucket_name)

    def upload_bytes(
        self,
        object_name: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """上传字节内容并返回对象公开 URL。"""
        headers = {"Content-Type": content_type}
        self.bucket.put_object(object_name, content, headers=headers)
        return self.get_object_url(object_name)

    def delete_object(self, object_name: str) -> None:
        """删除对象。"""
        self.bucket.delete_object(object_name)

    def get_object_url(self, object_name: str) -> str:
        """有 base_url 时拼接公开地址，否则生成签名 URL。"""
        if self.config.base_url:
            return urljoin(self.config.base_url.rstrip("/") + "/", quote_object_name(object_name))
        return self.get_presigned_url(object_name)

    def get_presigned_url(self, object_name: str) -> str:
        """生成 GET 签名 URL。"""
        return str(
            self.bucket.sign_url(
                "GET",
                object_name,
                self.config.presign_expire_seconds,
            )
        )
