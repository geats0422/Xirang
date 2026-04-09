from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.repositories.user_repository import UserRepository
    from app.schemas.user import DailyGoalResponse


class UserServiceError(Exception):
    pass


class UserService:
    def __init__(self, *, repository: UserRepository) -> None:
        self._repository = repository

    async def get_daily_goal(self, user_id: UUID) -> DailyGoalResponse:
        return await self._repository.get_daily_goal(user_id)
