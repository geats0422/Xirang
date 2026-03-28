from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.profile import LeaderboardScope, ThemeKey


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    theme_key: ThemeKey
    language_code: str
    sound_enabled: bool
    haptic_enabled: bool
    daily_reminder_enabled: bool
    leaderboard_scope_default: LeaderboardScope
    updated_at: datetime


class SettingsUpdateRequest(BaseModel):
    theme_key: ThemeKey | None = None
    language_code: str | None = None
    sound_enabled: bool | None = None
    haptic_enabled: bool | None = None
    daily_reminder_enabled: bool | None = None
    leaderboard_scope_default: LeaderboardScope | None = None


class AiConfigResponse(BaseModel):
    provider: str
    base_url: str | None
    model: str
    configured: bool
    available_models: list[str] = []
