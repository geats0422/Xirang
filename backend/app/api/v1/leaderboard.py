"""API routes for leaderboard."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.session import get_db_session
from app.repositories.leaderboard_repository import LeaderboardRepository
from app.schemas.leaderboard import LeaderboardListResponse
from app.services.leaderboard.service import LeaderboardService, create_leaderboard_service

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])
logger = logging.getLogger(__name__)


async def get_leaderboard_service(
    session: AsyncSession = Depends(get_db_session),
) -> LeaderboardService:
    return create_leaderboard_service(repository=LeaderboardRepository(session))


@router.get("", response_model=LeaderboardListResponse)
async def list_leaderboard(
    limit: int = 25,
    offset: int = 0,
    scope: str = "global",
    user_id: UUID = Depends(get_current_user_id),
    service: LeaderboardService = Depends(get_leaderboard_service),
) -> LeaderboardListResponse:
    logger.info(
        "Leaderboard request: scope=%s, limit=%d, offset=%d, user_id=%s",
        scope,
        limit,
        offset,
        user_id,
    )
    return await service.get_global_leaderboard(
        user_id=user_id,
        limit=limit,
        offset=offset,
        scope=scope,
    )


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
