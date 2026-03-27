from typing import Annotated
from uuid import UUID

from fastapi import Header, HTTPException, status

from app.core.config import get_settings
from app.services.auth.tokens import TokenService


def parse_bearer_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization",
        )
    return token.strip()


def get_current_user_id(
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> UUID:
    _ = x_user_id
    token = parse_bearer_token(authorization)

    settings = get_settings()
    token_service = TokenService(
        secret_key=settings.secret_key,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
        algorithm=settings.jwt_algorithm,
    )

    try:
        payload = token_service.decode_token(token, expected_token_type="access")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e

    return payload.user_id
