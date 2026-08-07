""" Author: Charlie

IM 短期 AUTH 票据。
"""
import pytest

from app.modules.message.im import auth as im_auth


@pytest.mark.asyncio
async def test_im_ticket_issue_and_consume_once(fake_redis, monkeypatch):
    monkeypatch.setattr(im_auth.settings.auth, "im_ticket_ttl_seconds", 60)
    ticket, ttl = await im_auth.issue_im_ticket(account_type="ADMIN", account_id="acc-1")
    assert ttl == 60
    assert ticket.startswith("imt_")

    first = await im_auth.auth_token(ticket)
    assert first == ("ADMIN", "acc-1")

    # 一次性：第二次消费失败
    second = await im_auth.auth_token(ticket)
    assert second is None


@pytest.mark.asyncio
async def test_im_ticket_requires_redis(monkeypatch):
    monkeypatch.setattr(im_auth, "get_redis", lambda: None)
    with pytest.raises(RuntimeError, match="Redis"):
        await im_auth.issue_im_ticket(account_type="ADMIN", account_id="acc-1")
