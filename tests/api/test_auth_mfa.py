""" Author: Charlie

管理端 MFA 质询 → 会话 cookie。
"""
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config.settings import settings
from app.core.security.session import SessionPayload
from app.factory import create_app
from app.modules.auth.service import LoginOutcome


@pytest.mark.asyncio
async def test_admin_login_mfa_challenge_then_complete(monkeypatch):
    monkeypatch.setattr(settings.auth, "session_cookie_enabled", True)
    monkeypatch.setattr(settings.auth, "session_cookie_name", "hei_session")
    monkeypatch.setattr(settings.swagger, "enabled", False)

    async def _fake_login(self, payload):
        return LoginOutcome(mfa_required=True, challenge_id="challenge-abcdef123456")

    session = SessionPayload(
        token="tok-mfa-1",
        account_id="acc-mfa",
        account_type="ADMIN",
        permission_keys=[],
        password_expired=False,
        remember_me=True,
    )

    async def _fake_mfa(self, payload, *, client_ip=None):
        return session

    monkeypatch.setattr("app.modules.auth.service.AuthService.login", _fake_login)
    monkeypatch.setattr("app.modules.auth.service.AuthService.complete_mfa_login", _fake_mfa)
    monkeypatch.setattr("app.modules.auth.router.verify_captcha", AsyncMock())
    monkeypatch.setattr(
        "app.modules.auth.router.decrypt_password",
        AsyncMock(return_value="plain"),
    )

    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as client:
        first = await client.post(
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
        assert first.status_code == 200
        body = first.json()["data"]
        assert body["mfa_required"] == "true"
        assert body["challenge_id"] == "challenge-abcdef123456"
        assert first.cookies.get("hei_session") is None

        second = await client.post(
            "/api/v1/admin/login/mfa",
            json={"challenge_id": "challenge-abcdef123456", "code": "123456"},
        )
        assert second.status_code == 200
        assert second.json()["data"]["token"] == "tok-mfa-1"
        assert second.cookies.get("hei_session") == "tok-mfa-1"
