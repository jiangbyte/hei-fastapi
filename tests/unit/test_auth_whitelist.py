""" Author: Charlie """

from app.core.security.auth_whitelist import (
    BUILTIN_AUTH_WHITELIST,
    clear_auth_whitelist_cache,
    is_auth_whitelisted,
)


def test_builtin_whitelist_matches_login_and_health():
    clear_auth_whitelist_cache()
    assert is_auth_whitelisted("/api/v1/admin/login")
    assert is_auth_whitelisted("/api/v1/portal/captcha")
    assert is_auth_whitelisted("/api/v1/internal/health/live")
    assert is_auth_whitelisted("/api/v1/files")
    assert is_auth_whitelisted("/api/v1/portal/sys/banners/list")
    assert not is_auth_whitelisted("/api/v1/admin/sys/banners/create")


def test_configured_whitelist_extends_builtin(monkeypatch):
    clear_auth_whitelist_cache()
    monkeypatch.setattr(
        "app.core.security.auth_whitelist.settings.auth.auth_whitelist",
        ["/api/v1/custom/*"],
        raising=False,
    )
    # settings.auth 为嵌套模型 — 通过 object patch
    from app.core.config.settings import settings

    monkeypatch.setattr(settings.auth, "auth_whitelist", ["/api/v1/custom/*"])
    clear_auth_whitelist_cache()
    assert is_auth_whitelisted("/api/v1/custom/foo")
    assert is_auth_whitelisted("/api/v1/admin/login")
    clear_auth_whitelist_cache()


def test_builtin_whitelist_nonempty():
    assert len(BUILTIN_AUTH_WHITELIST) > 10
