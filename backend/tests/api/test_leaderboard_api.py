from dataclasses import dataclass
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user_id
from app.api.v1.leaderboard import get_leaderboard_service
from app.main import create_app
from app.schemas.leaderboard import (
    DailyFocusItemResponse,
    LeaderboardEntryResponse,
    LeaderboardListResponse,
    LeaderboardViewerSummaryResponse,
)


@dataclass
class FakeLeaderboardService:
    expected_user_id: UUID
    last_call: dict[str, object] | None = None

    async def get_global_leaderboard(
        self,
        *,
        user_id: UUID,
        limit: int = 25,
        offset: int = 0,
        scope: str = "global",
    ) -> LeaderboardListResponse:
        self.last_call = {
            "user_id": user_id,
            "limit": limit,
            "offset": offset,
            "scope": scope,
        }
        return LeaderboardListResponse(
            scope=scope,
            limit=limit,
            offset=offset,
            has_more=True,
            entries=[
                LeaderboardEntryResponse(
                    user_id=UUID("00000000-0000-0000-0000-000000000011"),
                    display_name="Scholar One",
                    total_xp=2600,
                    rank=offset + 1,
                    level=6,
                    energy_points=0,
                    is_current_user=False,
                )
            ],
            viewer=LeaderboardViewerSummaryResponse(
                user_id=user_id,
                display_name="Viewer User",
                total_xp=1800,
                rank=7,
                level=4,
                energy_points=2,
                daily_focus=[
                    DailyFocusItemResponse(
                        document_id=UUID("00000000-0000-0000-0000-000000000123"),
                        title="The Art of War",
                        progress_current=3,
                        progress_total=5,
                        progress_text="3/5",
                    )
                ],
            ),
        )


def create_test_client(fake_service: FakeLeaderboardService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_leaderboard_service] = lambda: fake_service
    app.dependency_overrides[get_current_user_id] = lambda: fake_service.expected_user_id
    return TestClient(app)


def test_list_leaderboard_returns_snapshot_payload() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000099")
    service = FakeLeaderboardService(expected_user_id=user_id)
    client = create_test_client(service)

    response = client.get("/api/v1/leaderboard?limit=10&offset=20&scope=friends")

    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "friends"
    assert body["limit"] == 10
    assert body["offset"] == 20
    assert body["has_more"] is True
    assert body["viewer"]["display_name"] == "Viewer User"
    assert body["viewer"]["rank"] == 7
    assert body["viewer"]["daily_focus"][0]["progress_text"] == "3/5"
    assert body["entries"][0]["display_name"] == "Scholar One"
    assert service.last_call == {
        "user_id": user_id,
        "limit": 10,
        "offset": 20,
        "scope": "friends",
    }


def test_list_leaderboard_uses_default_query_values() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000088")
    service = FakeLeaderboardService(expected_user_id=user_id)
    client = create_test_client(service)

    response = client.get("/api/v1/leaderboard")

    assert response.status_code == 200
    assert service.last_call is not None
    assert service.last_call["limit"] == 25
    assert service.last_call["offset"] == 0
    assert service.last_call["scope"] == "global"


def test_leaderboard_health_endpoint_returns_ok() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000077")
    service = FakeLeaderboardService(expected_user_id=user_id)
    client = create_test_client(service)

    response = client.get("/api/v1/leaderboard/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
