"""API routes for settings."""

from datetime import datetime
from typing import Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.core.config import get_settings
from app.db.models.profile import LeaderboardScope, ThemeKey
from app.db.session import get_db_session
from app.repositories.auth_repository import AuthRepository
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest
from app.services.auth.passwords import PasswordService
from app.services.auth.service import AuthService
from app.services.auth.tokens import TokenService
from app.services.settings.service import SettingsNotFoundError, SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


async def get_settings_service(session: AsyncSession = Depends(get_db_session)) -> SettingsService:
    return SettingsService(repository=SettingsRepository(session))


async def get_account_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    settings = get_settings()
    token_service = TokenService(
        secret_key=settings.secret_key,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
        algorithm=settings.jwt_algorithm,
    )
    return AuthService(
        repository=AuthRepository(session),
        password_service=PasswordService(),
        token_service=token_service,
    )


@router.get("", response_model=SettingsResponse)
async def fetch_settings(
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


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/clear-game-data", status_code=status.HTTP_204_NO_CONTENT)
async def clear_game_data(
    user_id: UUID = Depends(get_current_user_id),
    service: AuthService = Depends(get_account_service),
) -> Response:
    await service.clear_game_data(user_id=user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


FEATURED_MODEL_KEYWORDS = [
    "minimax",
    "kimi",
    "deepseek",
    "nemotron",
    "llama",
    "qwen",
    "mistral",
    "gemma",
    "gpt",
    "claude",
    "gemini",
    "yi-large",
    "baichuan",
    "dracarys",
]


def _build_model_info(model_id: str) -> dict[str, Any]:
    parts = model_id.split("/", 1)
    provider = parts[0] if len(parts) > 1 else "nvidia"
    name = parts[-1].replace("-", " ").replace("_", " ").title()
    is_premium = any(k in model_id.lower() for k in ["340b", "70b", "large", "pro"])
    return {
        "id": model_id,
        "name": f"{provider.title()} {name}",
        "description": f"Available on NVIDIA Build - {model_id}",
        "tags": [provider.title(), "PRO" if is_premium else "Standard"],
        "provider": provider,
    }


@router.get("/models")
async def get_available_models() -> list[dict[str, Any]]:
    settings = get_settings()
    models: list[dict[str, Any]] = []

    if settings.nvidia_api_key:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{settings.nvidia_base_url}/models",
                    headers={
                        "Authorization": f"Bearer {settings.nvidia_api_key}",
                        "Accept": "application/json",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    raw_models = data.get("data", []) if isinstance(data, dict) else []
                    featured = [
                        m["id"]
                        for m in raw_models
                        if isinstance(m, dict)
                        and any(k in m.get("id", "").lower() for k in FEATURED_MODEL_KEYWORDS)
                    ]
                    for mid in featured:
                        models.append(_build_model_info(mid))
        except Exception:
            pass

    if settings.openai_api_key and not models:
        models.extend(
            [
                {
                    "id": "gpt-4o-mini",
                    "name": "GPT-4o Mini",
                    "description": "Fast and efficient for most tasks.",
                    "tags": ["OpenAI", "Fast"],
                    "provider": "openai",
                },
                {
                    "id": "gpt-4o",
                    "name": "GPT-4o",
                    "description": "Most capable OpenAI model.",
                    "tags": ["OpenAI", "PRO", "Versatile"],
                    "provider": "openai",
                },
            ]
        )

    if not models:
        models.append(
            {
                "id": "placeholder",
                "name": "No API Configured",
                "description": "Configure NVIDIA_API_KEY or OPENAI_API_KEY in environment.",
                "tags": ["Setup Required"],
                "provider": "none",
            }
        )

    return models
