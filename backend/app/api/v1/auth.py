"""Authentication API routes."""

import logging
import secrets
import time
from typing import Annotated, Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import parse_bearer_token
from app.core.config import get_settings
from app.db.models.auth import AuthProvider
from app.db.session import get_db_session
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth.passwords import PasswordService
from app.services.auth.service import (
    AuthService,
    AuthServiceError,
    DuplicateIdentityError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.services.auth.tokens import TokenService

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _ensure_client_id(provider: str, client_id: str | None) -> str:
    if client_id:
        return client_id
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{provider} OAuth is not configured",
    )


def _build_redirect_url(base_url: str, params: dict[str, str]) -> str:
    return f"{base_url}?{urlencode(params)}"


def _frontend_oauth_redirect(
    *,
    settings: Any,
    provider: str,
    code: str | None,
    state: str | None,
    error: str | None,
    error_description: str | None,
) -> str:
    frontend_login_url = f"{settings.frontend_base_url.rstrip('/')}/login"
    params: dict[str, str] = {
        "oauth_provider": provider,
    }
    if error:
        params["oauth_status"] = "error"
        params["oauth_error"] = error
        if error_description:
            params["oauth_error_description"] = error_description
    elif code:
        params["oauth_status"] = "callback_received"
        params["oauth_code"] = code
        if state:
            params["oauth_state"] = state
    else:
        params["oauth_status"] = "missing_code"
    return _build_redirect_url(frontend_login_url, params)


def _frontend_oauth_success_redirect(
    *, settings: Any, provider: str, access_token: str, refresh_token: str
) -> str:
    frontend_login_url = f"{settings.frontend_base_url.rstrip('/')}/login"
    return _build_redirect_url(
        frontend_login_url,
        {
            "oauth_provider": provider,
            "oauth_status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": "900",
        },
    )


def _state_cookie_name(provider: str) -> str:
    return f"oauth_state_{provider}"


def _with_state_cookie(
    response: RedirectResponse, *, provider: str, state: str
) -> RedirectResponse:
    response.set_cookie(
        key=_state_cookie_name(provider),
        value=state,
        max_age=600,
        httponly=True,
        samesite="lax",
    )
    return response


def _read_and_validate_state(request: Request, *, provider: str, state: str | None) -> bool:
    cookie_state = request.cookies.get(_state_cookie_name(provider))
    return bool(cookie_state and state and cookie_state == state)


def _clear_state_cookie(response: RedirectResponse, *, provider: str) -> RedirectResponse:
    response.delete_cookie(key=_state_cookie_name(provider))
    return response


async def _fetch_github_profile(*, settings: Any, code: str) -> tuple[str, str | None, str]:
    if not settings.github_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth secret is not configured",
        )
    async with httpx.AsyncClient(timeout=20.0) as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_callback_url,
            },
        )
        token_resp.raise_for_status()
        token_payload = token_resp.json()
        access_token = token_payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise HTTPException(status_code=400, detail="GitHub OAuth token exchange failed")

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        user_resp.raise_for_status()
        user_payload = user_resp.json()
        provider_user_key = str(user_payload.get("id", "")).strip()
        if not provider_user_key:
            raise HTTPException(status_code=400, detail="GitHub OAuth user id is missing")
        display_name = str(
            user_payload.get("name") or user_payload.get("login") or provider_user_key
        ).strip()
        email = user_payload.get("email")
        provider_email = str(email).strip() if isinstance(email, str) and email else None

        if provider_email is None:
            emails_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            emails_resp.raise_for_status()
            emails_payload = emails_resp.json()
            if isinstance(emails_payload, list):
                primary_verified = next(
                    (
                        item
                        for item in emails_payload
                        if isinstance(item, dict)
                        and item.get("primary") is True
                        and item.get("verified") is True
                        and item.get("email")
                    ),
                    None,
                )
                fallback_email = next(
                    (
                        item
                        for item in emails_payload
                        if isinstance(item, dict) and item.get("email")
                    ),
                    None,
                )
                selected = primary_verified or fallback_email
                if isinstance(selected, dict):
                    provider_email = str(selected["email"]).strip()

    return provider_user_key, provider_email, display_name


async def _fetch_google_profile(*, settings: Any, code: str) -> tuple[str, str | None, str]:
    if not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth secret is not configured",
        )
    async with httpx.AsyncClient(timeout=20.0) as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.google_callback_url,
            },
        )
        token_resp.raise_for_status()
        token_payload = token_resp.json()
        access_token = token_payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise HTTPException(status_code=400, detail="Google OAuth token exchange failed")

        profile_resp = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_resp.raise_for_status()
        profile_payload = profile_resp.json()
        provider_user_key = str(profile_payload.get("sub", "")).strip()
        if not provider_user_key:
            raise HTTPException(status_code=400, detail="Google OAuth user id is missing")
        email = profile_payload.get("email")
        provider_email = str(email).strip() if isinstance(email, str) and email else None
        display_name = str(
            profile_payload.get("name") or provider_email or provider_user_key
        ).strip()

    return provider_user_key, provider_email, display_name


