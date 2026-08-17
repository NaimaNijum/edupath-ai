from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urlencode
from uuid import UUID

import httpx
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthDisabledError, AuthenticationError
from app.core.redis_client import get_redis_client
from app.core.security import InvalidTokenError, create_access_token, decode_access_token
from app.database.models.entities import User
from app.repositories.user import UserRepository
from app.schemas.auth import AuthConfigResponse

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class AuthService:
    def __init__(self, repository: UserRepository | None = None) -> None:
        self._repository = repository or UserRepository()

    def is_google_configured(self) -> bool:
        return bool(settings.google_client_id and settings.google_client_secret)

    def get_config(self) -> AuthConfigResponse:
        if self.is_google_configured():
            return AuthConfigResponse(mode="google", google_login_url="/api/v1/auth/login")
        return AuthConfigResponse(mode="dev-mock")

    def build_google_login_url(self, state: str) -> str:
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }
        return f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def handle_google_callback(self, session: AsyncSession, code: str) -> tuple[User, str]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_response = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            tokens = token_response.json()

        # Verifies signature, issuer, audience, and expiry against Google's
        # public keys -- never trust the id_token payload without this.
        id_info = id_token.verify_oauth2_token(
            tokens["id_token"], google_requests.Request(), settings.google_client_id
        )

        google_sub = id_info["sub"]
        email = id_info["email"]
        name = id_info.get("name")
        avatar_url = id_info.get("picture")

        user = await self._repository.get_by_google_sub(session, google_sub)
        if user is None:
            # A dev-mock user with this email may already exist; link it to
            # the real Google account instead of creating a duplicate.
            user = await self._repository.get_by_email(session, email)
        if user is None:
            user = await self._repository.create(
                session, User(google_sub=google_sub, email=email, name=name, avatar_url=avatar_url)
            )
        else:
            user.google_sub = google_sub
            user.name = name or user.name
            user.avatar_url = avatar_url or user.avatar_url
            user = await self._repository.update(session, user)

        return user, create_access_token(str(user.id))

    async def dev_login(self, session: AsyncSession, *, email: str, name: str | None) -> tuple[User, str]:
        if self.is_google_configured():
            raise AuthDisabledError("Dev-mock login is disabled while real Google OAuth is configured.")

        user = await self._repository.get_by_email(session, email)
        if user is None:
            user = await self._repository.create(session, User(google_sub=None, email=email, name=name))
        return user, create_access_token(str(user.id))

    async def get_current_user(self, session: AsyncSession, token: str) -> User:
        try:
            payload = decode_access_token(token)
        except InvalidTokenError as exc:
            raise AuthenticationError("Invalid or expired session.") from exc

        if await self._is_blacklisted(payload["jti"]):
            raise AuthenticationError("Session has been revoked.")

        user = await self._repository.get(session, UUID(payload["sub"]))
        if user is None:
            raise AuthenticationError("User account no longer exists.")
        return user

    async def logout(self, token: str) -> None:
        try:
            payload = decode_access_token(token)
        except InvalidTokenError:
            return  # already invalid/expired -- nothing to revoke
        ttl_seconds = max(payload["exp"] - int(datetime.now(UTC).timestamp()), 1)
        try:
            await get_redis_client().set(f"jwt_blacklist:{payload['jti']}", "1", ex=ttl_seconds)
        except Exception:
            # Best-effort: if Redis is down, the token still expires on its
            # own via jwt_expiry_minutes -- logout failing silently here is
            # better than a 500 for a background cleanup step.
            pass

    async def _is_blacklisted(self, jti: str) -> bool:
        try:
            return bool(await get_redis_client().exists(f"jwt_blacklist:{jti}"))
        except Exception:
            # Fail open on infra hiccups -- token expiry is still the real
            # security bound; don't lock every user out because Redis blipped.
            return False
