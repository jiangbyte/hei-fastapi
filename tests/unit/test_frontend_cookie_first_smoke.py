""" Author: Charlie

前端冒烟检查（无浏览器），适合 CI。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_admin_package_has_cookie_first_auth_store():
    auth = (ROOT / "web/admin/src/stores/auth.ts").read_text(encoding="utf-8")
    assert "ensureSession" in auth
    assert "localStorage.setItem(tokenKey" not in auth
    assert "localStorage.setItem('token'" not in auth
    assert "this.token" not in auth


def test_portal_storage_does_not_persist_token():
    storage = (ROOT / "web/portal/src/utils/storage.ts").read_text(encoding="utf-8")
    assert "TOKEN_KEY" not in storage
    assert "function getToken" not in storage
    assert "function setToken" not in storage


def test_admin_axios_attaches_local_token_as_header():
    # 会话采用 Cookie 优先 + Authorization 头兜底双通道：拦截器从本地会话读取 token 附加请求头。
    interceptors = (ROOT / "web/admin/src/utils/axios/request-interceptors.ts").read_text(
        encoding="utf-8"
    )
    assert "getToken()" in interceptors
    assert "config.headers.Authorization = token" in interceptors
    assert "setupRequestInterceptor" in interceptors


def test_biz_services_wire_dept_column():
    for rel in (
        "app/modules/biz/cg_test_order/service.py",
        "app/modules/biz/cg_test_catalog/service.py",
        "app/modules/biz/cg_test_activity/service.py",
        "app/modules/biz/cg_test_knowledge_category/service.py",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "dept_column=getattr(" in text
        assert "owner_dept_id" in text