async def _fetch_microsoft_profile(*, settings: Any, code: str) -> tuple[str, str | None, str]:
    if not settings.microsoft_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Microsoft OAuth secret is not configured",
        )
    tenant_id = settings.microsoft_tenant_id or "common"
    token_endpoint = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_resp = await client.post(
            token_endpoint,
            data={
                "client_id": settings.microsoft_client_id,
                "client_secret": settings.microsoft_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.microsoft_callback_url,
            },
        )
        token_resp.raise_for_status()
        token_payload = token_resp.json()
        access_token = token_payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise HTTPException(status_code=400, detail="Microsoft OAuth token exchange failed")

        profile_resp = await client.get(
            "https://graph.microsoft.com/v1.0/me?$select=id,displayName,mail,userPrincipalName",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_resp.raise_for_status()
        profile_payload = profile_resp.json()
        provider_user_key = str(profile_payload.get("id", "")).strip()
        if not provider_user_key:
            raise HTTPException(status_code=400, detail="Microsoft OAuth user id is missing")
        email = profile_payload.get("mail") or profile_payload.get("userPrincipalName")
        provider_email = str(email).strip() if isinstance(email, str) and email else None
        display_name = str(
            profile_payload.get("displayName") or provider_email or provider_user_key
        ).strip()

    return provider_user_key, provider_email, display_name


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


@router.get("/oauth/github/start")
async def oauth_github_start() -> RedirectResponse:
    settings = get_settings()
    client_id = _ensure_client_id("GitHub", settings.github_client_id)
    state = secrets.token_urlsafe(24)
    auth_url = _build_redirect_url(
        "https://github.com/login/oauth/authorize",
        {
            "client_id": client_id,
            "redirect_uri": settings.github_callback_url,
            "scope": "read:user user:email",
            "state": state,
        },
    )
    response = RedirectResponse(url=auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return _with_state_cookie(response, provider="github", state=state)


@router.get("/oauth/google/start")
async def oauth_google_start() -> RedirectResponse:
    settings = get_settings()
    client_id = _ensure_client_id("Google", settings.google_client_id)
    state = secrets.token_urlsafe(24)
    auth_url = _build_redirect_url(
        "https://accounts.google.com/o/oauth2/v2/auth",
        {
            "client_id": client_id,
            "redirect_uri": settings.google_callback_url,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        },
    )
    response = RedirectResponse(url=auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return _with_state_cookie(response, provider="google", state=state)


@router.get("/oauth/microsoft/start")
async def oauth_microsoft_start() -> RedirectResponse:
    settings = get_settings()
    client_id = _ensure_client_id("Microsoft", settings.microsoft_client_id)
    tenant_id = settings.microsoft_tenant_id or "common"
    state = secrets.token_urlsafe(24)
    auth_url = _build_redirect_url(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize",
        {
            "client_id": client_id,
            "redirect_uri": settings.microsoft_callback_url,
            "response_type": "code",
            "scope": "openid profile email offline_access User.Read",
            "response_mode": "query",
            "state": state,
        },
    )
    response = RedirectResponse(url=auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return _with_state_cookie(response, provider="microsoft", state=state)


@router.get("/oauth/github/callback")
async def oauth_github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    service: Any = Depends(get_auth_service),
) -> RedirectResponse:
    settings = get_settings()
    if error:
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="github",
            code=None,
            state=state,
            error=error,
            error_description=error_description,
        )
        response = RedirectResponse(
            url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
        return _clear_state_cookie(response, provider="github")

    if not _read_and_validate_state(request, provider="github", state=state):
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="github",
            code=None,
            state=state,
            error="invalid_state",
            error_description="OAuth state mismatch",
        )
        response = RedirectResponse(
            url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
        return _clear_state_cookie(response, provider="github")

    if not code:
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="github",
            code=None,
            state=state,
            error="missing_code",
            error_description="Authorization code is missing",
        )
        response = RedirectResponse(
            url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
        return _clear_state_cookie(response, provider="github")

    try:
        provider_user_key, provider_email, display_name = await _fetch_github_profile(
            settings=settings,
            code=code,
        )
        result = await service.oauth_login(
            provider_key=AuthProvider.GITHUB,
            provider_user_key=provider_user_key,
            provider_email=provider_email,
            display_name=display_name,
        )
        redirect_url = _frontend_oauth_success_redirect(
            settings=settings,
            provider="github",
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
        )
    except Exception as exc:
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="github",
            code=None,
            state=state,
            error="oauth_callback_failed",
            error_description=str(exc),
        )

    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return _clear_state_cookie(response, provider="github")


@router.get("/oauth/google/callback")
async def oauth_google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    service: Any = Depends(get_auth_service),
) -> RedirectResponse:
    settings = get_settings()
    if error:
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="google",
            code=None,
            state=state,
            error=error,
            error_description=error_description,
        )
        response = RedirectResponse(
            url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
        return _clear_state_cookie(response, provider="google")

    if not _read_and_validate_state(request, provider="google", state=state):
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="google",
            code=None,
            state=state,
            error="invalid_state",
            error_description="OAuth state mismatch",
        )
        response = RedirectResponse(
            url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
        return _clear_state_cookie(response, provider="google")

    if not code:
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="google",
            code=None,
            state=state,
            error="missing_code",
            error_description="Authorization code is missing",
        )
        response = RedirectResponse(
            url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
        return _clear_state_cookie(response, provider="google")

    try:
        provider_user_key, provider_email, display_name = await _fetch_google_profile(
            settings=settings,
            code=code,
        )
        result = await service.oauth_login(
            provider_key=AuthProvider.GOOGLE,
            provider_user_key=provider_user_key,
            provider_email=provider_email,
            display_name=display_name,
        )
        redirect_url = _frontend_oauth_success_redirect(
            settings=settings,
            provider="google",
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
        )
    except Exception as exc:
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="google",
            code=None,
            state=state,
            error="oauth_callback_failed",
            error_description=str(exc),
        )

    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return _clear_state_cookie(response, provider="google")


