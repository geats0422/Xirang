"""API routes for profile."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.session import get_db_session
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileResponse

router = APIRouter(prefix="/profile", tags=["profile"])


async def get_profile_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ProfileRepository:
    return ProfileRepository(session)


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    user_id: UUID = Depends(get_current_user_id),
    repository: ProfileRepository = Depends(get_profile_repository),
) -> ProfileResponse:
    """Get the current user's profile including tier_label."""
    profile = await repository.get_profile(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return ProfileResponse.model_validate(profile)
