from datetime import UTC, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.services.leaderboard.service import LeaderboardService

BEIJING_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


class TestLeaderboardServiceFocusTitle:
    def test_resolve_focus_title_keeps_meaningful_title(self) -> None:
        result = LeaderboardService._resolve_focus_title("python简介、基础语法")
        assert result == "python简介、基础语法"

    def test_resolve_focus_title_strips_known_file_suffix(self) -> None:
        result = LeaderboardService._resolve_focus_title("python_intro_basics.md")
        assert result == "python intro basics"

    def test_resolve_focus_title_falls_back_when_empty(self) -> None:
        result = LeaderboardService._resolve_focus_title("   ")
        assert result == "Untitled document"


class _FakeRepo:
    async def get_global_leaderboard(self, limit: int, offset: int = 0) -> list[SimpleNamespace]:
        _ = limit
        _ = offset
        return []

    async def count_global_leaderboard_users(self) -> int:
        return 0

    async def get_user_total_xp(self, user_id: UUID) -> SimpleNamespace:
        _ = user_id
        return SimpleNamespace(display_name="Viewer", total_xp=1200)

    async def get_user_rank(self, user_id: UUID, total_xp: int) -> int:
        _ = user_id
        _ = total_xp
        return 1

    async def get_weekly_leaderboard(
        self, limit: int, offset: int = 0, *, start_at, end_at
    ) -> list[SimpleNamespace]:
        _ = limit
        _ = offset
        _ = start_at
        _ = end_at
        return []

    async def count_weekly_leaderboard_users(self, *, start_at, end_at) -> int:
        _ = start_at
        _ = end_at
        return 0

    async def get_user_weekly_xp(self, user_id: UUID, *, start_at, end_at) -> SimpleNamespace:
        _ = user_id
        _ = start_at
        _ = end_at
        return SimpleNamespace(display_name="Viewer", weekly_xp=1200)

    async def get_user_weekly_rank(self, user_id: UUID, weekly_xp: int, *, start_at, end_at) -> int:
        _ = user_id
        _ = weekly_xp
        _ = start_at
        _ = end_at
        return 1

    async def get_daily_focus_documents(
        self, *, user_id: UUID, start_at, end_at, limit: int
    ) -> list[SimpleNamespace]:
        _ = user_id
        _ = start_at
        _ = end_at
        _ = limit
        return [
            SimpleNamespace(
                document_id=UUID("00000000-0000-0000-0000-000000000123"),
                title="python_intro_basics.md",
                completed_runs=2,
                correct_sum=8,
                total_sum=10,
            )
        ]

    async def get_document_semantic_context(self, document_id: UUID, limit: int = 5) -> list[str]:
        _ = document_id
        _ = limit
        return [
            "Python 简介: 解释型语言",
            "基础语法包括变量、条件、循环与函数",
        ]


class _FakeWeeklyRepo(_FakeRepo):
    async def get_weekly_leaderboard(
        self, limit: int, offset: int = 0, *, start_at, end_at
    ) -> list[SimpleNamespace]:
        _ = limit
        _ = offset
        _ = start_at
        _ = end_at
        return [
            SimpleNamespace(
                user_id=UUID("00000000-0000-0000-0000-000000000001"),
                display_name="Top Scholar",
                weekly_xp=1889,
            ),
            SimpleNamespace(
                user_id=UUID("00000000-0000-0000-0000-000000000002"),
                display_name="Sixth Scholar",
                weekly_xp=104,
            ),
        ]

    async def count_weekly_leaderboard_users(self, *, start_at, end_at) -> int:
        _ = start_at
        _ = end_at
        return 2

    async def get_user_weekly_xp(self, user_id: UUID, *, start_at, end_at) -> SimpleNamespace:
        _ = user_id
        _ = start_at
        _ = end_at
        return SimpleNamespace(display_name="Viewer", weekly_xp=1889)

    async def get_user_weekly_rank(self, user_id: UUID, weekly_xp: int, *, start_at, end_at) -> int:
        _ = user_id
        _ = weekly_xp
        _ = start_at
        _ = end_at
        return 1


