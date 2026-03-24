from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast

from app.schemas.settings import SettingsResponse, SettingsUpdateRequest

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from app.db.models.profile import LeaderboardScope, ThemeKey


class SettingsProtocol(Protocol):
    user_id: UUID
    theme_key: ThemeKey
    language_code: str
    sound_enabled: bool
    haptic_enabled: bool
    daily_reminder_enabled: bool
    leaderboard_scope_default: LeaderboardScope
    updated_at: datetime


class SettingsRepositoryProtocol(Protocol):
    async def get_settings(self, user_id: UUID) -> SettingsProtocol | None: ...
    async def update_settings(self, user_id: UUID, **fields: Any) -> SettingsProtocol: ...
    async def commit(self) -> None: ...


@dataclass(slots=True)
class SettingsData:
    user_id: UUID
    theme_key: ThemeKey
    language_code: str
    sound_enabled: bool
    haptic_enabled: bool
    daily_reminder_enabled: bool
    leaderboard_scope_default: LeaderboardScope
    updated_at: datetime


class SettingsServiceError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SettingsNotFoundError(SettingsServiceError):
    status_code = 404


class SettingsService:
    """Service for managing user settings."""

    def __init__(self, *, repository: Any) -> None:
        self.repository: SettingsRepositoryProtocol = cast("SettingsRepositoryProtocol", repository)

    async def get_settings(self, user_id: UUID) -> SettingsResponse:
        """Get a user's settings.

        Args:
            user_id: The user's ID.

        Returns:
            The user's settings data.

        Raises:
            SettingsNotFoundError: If settings don't exist.
        """
        settings = await self.repository.get_settings(user_id)
        if settings is None:
            raise SettingsNotFoundError("Settings not found")
        return SettingsResponse.model_validate(settings)

    async def update_settings(
        self, user_id: UUID, payload: SettingsUpdateRequest
    ) -> SettingsResponse:
        """Update a user's settings.

        Args:
            user_id: The user's ID.
            payload: Settings update data.

        Returns:
            The updated settings data.
        """
        update_fields = payload.model_dump(exclude_unset=True)
        if not update_fields:
            return await self.get_settings(user_id)

        settings = await self.repository.update_settings(user_id, **update_fields)
        await self.repository.commit()
        return SettingsResponse.model_validate(settings)
