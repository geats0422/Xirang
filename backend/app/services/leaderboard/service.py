from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta, tzinfo
from typing import TYPE_CHECKING, Any, Protocol, cast
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import get_settings
from app.integrations.agents.client import AgentsClient
from app.schemas.leaderboard import (
    DailyFocusItemResponse,
    LeaderboardEntryResponse,
    LeaderboardListResponse,
    LeaderboardViewerSummaryResponse,
)

if TYPE_CHECKING:
    from uuid import UUID


logger = logging.getLogger(__name__)


class LeaderboardRowProtocol(Protocol):
    user_id: UUID
    display_name: str | None
    total_xp: int


class LeaderboardRepositoryProtocol(Protocol):
    async def get_global_leaderboard(
        self, limit: int, offset: int = 0
    ) -> list[LeaderboardRowProtocol]: ...

    async def count_global_leaderboard_users(self) -> int: ...
    async def get_user_total_xp(self, user_id: UUID) -> Any | None: ...
    async def get_user_rank(self, user_id: UUID, total_xp: int) -> int: ...
    async def get_daily_focus_documents(
        self,
        *,
        user_id: UUID,
        start_at: datetime,
        end_at: datetime,
        limit: int,
    ) -> list[Any]: ...

    async def get_document_semantic_context(
        self, document_id: UUID, limit: int = 5
    ) -> list[str]: ...


