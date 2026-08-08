""" Author: Charlie

路径风格公开文件 URL。
"""

from app.platform.storage.url import (
    build_file_access_url,
    normalize_object_name,
    resolve_file_url,
)


def test_build_file_access_url_is_path_style():
    assert (
        build_file_access_url("2026/07/25/a.png", public_path="/api/v1/files", base_url="")
        == "/api/v1/files/2026/07/25/a.png"
    )


def test_normalize_strips_public_path_prefix():
    assert normalize_object_name("/api/v1/files/2026/07/25/a.png") == "2026/07/25/a.png"


def test_resolve_file_url_from_object_name():
    assert resolve_file_url("uploads/a.png", base_url="", public_path="/api/v1/files") == (
        "/api/v1/files/uploads/a.png"
    )
