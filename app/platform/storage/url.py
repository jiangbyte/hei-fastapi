from urllib.parse import quote, urljoin, urlparse

from app.core.config.settings import settings


def quote_object_name(object_name: str) -> str:
    return "/".join(quote(part) for part in object_name.strip("/").split("/") if part)


def build_file_access_url(
    object_name: str,
    *,
    base_url: str | None = None,
    public_path: str | None = None,
) -> str:
    quoted_name = quote(object_name.strip("/"), safe="/")
    resolved_base_url = settings.storage.base_url if base_url is None else base_url
    resolved_public_path = settings.storage.public_path if public_path is None else public_path
    path = resolved_public_path.rstrip("/")
    query = f"object_name={quoted_name}"
    if resolved_base_url:
        return urljoin(resolved_base_url.rstrip("/") + "/", f"{path.lstrip('/')}?{query}")
    return f"{path}?{query}"


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

    resolved_public_path = public_path or settings.storage.public_path
    path_only = urlparse(raw_value).path if "://" in raw_value else raw_value
    query = urlparse(raw_value).query if "?" in raw_value else ""
    if query:
        from urllib.parse import parse_qs

        object_names = parse_qs(query).get("object_name") or []
        if object_names and object_names[0]:
            return object_names[0].replace("\\", "/").lstrip("/")

    public_prefix = resolved_public_path.rstrip("/") + "/"
    if path_only.startswith(public_prefix):
        return path_only[len(public_prefix) :].lstrip("/")
    # Legacy path-style URLs: /api/v1/files/<object_name>
    bare_prefix = resolved_public_path.rstrip("/")
    if path_only.startswith(bare_prefix + "/") or path_only == bare_prefix:
        remainder = path_only[len(bare_prefix) :].lstrip("/")
        if remainder:
            return remainder

    return raw_value.replace("\\", "/").lstrip("/")

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
