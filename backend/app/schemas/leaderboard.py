from uuid import UUID

from pydantic import BaseModel


class LeaderboardEntryResponse(BaseModel):
    user_id: UUID
    display_name: str | None
    total_xp: int
    rank: int
    level: int
    energy_points: int
    is_current_user: bool = False


class DailyFocusItemResponse(BaseModel):
    document_id: UUID | None
    title: str
    progress_current: int
    progress_total: int
    progress_text: str


class LeaderboardViewerSummaryResponse(BaseModel):
    user_id: UUID
    display_name: str
    total_xp: int
    rank: int
    level: int
    energy_points: int
    daily_focus: list[DailyFocusItemResponse]


class LeaderboardListResponse(BaseModel):
    scope: str
    limit: int
    offset: int
    has_more: bool
    entries: list[LeaderboardEntryResponse]
    viewer: LeaderboardViewerSummaryResponse
