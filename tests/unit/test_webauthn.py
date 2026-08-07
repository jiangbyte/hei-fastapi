""" Author: Charlie

WebAuthn 凭证存储辅助函数。
"""
from app.modules.auth.webauthn_service import (
    account_has_webauthn,
    dump_credentials,
    load_credentials,
)
from app.modules.iam.account.model import SysAccount


def test_load_dump_credentials_roundtrip():
    account = SysAccount(webauthn_credentials_json=None)
    assert load_credentials(account) == []
    assert not account_has_webauthn(account)

    payload = [{"id": "abc", "public_key": "pk", "sign_count": 1}]
    account.webauthn_credentials_json = dump_credentials(payload)
    assert load_credentials(account) == payload
    assert account_has_webauthn(account)
