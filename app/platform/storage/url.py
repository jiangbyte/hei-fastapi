""" Author: Charlie """

from urllib.parse import quote, urljoin, urlparse

from app.platform.module.paths import DEFAULT_FILES_PUBLIC_PATH


def quote_object_name(object_name: str) -> str:
    return "/".join(quote(part) for part in object_name.strip("/").split("/") if part)


def _default_storage_urls() -> tuple[str, str]:
    from app.platform.config.reader import config_reader

    active = config_reader.get_default_storage()
    if active is not None:
        return active.base_url or "", active.public_path or DEFAULT_FILES_PUBLIC_PATH
    return "", DEFAULT_FILES_PUBLIC_PATH


def build_file_access_url(
    object_name: str,
    *,
    base_url: str | None = None,
    public_path: str | None = None,
) -> str:
    """构建公开访问路径：``{public_path}/{object_name}``。"""
    default_base, default_public = _default_storage_urls()
    resolved_base_url = default_base if base_url is None else base_url
    resolved_public_path = default_public if public_path is None else public_path
    path = f"{resolved_public_path.rstrip('/')}/{quote_object_name(object_name)}"
    if resolved_base_url:
        return urljoin(resolved_base_url.rstrip("/") + "/", path.lstrip("/"))
    return path


def is_external_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "data", "blob"}


def normalize_object_name(value: str | None, *, public_path: str | None = None) -> str | None:
    if not value:
        return None
    raw_value = str(value).strip()
    if not raw_value:
        return None
    if is_external_url(raw_value):
        return raw_value

    _, default_public = _default_storage_urls()
    resolved_public_path = (public_path or default_public).rstrip("/")
    path_only = urlparse(raw_value).path if "://" in raw_value else raw_value
    prefix = resolved_public_path + "/"
    if path_only.startswith(prefix):
        return path_only[len(prefix) :].lstrip("/")
    if path_only == resolved_public_path:
        return None
    return path_only.replace("\\", "/").lstrip("/")


def resolve_file_url(
    value: str | None,
    *,
    base_url: str | None = None,
    public_path: str | None = None,
) -> str | None:
    object_name = normalize_object_name(value, public_path=public_path)
    if not object_name:
        return None
    if is_external_url(object_name):
        return object_name
    return build_file_access_url(object_name, base_url=base_url, public_path=public_path)
