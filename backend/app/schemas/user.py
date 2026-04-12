from pydantic import BaseModel


class DailyGoalResponse(BaseModel):
    goal_current: int = 0
    goal_total: int = 60
    goal_unit: str = "minutes"
    is_completed: bool = False
    streak_days: int = 0
