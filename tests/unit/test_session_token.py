""" Author: Charlie

会话 token 提取：cookie 优先，无 Bearer 方案。
"""
from unittest.mock import MagicMock

from app.core.config.settings import settings
from app.core.security.session_token import extract_session_token


def test_extract_prefers_cookie_over_authorization(monkeypatch):
    monkeypatch.setattr(settings.auth, "session_cookie_enabled", True)
    monkeypatch.setattr(settings.auth, "session_cookie_name", "hei_session")
    monkeypatch.setattr(settings.auth, "token_name", "Authorization")

    request = MagicMock()
    request.cookies = {"hei_session": "cookie-token"}
    request.headers = {"Authorization": "header-token"}

    assert extract_session_token(request) == "cookie-token"


def test_extract_rejects_bearer_scheme(monkeypatch):
    monkeypatch.setattr(settings.auth, "session_cookie_enabled", True)
    monkeypatch.setattr(settings.auth, "session_cookie_name", "hei_session")
    monkeypatch.setattr(settings.auth, "token_name", "Authorization")

    request = MagicMock()
    request.cookies = {}
    request.headers = {"Authorization": "Bearer legacy-jwt"}

    assert extract_session_token(request) is None
    assert extract_session_token(request, "Bearer legacy-jwt") is None


def test_extract_raw_authorization_for_native(monkeypatch):
    monkeypatch.setattr(settings.auth, "session_cookie_enabled", True)
    monkeypatch.setattr(settings.auth, "session_cookie_name", "hei_session")
    monkeypatch.setattr(settings.auth, "token_name", "Authorization")

    request = MagicMock()
    request.cookies = {}
    request.headers = {"Authorization": "opaque-session-token"}

    assert extract_session_token(request) == "opaque-session-token"
