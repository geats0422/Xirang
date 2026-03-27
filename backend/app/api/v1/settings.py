"""API routes for settings."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.core.config import get_settings as get_app_settings
from app.db.models.profile import LeaderboardScope, ThemeKey
from app.db.session import get_db_session
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import AiConfigResponse, SettingsResponse, SettingsUpdateRequest
from app.services.settings.service import SettingsNotFoundError, SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


async def get_settings_service(session: AsyncSession = Depends(get_db_session)) -> SettingsService:
    return SettingsService(repository=SettingsRepository(session))


@router.get("", response_model=SettingsResponse)
async def get_settings(
    user_id: UUID = Depends(get_current_user_id),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsResponse:
    try:
        return await service.get_settings(user_id)
    except SettingsNotFoundError:
        return SettingsResponse(
            user_id=user_id,
            theme_key=ThemeKey.SYSTEM,
            language_code="en",
            sound_enabled=True,
            haptic_enabled=True,
            daily_reminder_enabled=False,
            leaderboard_scope_default=LeaderboardScope.GLOBAL,
            updated_at=datetime.fromtimestamp(0),
        )


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    payload: SettingsUpdateRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsResponse:
    try:
        return await service.update_settings(user_id=user_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/ai-config", response_model=AiConfigResponse)
async def get_ai_config(
    _user_id: UUID = Depends(get_current_user_id),
) -> AiConfigResponse:
    settings = get_app_settings()
    return AiConfigResponse(
        provider="openai-compatible",
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        configured=bool(settings.llm_api_key),
    )


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
