""" Author: Charlie

登录设置 HttpOnly 会话 cookie（cookie 优先 Web 会话）。
"""
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config.settings import settings
from app.core.security.session import SessionPayload
from app.factory import create_app
from app.modules.auth.service import LoginOutcome


@pytest.mark.asyncio
async def test_admin_login_sets_session_cookie(monkeypatch):
    monkeypatch.setattr(settings.auth, "session_cookie_enabled", True)
    monkeypatch.setattr(settings.auth, "session_cookie_name", "hei_session")
    monkeypatch.setattr(settings.swagger, "enabled", False)

    session = SessionPayload(
        token="tok-cookie-1",
        account_id="acc-1",
        account_type="ADMIN",
        permission_keys=[],
        password_expired=False,
    )

    async def _fake_login(self, payload):
        return LoginOutcome(session=session)

    monkeypatch.setattr(
        "app.modules.auth.service.AuthService.login",
        _fake_login,
    )
    monkeypatch.setattr(
        "app.modules.auth.router.verify_captcha",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.modules.auth.router.decrypt_password",
        AsyncMock(return_value="plain"),
    )

    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/admin/login",
            json={
                "account": "admin",
                "password": "x",
                "identity_type": "ACCOUNT",
                "remember_me": True,
                "password_key_id": "k",
                "captcha_id": "c",
                "captcha_value": "1",
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["token"] == "tok-cookie-1"
    cookie = response.cookies.get("hei_session")
    assert cookie == "tok-cookie-1"