class _FakeLargeWeeklyRepo(_FakeRepo):
    def __init__(self, total_users: int) -> None:
        self.total_users = total_users
        self.last_limit = 0

    async def get_weekly_leaderboard(
        self, limit: int, offset: int = 0, *, start_at, end_at
    ) -> list[SimpleNamespace]:
        self.last_limit = limit
        _ = offset
        _ = start_at
        _ = end_at
        return [
            SimpleNamespace(
                user_id=UUID(f"00000000-0000-0000-0000-{index:012d}"),
                display_name=f"Scholar {index}",
                weekly_xp=1000 - index,
            )
            for index in range(1, min(limit, self.total_users) + 1)
        ]

    async def count_weekly_leaderboard_users(self, *, start_at, end_at) -> int:
        _ = start_at
        _ = end_at
        return self.total_users

    async def get_user_weekly_xp(self, user_id: UUID, *, start_at, end_at) -> SimpleNamespace:
        _ = start_at
        _ = end_at
        return SimpleNamespace(user_id=user_id, display_name="Viewer", weekly_xp=1)

    async def get_user_weekly_rank(self, user_id: UUID, weekly_xp: int, *, start_at, end_at) -> int:
        _ = user_id
        _ = weekly_xp
        _ = start_at
        _ = end_at
        return self.total_users


class _FakeEmptyWeeklyRepo(_FakeRepo):
    async def get_weekly_leaderboard(
        self, limit: int, offset: int = 0, *, start_at, end_at
    ) -> list[SimpleNamespace]:
        _ = limit
        _ = offset
        _ = start_at
        _ = end_at
        return []

    async def count_weekly_leaderboard_users(self, *, start_at, end_at) -> int:
        _ = start_at
        _ = end_at
        return 0

    async def get_user_weekly_xp(self, user_id: UUID, *, start_at, end_at) -> SimpleNamespace:
        _ = start_at
        _ = end_at
        return SimpleNamespace(user_id=user_id, display_name="Viewer", weekly_xp=0)

    async def get_user_weekly_rank(self, user_id: UUID, weekly_xp: int, *, start_at, end_at) -> int:
        _ = user_id
        _ = weekly_xp
        _ = start_at
        _ = end_at
        return 1


class _FakeLlmClient:
    def __init__(self, payload: dict[str, object] | None = None, raise_error: bool = False) -> None:
        self.payload = payload or {"structured_output": {"title": "python简介、基础语法"}}
        self.raise_error = raise_error

    async def generate(
        self, prompt: str, *, response_format: dict[str, str] | None = None
    ) -> dict[str, object]:
        _ = prompt
        _ = response_format
        if self.raise_error:
            raise RuntimeError("llm unavailable")
        return self.payload


@pytest.mark.asyncio
async def test_focus_title_prefers_llm_semantic_title() -> None:
    service = LeaderboardService(repository=_FakeRepo(), llm_client=_FakeLlmClient())

    result = await service.get_global_leaderboard(
        user_id=UUID("00000000-0000-0000-0000-000000000999"),
        limit=25,
        offset=0,
        scope="global",
    )

    assert result.viewer.daily_focus[0].title == "python简介、基础语法"


@pytest.mark.asyncio
async def test_focus_title_falls_back_when_llm_fails() -> None:
    service = LeaderboardService(
        repository=_FakeRepo(), llm_client=_FakeLlmClient(raise_error=True)
    )

    result = await service.get_global_leaderboard(
        user_id=UUID("00000000-0000-0000-0000-000000000999"),
        limit=25,
        offset=0,
        scope="global",
    )

    assert result.viewer.daily_focus[0].title == "python intro basics"


def test_week_window_uses_beijing_monday_boundary() -> None:
    now = datetime(2026, 5, 18, 8, 30, tzinfo=BEIJING_TZ)

    starts_at, ends_at = LeaderboardService._resolve_week_window(now)

    assert starts_at == datetime(2026, 5, 18, 0, 0, tzinfo=BEIJING_TZ)
    assert ends_at == datetime(2026, 5, 25, 0, 0, tzinfo=BEIJING_TZ)


