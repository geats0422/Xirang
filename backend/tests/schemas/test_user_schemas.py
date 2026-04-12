from app.schemas.user import DailyGoalResponse


def test_daily_goal_response_defaults():
    response = DailyGoalResponse()
    assert response.goal_current == 0
    assert response.goal_total == 60
    assert response.goal_unit == "minutes"
    assert response.is_completed is False
    assert response.streak_days == 0


def test_daily_goal_response_with_values():
    response = DailyGoalResponse(
        goal_current=30,
        goal_total=60,
        goal_unit="minutes",
        is_completed=False,
        streak_days=7,
    )
    assert response.goal_current == 30
    assert response.goal_total == 60
    assert response.goal_unit == "minutes"
    assert response.is_completed is False
    assert response.streak_days == 7


def test_daily_goal_response_completed():
    response = DailyGoalResponse(
        goal_current=60,
        goal_total=60,
        goal_unit="minutes",
        is_completed=True,
        streak_days=30,
    )
    assert response.goal_current == 60
    assert response.goal_total == 60
    assert response.is_completed is True
    assert response.streak_days == 30
