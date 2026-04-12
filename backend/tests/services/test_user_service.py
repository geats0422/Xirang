from uuid import uuid4

import pytest

from app.services.user.service import UserService


class FakeUserRepository:
    def __init__(self):
        self.get_daily_goal_calls = []

    async def get_daily_goal(self, user_id):
        self.get_daily_goal_calls.append(user_id)
        from app.schemas.user import DailyGoalResponse

        return DailyGoalResponse(
            goal_current=30,
            goal_total=60,
            goal_unit="minutes",
            is_completed=False,
            streak_days=7,
        )


@pytest.fixture
def user_service():
    return UserService(repository=FakeUserRepository())


def test_user_service_initialization(user_service):
    assert user_service._repository is not None


def test_user_service_has_get_daily_goal_method(user_service):
    assert hasattr(user_service, "get_daily_goal")
    assert callable(user_service.get_daily_goal)


@pytest.mark.asyncio
async def test_get_daily_goal_calls_repository(user_service):
    user_id = uuid4()
    await user_service.get_daily_goal(user_id)

    assert len(user_service._repository.get_daily_goal_calls) == 1
    assert user_service._repository.get_daily_goal_calls[0] == user_id


@pytest.mark.asyncio
async def test_get_daily_goal_returns_correct_data(user_service):
    user_id = uuid4()
    result = await user_service.get_daily_goal(user_id)

    assert result.goal_current == 30
    assert result.goal_total == 60
    assert result.goal_unit == "minutes"
    assert result.is_completed is False
    assert result.streak_days == 7
