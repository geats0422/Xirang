from types import SimpleNamespace
from uuid import UUID

import pytest

from app.services.leaderboard.service import LeaderboardService


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
