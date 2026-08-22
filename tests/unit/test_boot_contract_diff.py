"""Unit tests for boot vs fastapi OpenAPI path diff helpers."""

from scripts.e2e.boot_contract_diff import collect_operations, diff_openapi


def test_collect_operations_normalizes_api_prefix() -> None:
    doc = {
        "paths": {
            "/v1/public/site-footer": {"get": {}},
            "/api/v1/admin/workspace/overview": {"get": {}},
        }
    }
    ops = collect_operations(doc)
    assert ("GET", "/api/v1/public/site-footer") in ops
    assert ("GET", "/api/v1/admin/workspace/overview") in ops


def test_diff_openapi_reports_symmetric_gaps() -> None:
    boot = {"paths": {"/api/v1/a": {"get": {}}}}
    fast = {"paths": {"/api/v1/b": {"post": {}}}}
    result = diff_openapi(boot, fast)
    assert result["only_boot"] == ["GET /api/v1/a"]
    assert result["only_fastapi"] == ["POST /api/v1/b"]