class LLMClientProtocol(Protocol):
    async def generate(
        self,
        prompt: str,
        *,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


class LeaderboardServiceError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class LeaderboardService:
    """Service for retrieving leaderboard data."""

    def __init__(self, *, repository: Any, llm_client: LLMClientProtocol | None = None) -> None:
        self.repository: LeaderboardRepositoryProtocol = cast(
            "LeaderboardRepositoryProtocol", repository
        )
        self._llm_client = llm_client

    @staticmethod
    def _resolve_level(total_xp: int) -> int:
        return max(1, (max(0, total_xp) // 500) + 1)

    @staticmethod
    def _resolve_energy_points(today_completed_runs: int) -> int:
        return max(0, today_completed_runs)

    @staticmethod
    def _resolve_focus_title(raw_title: object) -> str:
        title = str(raw_title or "").strip()
        if not title:
            return "Untitled document"

        lowered = title.lower()
        known_suffixes = (
            ".pdf",
            ".txt",
            ".md",
            ".markdown",
            ".doc",
            ".docx",
            ".ppt",
            ".pptx",
            ".epub",
        )
        for suffix in known_suffixes:
            if lowered.endswith(suffix):
                title = title[: -len(suffix)].strip()
                break

        title = title.replace("_", " ").replace("-", " ")
        title = " ".join(part for part in title.split(" ") if part)
        if len(title) > 48:
            return f"{title[:45].rstrip()}..."
        return title or "Untitled document"

    @staticmethod
    def _resolve_day_timezone() -> tzinfo:
        try:
            return ZoneInfo("Asia/Shanghai")
        except ZoneInfoNotFoundError:
            logger.warning("ZoneInfo Asia/Shanghai unavailable, falling back to local timezone")
            local_tz = datetime.now().astimezone().tzinfo
            if local_tz is not None:
                return local_tz
            return UTC

    @staticmethod
    def _parse_semantic_title_response(response: dict[str, Any]) -> str | None:
        structured_output = response.get("structured_output")
        if isinstance(structured_output, dict):
            title_value = structured_output.get("title")
            if isinstance(title_value, str) and title_value.strip():
                return title_value.strip()

        content = response.get("content")
        if isinstance(content, str) and content.strip():
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    title_value = parsed.get("title")
                    if isinstance(title_value, str) and title_value.strip():
                        return title_value.strip()
            except json.JSONDecodeError:
                first_line = content.strip().splitlines()[0]
                if first_line:
                    return first_line[:80].strip()
        return None

    async def _resolve_focus_title_with_semantics(
        self, raw_title: object, document_id: UUID | None
    ) -> str:
        fallback_title = self._resolve_focus_title(raw_title)
        if self._llm_client is None or document_id is None:
            return fallback_title

        context_prompts = await self.repository.get_document_semantic_context(document_id, 5)
        if len(context_prompts) == 0:
            return fallback_title

        context_text = "\n".join(f"- {item}" for item in context_prompts[:5])
        prompt = (
            "You are generating a concise study focus title for a learning dashboard.\n"
            "Given question prompts from one document, infer the document topic and output JSON only.\n"
            'Required format: {"title":"..."}.\n'
            "Constraints:\n"
            "- <= 24 characters for Chinese, <= 40 chars for English\n"
            "- No punctuation wrapping such as quotes\n"
            "- Keep domain terms (e.g., Python, SQL)\n"
            f"Current fallback title: {fallback_title}\n"
            "Question prompts:\n"
            f"{context_text}"
        )

        try:
            response = await self._llm_client.generate(
                prompt,
                response_format={"type": "json_object"},
            )
            semantic_title = self._parse_semantic_title_response(response)
            if semantic_title:
                return self._resolve_focus_title(semantic_title)
        except Exception as exc:
            logger.warning(
                "Failed to generate semantic focus title for document %s: %s", document_id, exc
            )
        return fallback_title

    async def get_global_leaderboard(
        self,
        *,
        user_id: UUID,
        limit: int = 25,
        offset: int = 0,
        scope: str = "global",
    ) -> LeaderboardListResponse:
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        rows = await self.repository.get_global_leaderboard(safe_limit, safe_offset)
        total_users = await self.repository.count_global_leaderboard_users()

        entries = [
            LeaderboardEntryResponse(
                user_id=row.user_id,
                display_name=row.display_name,
                total_xp=int(row.total_xp),
                rank=safe_offset + idx + 1,
                level=self._resolve_level(int(row.total_xp)),
                energy_points=0,
                is_current_user=row.user_id == user_id,
            )
            for idx, row in enumerate(rows)
        ]

        viewer_row = await self.repository.get_user_total_xp(user_id)
        viewer_total_xp = int(viewer_row.total_xp) if viewer_row is not None else 0
        viewer_name = (
            str(viewer_row.display_name)
            if viewer_row is not None and viewer_row.display_name is not None
            else "Default user"
        )
        viewer_rank = await self.repository.get_user_rank(user_id, viewer_total_xp)

        tz = self._resolve_day_timezone()
        now_local = datetime.now(tz)
        day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        focus_rows = await self.repository.get_daily_focus_documents(
            user_id=user_id,
            start_at=day_start,
            end_at=day_end,
            limit=3,
        )
        daily_focus: list[DailyFocusItemResponse] = []
        today_completed_runs = 0
        for row in focus_rows:
            completed_runs = int(row.completed_runs or 0)
            today_completed_runs += completed_runs
            progress_total = int(row.total_sum or 0)
            progress_current = min(progress_total, int(row.correct_sum or 0))
            if progress_total <= 0:
                progress_total = max(1, completed_runs)
                progress_current = min(progress_total, completed_runs)
            resolved_title = await self._resolve_focus_title_with_semantics(
                row.title, row.document_id
            )
            daily_focus.append(
                DailyFocusItemResponse(
                    document_id=row.document_id,
                    title=resolved_title,
                    progress_current=progress_current,
                    progress_total=progress_total,
                    progress_text=f"{progress_current}/{progress_total}",
                )
            )
        viewer = LeaderboardViewerSummaryResponse(
            user_id=user_id,
            display_name=viewer_name,
            total_xp=viewer_total_xp,
            rank=viewer_rank,
            level=self._resolve_level(viewer_total_xp),
            energy_points=self._resolve_energy_points(today_completed_runs),
            daily_focus=daily_focus,
        )

        return LeaderboardListResponse(
            scope=scope,
            limit=safe_limit,
            offset=safe_offset,
            has_more=safe_offset + len(entries) < total_users,
            entries=entries,
            viewer=viewer,
        )


def create_leaderboard_service(*, repository: Any) -> LeaderboardService:
    settings = get_settings()
    llm_client = AgentsClient() if settings.llm_api_key else None
    return LeaderboardService(repository=repository, llm_client=llm_client)
