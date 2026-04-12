from __future__ import annotations

from datetime import datetime as dt
from datetime import timedelta
from datetime import timezone as tz_module
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select

from app.db.models.runs import Run, RunStatus
from app.schemas.user import DailyGoalResponse

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_daily_goal(self, user_id: UUID) -> DailyGoalResponse:
        day_start = func.cast(
            func.date_trunc("day", func.now().op("AT TIME ZONE")("Asia/Shanghai")),
            Run.started_at.type,
        )
        day_end = day_start + timedelta(days=1)

        stmt = select(
            func.count(Run.id).label("run_count"),
            func.coalesce(
                func.sum(func.extract("epoch", Run.ended_at - Run.started_at) / 60),
                0,
            ).label("total_minutes"),
        ).where(
            Run.user_id == user_id,
            Run.status == RunStatus.COMPLETED,
            Run.ended_at.is_not(None),
            Run.ended_at >= day_start,
            Run.ended_at < day_end,
        )
        result = await self._session.execute(stmt)
        row = result.one()

        total_minutes = int(float(row.total_minutes or 0))
        goal_total = 60
        is_completed = total_minutes >= goal_total

        streak_days = await self._calculate_streak(user_id)

        return DailyGoalResponse(
            goal_current=total_minutes,
            goal_total=goal_total,
            goal_unit="minutes",
            is_completed=is_completed,
            streak_days=streak_days,
        )

    async def _calculate_streak(self, user_id: UUID) -> int:
        day_expr = func.date_trunc("day", func.timezone("Asia/Shanghai", Run.ended_at)).label("day")

        stmt = (
            select(day_expr)
            .where(
                Run.user_id == user_id,
                Run.status == RunStatus.COMPLETED,
                Run.ended_at.is_not(None),
            )
            .group_by(day_expr)
            .order_by(day_expr.desc())
        )
        result = await self._session.execute(stmt)
        rows = list(result.all())

        if not rows:
            return 0

        streak = 0
        local_tz = tz_module(timedelta(hours=8))
        today = dt.now(local_tz).date()
        expected_date = today

        for row in rows:
            row_date = row.day.date() if hasattr(row.day, "date") else row.day
            if row_date == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            elif row_date < expected_date:
                break

        return streak
