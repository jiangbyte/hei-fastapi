""" Author: Charlie

OpenAPI 完整性：每个 operation 应有可校验的 200 JSON schema（二进制下载除外）。
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SWAGGER__ENABLED", "true")

from app.factory import create_app  # noqa: E402
from scripts.e2e.contract import has_json_200, iter_operations  # noqa: E402

_BINARY_SUFFIXES = ("/download",)


@pytest.fixture(scope="module")
def openapi_doc() -> dict:
    app = create_app()
    return app.openapi()


def test_openapi_operations_have_json_200(openapi_doc: dict) -> None:
    missing: list[str] = []
    for item in iter_operations(openapi_doc):
        path = item["path"]
        if any(path.endswith(s) for s in _BINARY_SUFFIXES):
            continue
        if not has_json_200(openapi_doc, item["operation"]):
            missing.append(f"{item['method']} {path}")
    assert not missing, "missing application/json 200 schema:\n" + "\n".join(missing)


def test_openapi_auth_code_endpoints_documented(openapi_doc: dict) -> None:
    paths = openapi_doc.get("paths") or {}
    for path in (
        "/api/v1/admin/send-login-code",
        "/api/v1/portal/send-login-code",
        "/api/v1/portal/register/send-code",
        "/api/v1/admin/forgot-password",
        "/api/v1/admin/reset-password",
        "/api/v1/portal/forgot-password",
        "/api/v1/portal/reset-password",
    ):
        op = (paths.get(path) or {}).get("post") or {}
        assert has_json_200(openapi_doc, op), path
