from __future__ import annotations

import hashlib
from services.auth_system.app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hashing_and_verification():
    raw_pass = "super_password_123"
    hashed = hash_password(raw_pass)

    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_sha256_compatibility():
    raw_pass = "secret123"
    sha_hash = hashlib.sha256(raw_pass.encode("utf-8")).hexdigest()

    assert verify_password(raw_pass, sha_hash) is True
    assert verify_password(sha_hash, sha_hash) is True


def test_jwt_token_flow():
    payload = {"hr_id": 42, "login": "test_hr", "full_name": "Тестовый HR"}
    token = create_access_token(payload)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["hr_id"] == 42
    assert decoded["login"] == "test_hr"

    # Невалидный токен
    assert decode_access_token("corrupted.token.value") is None
