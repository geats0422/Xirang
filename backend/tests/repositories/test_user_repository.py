from __future__ import annotations

from uuid import uuid4

import pytest

from app.repositories.user_repository import UserRepository


class FakeSession:
    def __init__(self):
        self.executed_stmts = []

    async def execute(self, stmt):
        self.executed_stmts.append(stmt)
        return FakeResult()


class FakeResult:
    def one(self):
        return FakeRow(run_count=0, total_minutes=0.0)

    def all(self):
        return []


class FakeRow:
    def __init__(self, run_count, total_minutes):
        self.run_count = run_count
        self.total_minutes = total_minutes


@pytest.fixture
def session():
    return FakeSession()


@pytest.fixture
def repository(session):
    return UserRepository(session=session)


def test_repository_initialization(repository, session):
    assert repository._session is session


def test_repository_has_get_daily_goal_method(repository):
    assert hasattr(repository, "get_daily_goal")
    assert callable(repository.get_daily_goal)


def test_repository_has_calculate_streak_method(repository):
    assert hasattr(repository, "_calculate_streak")
    assert callable(repository._calculate_streak)


@pytest.mark.asyncio
async def test_get_daily_goal_returns_daily_goal_response(repository, session):
    result = await repository.get_daily_goal(uuid4())

    assert hasattr(result, "goal_current")
    assert hasattr(result, "goal_total")
    assert hasattr(result, "goal_unit")
    assert hasattr(result, "is_completed")
    assert hasattr(result, "streak_days")

    assert result.goal_total == 60
    assert result.goal_unit == "minutes"
    assert result.goal_current >= 0
