from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthDisabledError, AuthenticationError
from app.core.redis_client import get_redis_client
from app.database.models.entities import User
from app.database.session import get_db
from app.schemas.auth import AuthConfigResponse, UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer_scheme = HTTPBearer(auto_error=False)
_OAUTH_STATE_TTL_SECONDS = 600


def get_auth_service() -> AuthService:
    return AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> User:
    """Required-auth dependency: use on routes that must be logged in."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        return await service.get_current_user(session, credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> User | None:
    """Optional-auth dependency: use on routes that work anonymously but
    should personalize/link data when a valid session is present."""
    if credentials is None:
        return None
    try:
        return await service.get_current_user(session, credentials.credentials)
    except AuthenticationError:
        return None


@router.get("/config", response_model=AuthConfigResponse)
async def auth_config(service: AuthService = Depends(get_auth_service)) -> AuthConfigResponse:
    return service.get_config()


@router.get("/login")
async def login(service: AuthService = Depends(get_auth_service)) -> RedirectResponse:
    if not service.is_google_configured():
        raise HTTPException(status_code=400, detail="Google OAuth is not configured; use /auth/dev-login instead.")

    # CSRF protection: a one-time state token, verified (and consumed) on
    # callback. Intentionally NOT best-effort -- if Redis is unreachable,
    # login should fail loudly rather than silently skip CSRF protection.
    state = secrets.token_urlsafe(24)
    await get_redis_client().set(f"oauth_state:{state}", "1", ex=_OAUTH_STATE_TTL_SECONDS)

    return RedirectResponse(service.build_google_login_url(state))


@router.get("/callback")
async def callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    if not service.is_google_configured():
        raise HTTPException(status_code=400, detail="Google OAuth is not configured.")

    redis_client = get_redis_client()
    stored = await redis_client.get(f"oauth_state:{state}")
    if stored is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state.")
    await redis_client.delete(f"oauth_state:{state}")

    _, access_token = await service.handle_google_callback(session, code)
    return RedirectResponse(f"{settings.frontend_url}/?token={access_token}")


@router.get("/dev-login")
async def dev_login(
    email: str = Query(...),
    name: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """Only usable when Google OAuth is NOT configured -- see
    AuthService.dev_login. Required for the app to be runnable locally
    without real Google credentials."""
    try:
        user, access_token = await service.dev_login(session, email=email, name=name)
    except AuthDisabledError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"access_token": access_token, "user": UserRead.model_validate(user)}


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    if credentials is not None:
        await service.logout(credentials.credentials)
    return {"status": "logged_out"}