def test_week_window_keeps_sunday_in_current_beijing_week() -> None:
    now = datetime(2026, 5, 24, 23, 30, tzinfo=BEIJING_TZ)

    starts_at, ends_at = LeaderboardService._resolve_week_window(now)

    assert starts_at == datetime(2026, 5, 18, 0, 0, tzinfo=BEIJING_TZ)
    assert ends_at == datetime(2026, 5, 25, 0, 0, tzinfo=BEIJING_TZ)


def test_week_window_converts_utc_to_beijing_week() -> None:
    now = datetime(2026, 5, 17, 20, 30, tzinfo=UTC)

    starts_at, ends_at = LeaderboardService._resolve_week_window(now)

    assert starts_at == datetime(2026, 5, 18, 0, 0, tzinfo=BEIJING_TZ)
    assert ends_at == datetime(2026, 5, 25, 0, 0, tzinfo=BEIJING_TZ)


@pytest.mark.asyncio
async def test_leaderboard_snapshot_uses_weekly_xp_and_promotion_zone() -> None:
    service = LeaderboardService(repository=_FakeWeeklyRepo())

    result = await service.get_global_leaderboard(
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        limit=25,
        offset=0,
        scope="global",
    )

    assert result.promotion_cutoff_rank == 5
    assert result.week_starts_at.tzinfo is not None
    assert result.week_ends_at.tzinfo is not None
    assert result.entries[0].weekly_xp == 1889
    assert result.entries[0].total_xp == 1889
    assert result.entries[0].tier_key == "apprentice"
    assert result.entries[0].tier_name == "见习学徒"
    assert result.entries[0].is_promotion_zone is True
    assert result.entries[1].is_promotion_zone is True
    assert result.viewer.weekly_xp == 1889
    assert result.viewer.tier_name == "见习学徒"
    assert result.viewer.is_promotion_zone is True


@pytest.mark.asyncio
async def test_leaderboard_includes_viewer_when_weekly_xp_is_zero() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000099")
    service = LeaderboardService(repository=_FakeEmptyWeeklyRepo())

    result = await service.get_global_leaderboard(
        user_id=user_id,
        limit=25,
        offset=0,
        scope="global",
    )

    assert result.viewer.weekly_xp == 0
    assert result.entries[0].user_id == user_id
    assert result.entries[0].display_name == "Viewer"
    assert result.entries[0].weekly_xp == 0
    assert result.entries[0].rank == 1


@pytest.mark.asyncio
async def test_leaderboard_caps_weekly_participants_at_twenty() -> None:
    repo = _FakeLargeWeeklyRepo(total_users=25)
    service = LeaderboardService(repository=repo)

    result = await service.get_global_leaderboard(
        user_id=UUID("00000000-0000-0000-0000-000000000099"),
        limit=100,
        offset=0,
        scope="global",
    )

    assert repo.last_limit == 20
    assert result.limit == 20
    assert result.participants_count == 25
    assert len(result.entries) == 21


@pytest.mark.asyncio
async def test_leaderboard_hides_demotion_zone_when_participants_are_fewer_than_ten() -> None:
    service = LeaderboardService(repository=_FakeLargeWeeklyRepo(total_users=9))

    result = await service.get_global_leaderboard(
        user_id=UUID("00000000-0000-0000-0000-000000000009"),
        limit=20,
        offset=0,
        scope="global",
    )

    assert result.demotion_count == 4
    assert all(not entry.is_demotion_zone for entry in result.entries)
    assert result.viewer.is_demotion_zone is False


@pytest.mark.asyncio
async def test_leaderboard_marks_bottom_four_as_demotion_zone_when_enough_participants() -> None:
    service = LeaderboardService(repository=_FakeLargeWeeklyRepo(total_users=10))

    result = await service.get_global_leaderboard(
        user_id=UUID("00000000-0000-0000-0000-000000000010"),
        limit=20,
        offset=0,
        scope="global",
    )

    demotion_ranks = [entry.rank for entry in result.entries if entry.is_demotion_zone]
    assert demotion_ranks == [7, 8, 9, 10]
    assert result.entries[0].projected_tier_name == "初阶学者"
    assert result.entries[-1].projected_tier_name == "见习学徒"
    assert result.viewer.is_demotion_zone is True
