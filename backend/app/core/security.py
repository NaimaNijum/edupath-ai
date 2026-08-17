from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import TypedDict

import jwt

from app.core.config import settings

_ALGORITHM = "HS256"


class TokenPayload(TypedDict):
    sub: str  # user id
    jti: str  # unique token id, used for logout blacklisting
    exp: int
    iat: int


class InvalidTokenError(Exception):
    pass


def create_access_token(user_id: str) -> str:
    now = datetime.now(UTC)
    payload: TokenPayload = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expiry_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[_ALGORITHM])  # type: ignore[return-value]
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
