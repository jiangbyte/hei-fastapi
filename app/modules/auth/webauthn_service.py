""" Author: Charlie

管理端 MFA 的 WebAuthn 辅助工具。
"""
from __future__ import annotations

import json
from typing import Any

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.core.config.settings import settings
from app.core.exceptions.business import AuthenticationError, BusinessError
from app.modules.iam.account.model import SysAccount
from app.platform.cache.redis import get_redis

_REG_CHALLENGE_PREFIX = "auth:webauthn_reg:"
_AUTH_CHALLENGE_PREFIX = "auth:webauthn_auth:"


def _redis():
    redis = get_redis()
    if redis is None:
        raise BusinessError("Redis is required for WebAuthn")
    return redis


def load_credentials(account: SysAccount) -> list[dict[str, Any]]:
    raw = account.webauthn_credentials_json
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def dump_credentials(credentials: list[dict[str, Any]]) -> str:
    return json.dumps(credentials)


async def begin_registration(account: SysAccount) -> dict[str, Any]:
    existing = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(item["credential_id"]))
        for item in load_credentials(account)
        if item.get("credential_id")
    ]
    options = generate_registration_options(
        rp_id=settings.auth.webauthn_rp_id,
        rp_name=settings.auth.webauthn_rp_name,
        user_id=account.id.encode("utf-8"),
        user_name=account.id,
        user_display_name=account.id,
        exclude_credentials=existing,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    redis = _redis()
    await redis.set(
        f"{_REG_CHALLENGE_PREFIX}{account.id}",
        bytes_to_base64url(options.challenge),
        ex=settings.auth.mfa_challenge_ttl_seconds,
    )
    return json.loads(options_to_json(options))


async def complete_registration(account: SysAccount, credential: dict[str, Any]) -> None:
    redis = _redis()
    raw = await redis.getdel(f"{_REG_CHALLENGE_PREFIX}{account.id}")
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode()
    if not raw:
        raise BusinessError("WebAuthn registration challenge expired")
    expected = base64url_to_bytes(str(raw))
    verification = verify_registration_response(
        credential=credential,
        expected_challenge=expected,
        expected_rp_id=settings.auth.webauthn_rp_id,
        expected_origin=settings.auth.webauthn_origin,
    )
    credentials = load_credentials(account)
    credentials.append(
        {
            "credential_id": bytes_to_base64url(verification.credential_id),
            "public_key": bytes_to_base64url(verification.credential_public_key),
            "sign_count": int(verification.sign_count),
        }
    )
    account.webauthn_credentials_json = dump_credentials(credentials)
    account.mfa_enabled = True
    if account.mfa_enabled_at is None:
        from datetime import UTC, datetime

        account.mfa_enabled_at = datetime.now(UTC)


async def begin_authentication(account: SysAccount) -> dict[str, Any] | None:
    credentials = load_credentials(account)
    if not credentials:
        return None
    allow = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(item["credential_id"]))
        for item in credentials
        if item.get("credential_id")
    ]
    options = generate_authentication_options(
        rp_id=settings.auth.webauthn_rp_id,
        allow_credentials=allow,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    redis = _redis()
    await redis.set(
        f"{_AUTH_CHALLENGE_PREFIX}{account.id}",
        bytes_to_base64url(options.challenge),
        ex=settings.auth.mfa_challenge_ttl_seconds,
    )
    return json.loads(options_to_json(options))


async def complete_authentication(account: SysAccount, credential: dict[str, Any]) -> None:
    redis = _redis()
    raw = await redis.getdel(f"{_AUTH_CHALLENGE_PREFIX}{account.id}")
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode()
    if not raw:
        raise AuthenticationError("WebAuthn authentication challenge expired")
    expected = base64url_to_bytes(str(raw))
    credentials = load_credentials(account)
    cred_id = credential.get("id") or credential.get("rawId")
    stored = next((c for c in credentials if c.get("credential_id") == cred_id), None)
    if stored is None:
        raise AuthenticationError("Unknown WebAuthn credential")
    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=expected,
        expected_rp_id=settings.auth.webauthn_rp_id,
        expected_origin=settings.auth.webauthn_origin,
        credential_public_key=base64url_to_bytes(stored["public_key"]),
        credential_current_sign_count=int(stored.get("sign_count") or 0),
    )
    stored["sign_count"] = int(verification.new_sign_count)
    account.webauthn_credentials_json = dump_credentials(credentials)


def account_has_webauthn(account: SysAccount) -> bool:
    return bool(load_credentials(account))
