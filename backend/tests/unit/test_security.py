from __future__ import annotations

import time

import jwt
import pytest

from app.core.security import InvalidTokenError, create_access_token, decode_access_token


def test_create_and_decode_round_trip():
    token = create_access_token("11111111-1111-1111-1111-111111111111")
    payload = decode_access_token(token)

    assert payload["sub"] == "11111111-1111-1111-1111-111111111111"
    assert "jti" in payload
    assert payload["exp"] > payload["iat"]


def test_two_tokens_for_same_user_have_different_jti():
    token1 = create_access_token("user-1")
    token2 = create_access_token("user-1")

    assert decode_access_token(token1)["jti"] != decode_access_token(token2)["jti"]


def test_decode_rejects_garbage_token():
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-real-token")


def test_decode_rejects_expired_token():
    from app.core.config import settings

    expired_payload = {
        "sub": "user-1",
        "jti": "abc",
        "iat": int(time.time()) - 7200,
        "exp": int(time.time()) - 3600,
    }
    expired_token = jwt.encode(expired_payload, settings.jwt_secret_key, algorithm="HS256")

    with pytest.raises(InvalidTokenError):
        decode_access_token(expired_token)


def test_decode_rejects_token_signed_with_wrong_secret():
    forged = jwt.encode({"sub": "user-1", "jti": "x", "iat": 0, "exp": 9999999999}, "wrong-secret", algorithm="HS256")

    with pytest.raises(InvalidTokenError):
        decode_access_token(forged)
