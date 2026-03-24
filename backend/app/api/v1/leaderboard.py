"""API routes for leaderboard."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.leaderboard_repository import LeaderboardRepository
from app.schemas.shop import LeaderboardEntryResponse
from app.services.leaderboard.service import LeaderboardService

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


async def get_leaderboard_service(
    session: AsyncSession = Depends(get_db_session),
) -> LeaderboardService:
    return LeaderboardService(repository=LeaderboardRepository(session))


@router.get("", response_model=list[LeaderboardEntryResponse])
async def list_leaderboard(
    limit: int = 50,
    service: LeaderboardService = Depends(get_leaderboard_service),
) -> list[LeaderboardEntryResponse]:
    safe_limit = max(1, min(limit, 100))
    return await service.get_global_leaderboard(safe_limit)


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
