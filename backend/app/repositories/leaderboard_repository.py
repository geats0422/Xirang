from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

from app.db.models.profile import Profile
from app.db.models.runs import Settlement

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class LeaderboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_global_leaderboard(self, limit: int) -> list[Any]:
        stmt = (
            select(
                Settlement.user_id,
                Profile.display_name,
                func.coalesce(func.sum(Settlement.xp_gained), 0).label("total_xp"),
            )
            .outerjoin(Profile, Profile.user_id == Settlement.user_id)
            .group_by(Settlement.user_id, Profile.display_name)
            .order_by(func.sum(Settlement.xp_gained).desc(), Settlement.user_id.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.all())
