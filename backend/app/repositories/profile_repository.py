from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from app.db.models.profile import Profile

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_profile(self, user_id: UUID) -> Profile | None:
        stmt = select(Profile).where(Profile.user_id == user_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
