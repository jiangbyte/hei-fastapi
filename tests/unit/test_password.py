""" Author: Charlie """

from app.core.security.password import hash_password, verify_password


def test_hash_password_uses_bcrypt() -> None:
    hashed = hash_password("123456789")

    assert hashed.startswith("$2b$")
    assert verify_password("123456789", hashed)
    assert not verify_password("wrong-password", hashed)


def test_verify_password_rejects_non_bcrypt_hash() -> None:
    assert not verify_password(
        "123456789",
        "$pbkdf2-sha256$29000$9F4rZWxtTQkBoHROKWUsRQ$gTUk2O4CMqpmvYVGc5e9.SuCERJnkSefgRbjNtJEfpE",
    )
