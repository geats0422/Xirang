from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LeaderboardEntryResponse(BaseModel):
    user_id: UUID
    display_name: str | None
    total_xp: int
    weekly_xp: int = 0
    rank: int
    level: int
    tier_key: str = "apprentice"
    tier_name: str = "见习学徒"
    projected_tier_name: str = "见习学徒"
    energy_points: int
    is_current_user: bool = False
    is_promotion_zone: bool = False
    is_demotion_zone: bool = False


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
    weekly_xp: int = 0
    rank: int
    level: int
    tier_key: str = "apprentice"
    tier_name: str = "见习学徒"
    projected_tier_name: str = "见习学徒"
    energy_points: int
    is_promotion_zone: bool = False
    is_demotion_zone: bool = False
    daily_focus: list[DailyFocusItemResponse]


class LeaderboardListResponse(BaseModel):
    scope: str
    limit: int
    offset: int
    week_starts_at: datetime | None = None
    week_ends_at: datetime | None = None
    promotion_cutoff_rank: int = 5
    demotion_count: int = 4
    participants_count: int = 0
    has_more: bool
    entries: list[LeaderboardEntryResponse]
    viewer: LeaderboardViewerSummaryResponse
