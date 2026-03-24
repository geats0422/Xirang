from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.auth import get_auth_service
from app.main import create_app
from app.schemas.auth import AuthTokensResponse, AuthUserResponse, AuthWithUserResponse
from app.services.auth.service import DuplicateIdentityError, InvalidCredentialsError


@dataclass
class FakeApiAuthService:
    async def register(self, *, username: str, email: str, password: str) -> AuthWithUserResponse:
        if email == "dupe@example.com":
            raise DuplicateIdentityError("Email already registered")
        return self._success(username=username, email=email)

    async def login(self, *, identity: str, password: str) -> AuthWithUserResponse:
        if password == "bad-pass":
            raise InvalidCredentialsError("Invalid credentials")
        return self._success(username="Hero", email="hero@example.com")

    async def refresh(self, *, refresh_token: str) -> AuthWithUserResponse:
        return self._success(username="Hero", email="hero@example.com")

    async def logout(self, *, access_token: str) -> None:
        return None

    async def get_current_user(self, *, access_token: str) -> AuthUserResponse:
        return AuthUserResponse(
            id=uuid4(),
            username="Hero",
            email="hero@example.com",
            status="active",
        )

    def _success(self, *, username: str, email: str) -> AuthWithUserResponse:
        return AuthWithUserResponse(
            user=AuthUserResponse(id=uuid4(), username=username, email=email, status="active"),
            tokens=AuthTokensResponse(
                access_token="access-token",
                refresh_token="refresh-token",
                token_type="bearer",
                expires_in=900,
            ),
        )


def create_test_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: FakeApiAuthService()
    return TestClient(app)


def test_register_endpoint_returns_created_auth_payload() -> None:
    client = create_test_client()

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "Hero", "email": "hero@example.com", "password": "secret-pass"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "hero@example.com"
    assert body["tokens"]["access_token"] == "access-token"


def test_register_endpoint_maps_duplicate_identity_to_conflict() -> None:
    client = create_test_client()

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "Hero", "email": "dupe@example.com", "password": "secret-pass"},
    )

    assert response.status_code == 409


def test_login_endpoint_returns_auth_payload() -> None:
    client = create_test_client()

    response = client.post(
        "/api/v1/auth/login",
        json={"identity": "hero@example.com", "password": "secret-pass"},
    )

    assert response.status_code == 200
    assert response.json()["tokens"]["refresh_token"] == "refresh-token"


def test_login_endpoint_maps_invalid_credentials_to_unauthorized() -> None:
    client = create_test_client()

    response = client.post(
        "/api/v1/auth/login",
        json={"identity": "hero@example.com", "password": "bad-pass"},
    )

    assert response.status_code == 401


def test_refresh_endpoint_returns_rotated_tokens() -> None:
    client = create_test_client()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "refresh-token"})

    assert response.status_code == 200
    assert response.json()["tokens"]["token_type"] == "bearer"


def test_logout_endpoint_returns_no_content() -> None:
    client = create_test_client()

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer access-token"},
    )

    assert response.status_code == 204
    assert response.content == b""


def test_me_endpoint_returns_current_user() -> None:
    client = create_test_client()

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer access-token"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "Hero"
