"""Auth wiring integration tests - NO dependency overrides."""

from __future__ import annotations

import sys
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app

pytestmark = [
    pytest.mark.asyncio(loop_scope="module"),
    pytest.mark.skipif(sys.platform == "win32", reason="asyncpg event loop instability on Windows"),
]


@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


def _unique_user_payload() -> dict[str, str]:
    suffix = uuid4().hex[:10]
    return {
        "username": f"AuthInt{suffix}",
        "email": f"auth-int-{suffix}@example.com",
        "password": "Secret-pass1!",
    }


def _auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def test_auth_full_flow_register_login_refresh_logout_me(client: AsyncClient) -> None:
    user = _unique_user_payload()

    register_response = await client.post("/api/v1/auth/register", json=user)
    assert register_response.status_code == 201
    register_body = register_response.json()
    assert register_body["user"]["email"] == user["email"]

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"identity": user["email"], "password": user["password"]},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    login_access_token = login_body["tokens"]["access_token"]
    login_refresh_token = login_body["tokens"]["refresh_token"]

    me_ok_response = await client.get("/api/v1/auth/me", headers=_auth_header(login_access_token))
    assert me_ok_response.status_code == 200

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_refresh_token},
    )
    assert refresh_response.status_code == 200
    refresh_body = refresh_response.json()
    rotated_access_token = refresh_body["tokens"]["access_token"]
    rotated_refresh_token = refresh_body["tokens"]["refresh_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout",
        headers=_auth_header(rotated_access_token),
    )
    assert logout_response.status_code == 204

    refresh_after_logout_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated_refresh_token},
    )
    assert refresh_after_logout_response.status_code == 401

    me_after_logout_response = await client.get(
        "/api/v1/auth/me", headers=_auth_header(login_access_token)
    )
    assert me_after_logout_response.status_code == 401


async def test_register_duplicate_returns_409_not_500(client: AsyncClient) -> None:
    user = _unique_user_payload()

    first_response = await client.post("/api/v1/auth/register", json=user)
    assert first_response.status_code == 201

    second_response = await client.post("/api/v1/auth/register", json=user)
    assert second_response.status_code == 409


async def test_me_requires_valid_token(client: AsyncClient) -> None:
    no_token_response = await client.get("/api/v1/auth/me")
    assert no_token_response.status_code == 401

    invalid_token_response = await client.get(
        "/api/v1/auth/me",
        headers=_auth_header("not-a-valid-jwt-token"),
    )
    assert invalid_token_response.status_code == 401
