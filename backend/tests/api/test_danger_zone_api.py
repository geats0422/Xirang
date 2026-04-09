from dataclasses import dataclass
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.auth import get_auth_service
from app.api.v1.settings import get_account_service
from app.main import create_app
from app.schemas.auth import AuthUserResponse


@dataclass
class FakeDangerAuthService:
    deleted_account: bool = False
    cleared_game_data: bool = False

    async def get_current_user(self, *, access_token: str) -> AuthUserResponse:
        return AuthUserResponse(
            id=uuid4(),
            username="DangerUser",
            email="danger@test.com",
            status="active",
        )

    async def delete_account(self, *, user_id) -> None:
        self.deleted_account = True

    async def clear_game_data(self, *, user_id) -> None:
        self.cleared_game_data = True

    async def logout(self, *, access_token: str) -> None:
        pass


def _create_auth_client() -> tuple[TestClient, FakeDangerAuthService]:
    fake = FakeDangerAuthService()
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: fake
    return TestClient(app), fake


def test_delete_account_returns_204() -> None:
    client, fake = _create_auth_client()

    response = client.delete(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer access-token"},
    )

    assert response.status_code == 204
    assert response.content == b""
    assert fake.deleted_account


def test_delete_account_requires_auth() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.delete("/api/v1/auth/me")

    assert response.status_code == 401 or response.status_code == 422


def _create_settings_client() -> tuple[TestClient, FakeDangerAuthService]:
    fake = FakeDangerAuthService()
    app = create_app()
    app.dependency_overrides[get_account_service] = lambda: fake
    from app.api.dependencies.auth import get_current_user_id

    uid = uuid4()
    app.dependency_overrides[get_current_user_id] = lambda: uid
    return TestClient(app), fake


def test_clear_game_data_returns_204() -> None:
    client, fake = _create_settings_client()

    response = client.post("/api/v1/settings/clear-game-data")

    assert response.status_code == 204
    assert response.content == b""
    assert fake.cleared_game_data


def test_logout_endpoint_remains_functional() -> None:
    fake = FakeDangerAuthService()
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer access-token"},
    )

    assert response.status_code == 204
