from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast

from app.schemas.profile import ProfileResponse, ProfileUpdateRequest

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class ProfileProtocol(Protocol):
    user_id: UUID
    display_name: str | None
    avatar_url: str | None
    bio: str | None
    verified_badge: bool
    tier_label: str | None
    created_at: datetime
    updated_at: datetime


class ProfileRepositoryProtocol(Protocol):
    async def get_profile(self, user_id: UUID) -> ProfileProtocol | None: ...
    async def update_profile(self, user_id: UUID, **fields: Any) -> ProfileProtocol: ...
    async def commit(self) -> None: ...


@dataclass(slots=True)
class ProfileData:
    user_id: UUID
    display_name: str | None
    avatar_url: str | None
    bio: str | None
    verified_badge: bool
    tier_label: str | None
    created_at: datetime
    updated_at: datetime


class ProfileServiceError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProfileNotFoundError(ProfileServiceError):
    status_code = 404


class ProfileService:
    """Service for managing user profiles."""

    def __init__(self, *, repository: Any) -> None:
        self.repository: ProfileRepositoryProtocol = cast("ProfileRepositoryProtocol", repository)

    async def get_profile(self, user_id: UUID) -> ProfileResponse:
        """Get a user's profile.

        Args:
            user_id: The user's ID.

        Returns:
            The user's profile data.

        Raises:
            ProfileNotFoundError: If profile doesn't exist.
        """
        profile = await self.repository.get_profile(user_id)
        if profile is None:
            raise ProfileNotFoundError("Profile not found")
        return ProfileResponse.model_validate(profile)

    async def update_profile(self, user_id: UUID, payload: ProfileUpdateRequest) -> ProfileResponse:
        """Update a user's profile.

        Args:
            user_id: The user's ID.
            payload: Profile update data.

        Returns:
            The updated profile data.
        """
        update_fields = payload.model_dump(exclude_unset=True)
        if not update_fields:
            return await self.get_profile(user_id)

        profile = await self.repository.update_profile(user_id, **update_fields)
        await self.repository.commit()
        return ProfileResponse.model_validate(profile)