@router.get("/oauth/microsoft/callback")
async def oauth_microsoft_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    service: Any = Depends(get_auth_service),
) -> RedirectResponse:
    settings = get_settings()
    if error:
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="microsoft",
            code=None,
            state=state,
            error=error,
            error_description=error_description,
        )
        response = RedirectResponse(
            url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
        return _clear_state_cookie(response, provider="microsoft")

    if not _read_and_validate_state(request, provider="microsoft", state=state):
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="microsoft",
            code=None,
            state=state,
            error="invalid_state",
            error_description="OAuth state mismatch",
        )
        response = RedirectResponse(
            url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
        return _clear_state_cookie(response, provider="microsoft")

    if not code:
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="microsoft",
            code=None,
            state=state,
            error="missing_code",
            error_description="Authorization code is missing",
        )
        response = RedirectResponse(
            url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
        return _clear_state_cookie(response, provider="microsoft")

    try:
        provider_user_key, provider_email, display_name = await _fetch_microsoft_profile(
            settings=settings,
            code=code,
        )
        result = await service.oauth_login(
            provider_key=AuthProvider.MICROSOFT,
            provider_user_key=provider_user_key,
            provider_email=provider_email,
            display_name=display_name,
        )
        redirect_url = _frontend_oauth_success_redirect(
            settings=settings,
            provider="microsoft",
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
        )
    except Exception as exc:
        redirect_url = _frontend_oauth_redirect(
            settings=settings,
            provider="microsoft",
            code=None,
            state=state,
            error="oauth_callback_failed",
            error_description=str(exc),
        )

    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return _clear_state_cookie(response, provider="microsoft")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    service: Any = Depends(get_auth_service),
    x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    try:
        result = await service.register(
            username=request.username,
            email=request.email,
            password=request.password,
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
    except AuthServiceError as e:
        log_auth_event(
            endpoint="/api/v1/auth/register",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            started_at=started_at,
            request_id=x_request_id,
            failure_reason="validation_error",
        )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.post("/login")
async def login(
    request: LoginRequest,
    service: Any = Depends(get_auth_service),
    x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    try:
        result = await service.login(
            identity=request.identity,
            password=request.password,
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


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    authorization: Annotated[str | None, Header()] = None,
    service: Any = Depends(get_auth_service),
    x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> Response:
    started_at = time.perf_counter()
    token = parse_bearer_token(authorization)
    try:
        user = await service.get_current_user(access_token=token)
        await service.delete_account(user_id=user.id)
        log_auth_event(
            endpoint="/api/v1/auth/me",
            status_code=status.HTTP_204_NO_CONTENT,
            started_at=started_at,
            request_id=x_request_id,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except InvalidTokenError as e:
        log_auth_event(
            endpoint="/api/v1/auth/me",
            status_code=status.HTTP_401_UNAUTHORIZED,
            started_at=started_at,
            request_id=x_request_id,
            failure_reason="invalid_token",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
