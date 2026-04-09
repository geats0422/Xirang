from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.session import get_db_session
from app.repositories.user_repository import UserRepository
from app.schemas.user import DailyGoalResponse
from app.services.user.service import UserService

router = APIRouter(prefix="/user", tags=["user"])


async def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)


async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository=repository)


@router.get("/daily-goal", response_model=DailyGoalResponse)
async def get_daily_goal(
    user_id: UUID = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
) -> DailyGoalResponse:
    return await service.get_daily_goal(user_id)
