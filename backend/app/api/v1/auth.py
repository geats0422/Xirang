"""Authentication API routes."""

import logging
import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import parse_bearer_token
from app.core.config import get_settings
from app.db.session import get_db_session
from app.repositories.auth_repository import AuthRepository
from app.services.auth.passwords import PasswordService
from app.services.auth.service import (
    AuthService,
    DuplicateIdentityError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.services.auth.tokens import TokenService

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def log_auth_event(
    *,
    endpoint: str,
    status_code: int,
    started_at: float,
    request_id: str | None,
    failure_reason: str | None = None,
) -> None:
    latency_ms = int((time.perf_counter() - started_at) * 1000)
    base = (
        f"endpoint={endpoint} status_code={status_code} latency_ms={latency_ms} "
        f"request_id={request_id or '-'}"
    )
    if failure_reason is None:
        logger.info("auth_request %s", base)
        return

    logger.warning("auth_request %s failure_reason=%s", base, failure_reason)


async def get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    settings = get_settings()
    token_service = TokenService(
        secret_key=settings.secret_key,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
        algorithm=settings.jwt_algorithm,
    )
    return AuthService(
        repository=AuthRepository(session),
        password_service=PasswordService(),
        token_service=token_service,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: dict[str, Any],
    service: Any = Depends(get_auth_service),
    x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> dict[str, Any]:
    """Register a new user."""
    started_at = time.perf_counter()
    try:
        result = await service.register(
            username=request.get("username", ""),
            email=request.get("email", ""),
            password=request.get("password", ""),
        )
        log_auth_event(
            endpoint="/api/v1/auth/register",
            status_code=status.HTTP_201_CREATED,
            started_at=started_at,
            request_id=x_request_id,
        )
        return {
            "user": {
                "id": str(result.user.id),
                "username": result.user.username,
                "email": result.user.email,
                "status": result.user.status,
            },
            "tokens": {
                "access_token": result.tokens.access_token,
                "refresh_token": result.tokens.refresh_token,
                "token_type": "bearer",
                "expires_in": 900,
            },
        }
    except DuplicateIdentityError as e:
        log_auth_event(
            endpoint="/api/v1/auth/register",
            status_code=status.HTTP_409_CONFLICT,
            started_at=started_at,
            request_id=x_request_id,
            failure_reason="duplicate_identity",
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post("/login")
async def login(
    request: dict[str, Any],
    service: Any = Depends(get_auth_service),
    x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> dict[str, Any]:
    """Login user."""
    started_at = time.perf_counter()
    try:
        result = await service.login(
            identity=request.get("identity", ""),
            password=request.get("password", ""),
        )
        log_auth_event(
            endpoint="/api/v1/auth/login",
            status_code=status.HTTP_200_OK,
            started_at=started_at,
            request_id=x_request_id,
        )
        return {
            "user": {
                "id": str(result.user.id),
                "username": result.user.username,
                "email": result.user.email,
                "status": result.user.status,
            },
            "tokens": {
                "access_token": result.tokens.access_token,
                "refresh_token": result.tokens.refresh_token,
                "token_type": "bearer",
                "expires_in": 900,
            },
        }
    except InvalidCredentialsError as e:
        log_auth_event(
            endpoint="/api/v1/auth/login",
            status_code=status.HTTP_401_UNAUTHORIZED,
            started_at=started_at,
            request_id=x_request_id,
            failure_reason="invalid_credentials",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


@router.post("/refresh")
async def refresh(
    request: dict[str, Any],
    service: Any = Depends(get_auth_service),
    x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> dict[str, Any]:
    """Refresh tokens."""
    started_at = time.perf_counter()
    try:
        result = await service.refresh(refresh_token=request.get("refresh_token", ""))
        tokens = result.tokens if hasattr(result, "tokens") else result
        log_auth_event(
            endpoint="/api/v1/auth/refresh",
            status_code=status.HTTP_200_OK,
            started_at=started_at,
            request_id=x_request_id,
        )
        return {
            "tokens": {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": getattr(tokens, "token_type", "bearer"),
                "expires_in": getattr(tokens, "expires_in", 900),
            }
        }
    except InvalidTokenError as e:
        log_auth_event(
            endpoint="/api/v1/auth/refresh",
            status_code=status.HTTP_401_UNAUTHORIZED,
            started_at=started_at,
            request_id=x_request_id,
            failure_reason="invalid_token",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


@router.post("/logout")
async def logout(
    authorization: Annotated[str | None, Header()] = None,
    service: Any = Depends(get_auth_service),
    x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> Response:
    """Logout user."""
    started_at = time.perf_counter()
    token = parse_bearer_token(authorization)
    await service.logout(access_token=token)
    log_auth_event(
        endpoint="/api/v1/auth/logout",
        status_code=status.HTTP_204_NO_CONTENT,
        started_at=started_at,
        request_id=x_request_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me")
async def get_me(
    authorization: Annotated[str | None, Header()] = None,
    service: Any = Depends(get_auth_service),
    x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> dict[str, Any]:
    """Get current user."""
    started_at = time.perf_counter()
    token = parse_bearer_token(authorization)
    try:
        user = await service.get_current_user(access_token=token)
        log_auth_event(
            endpoint="/api/v1/auth/me",
            status_code=status.HTTP_200_OK,
            started_at=started_at,
            request_id=x_request_id,
        )
        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "status": user.status,
        }
    except InvalidTokenError as e:
        log_auth_event(
            endpoint="/api/v1/auth/me",
            status_code=status.HTTP_401_UNAUTHORIZED,
            started_at=started_at,
            request_id=x_request_id,
            failure_reason="invalid_token",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
