from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

from app.schemas.shop import LeaderboardEntryResponse

if TYPE_CHECKING:
    from uuid import UUID


class LeaderboardRowProtocol(Protocol):
    user_id: UUID
    display_name: str | None
    total_xp: int


class LeaderboardRepositoryProtocol(Protocol):
    async def get_global_leaderboard(self, limit: int) -> list[LeaderboardRowProtocol]: ...


class LeaderboardServiceError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class LeaderboardService:
    """Service for retrieving leaderboard data."""

    def __init__(self, *, repository: Any) -> None:
        self.repository: LeaderboardRepositoryProtocol = cast(
            "LeaderboardRepositoryProtocol", repository
        )

    async def get_global_leaderboard(self, limit: int = 100) -> list[LeaderboardEntryResponse]:
        """Get the global leaderboard.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of leaderboard entries with rankings.
        """
        rows = await self.repository.get_global_leaderboard(limit)
        return [
            LeaderboardEntryResponse(
                user_id=row.user_id,
                display_name=row.display_name,
                total_xp=row.total_xp,
                rank=idx + 1,
            )
            for idx, row in enumerate(rows)
        ]
