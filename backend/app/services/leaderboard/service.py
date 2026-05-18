from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone, tzinfo
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
    async def get_weekly_leaderboard(
        self,
        limit: int,
        offset: int = 0,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[LeaderboardRowProtocol]: ...

    async def count_weekly_leaderboard_users(
        self, *, start_at: datetime, end_at: datetime
    ) -> int: ...

    async def get_user_weekly_xp(
        self, user_id: UUID, *, start_at: datetime, end_at: datetime
    ) -> Any | None: ...

    async def get_user_weekly_rank(
        self, user_id: UUID, weekly_xp: int, *, start_at: datetime, end_at: datetime
    ) -> int: ...

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

    PROMOTION_CUTOFF_RANK = 5
    DEMOTION_COUNT = 4
    MAX_WEEKLY_PARTICIPANTS = 20
    DEFAULT_TIER_KEY = "apprentice"
    DEFAULT_TIER_NAME = "见习学徒"
    NEXT_TIER_NAME = "初阶学者"

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
            logger.warning("ZoneInfo Asia/Shanghai unavailable, falling back to UTC+8")
            return timezone(timedelta(hours=8), name="Asia/Shanghai")

    @classmethod
    def _resolve_week_window(cls, now: datetime | None = None) -> tuple[datetime, datetime]:
        tz = cls._resolve_day_timezone()
        local_now = (now or datetime.now(tz)).astimezone(tz)
        week_start = (local_now - timedelta(days=local_now.weekday())).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return week_start, week_start + timedelta(days=7)

    @classmethod
    def _is_promotion_zone(cls, rank: int) -> bool:
        return 1 <= rank <= cls.PROMOTION_CUTOFF_RANK

    @classmethod
    def _is_demotion_zone(cls, rank: int, participants_count: int) -> bool:
        return participants_count >= 10 and rank > participants_count - cls.DEMOTION_COUNT

    @classmethod
    def _projected_tier_name(cls, rank: int, participants_count: int) -> str:
        if cls._is_promotion_zone(rank):
            return cls.NEXT_TIER_NAME
        if cls._is_demotion_zone(rank, participants_count):
            return cls.DEFAULT_TIER_NAME
        return cls.DEFAULT_TIER_NAME

    @staticmethod
    def _resolve_row_xp(row: LeaderboardRowProtocol) -> int:
        raw_xp = getattr(row, "weekly_xp", None)
        if raw_xp is None:
            raw_xp = row.total_xp
        return int(raw_xp)

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
        safe_limit = max(1, min(limit, self.MAX_WEEKLY_PARTICIPANTS))
        safe_offset = max(0, offset)

        week_starts_at, week_ends_at = self._resolve_week_window()
        rows = await self.repository.get_weekly_leaderboard(
            safe_limit,
            safe_offset,
            start_at=week_starts_at,
            end_at=week_ends_at,
        )
        total_users = await self.repository.count_weekly_leaderboard_users(
            start_at=week_starts_at,
            end_at=week_ends_at,
        )

        viewer_row = await self.repository.get_user_weekly_xp(
            user_id,
            start_at=week_starts_at,
            end_at=week_ends_at,
        )
        viewer_weekly_xp = int(getattr(viewer_row, "weekly_xp", 0)) if viewer_row is not None else 0
        viewer_name = (
            str(viewer_row.display_name)
            if viewer_row is not None and viewer_row.display_name is not None
            else "Default user"
        )
        viewer_rank = await self.repository.get_user_weekly_rank(
            user_id,
            viewer_weekly_xp,
            start_at=week_starts_at,
            end_at=week_ends_at,
        )

        entries = [
            LeaderboardEntryResponse(
                user_id=row.user_id,
                display_name=row.display_name,
                total_xp=self._resolve_row_xp(row),
                weekly_xp=self._resolve_row_xp(row),
                rank=safe_offset + idx + 1,
                level=self._resolve_level(self._resolve_row_xp(row)),
                tier_key=self.DEFAULT_TIER_KEY,
                tier_name=self.DEFAULT_TIER_NAME,
                projected_tier_name=self._projected_tier_name(
                    safe_offset + idx + 1,
                    total_users,
                ),
                energy_points=0,
                is_current_user=row.user_id == user_id,
                is_promotion_zone=self._is_promotion_zone(safe_offset + idx + 1),
                is_demotion_zone=self._is_demotion_zone(safe_offset + idx + 1, total_users),
            )
            for idx, row in enumerate(rows)
        ]
        if safe_offset == 0 and all(entry.user_id != user_id for entry in entries):
            entries.append(
                LeaderboardEntryResponse(
                    user_id=user_id,
                    display_name=viewer_name,
                    total_xp=viewer_weekly_xp,
                    weekly_xp=viewer_weekly_xp,
                    rank=viewer_rank,
                    level=self._resolve_level(viewer_weekly_xp),
                    tier_key=self.DEFAULT_TIER_KEY,
                    tier_name=self.DEFAULT_TIER_NAME,
                    projected_tier_name=self._projected_tier_name(viewer_rank, total_users),
                    energy_points=0,
                    is_current_user=True,
                    is_promotion_zone=self._is_promotion_zone(viewer_rank),
                    is_demotion_zone=self._is_demotion_zone(viewer_rank, total_users),
                )
            )

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
            total_xp=viewer_weekly_xp,
            weekly_xp=viewer_weekly_xp,
            rank=viewer_rank,
            level=self._resolve_level(viewer_weekly_xp),
            tier_key=self.DEFAULT_TIER_KEY,
            tier_name=self.DEFAULT_TIER_NAME,
            projected_tier_name=self._projected_tier_name(viewer_rank, total_users),
            energy_points=self._resolve_energy_points(today_completed_runs),
            is_promotion_zone=self._is_promotion_zone(viewer_rank),
            is_demotion_zone=self._is_demotion_zone(viewer_rank, total_users),
            daily_focus=daily_focus,
        )

        return LeaderboardListResponse(
            scope=scope,
            limit=safe_limit,
            offset=safe_offset,
            week_starts_at=week_starts_at,
            week_ends_at=week_ends_at,
            promotion_cutoff_rank=self.PROMOTION_CUTOFF_RANK,
            demotion_count=self.DEMOTION_COUNT,
            participants_count=total_users,
            has_more=safe_offset + len(entries) < total_users,
            entries=entries,
            viewer=viewer,
        )


def create_leaderboard_service(*, repository: Any) -> LeaderboardService:
    settings = get_settings()
    llm_client = AgentsClient() if settings.llm_api_key else None
    return LeaderboardService(repository=repository, llm_client=llm_client)
