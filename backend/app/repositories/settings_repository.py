from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import select

from app.db.models.profile import UserSetting

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_settings(self, user_id: UUID) -> UserSetting | None:
        stmt = select(UserSetting).where(UserSetting.user_id == user_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_settings(self, user_id: UUID, **fields: Any) -> UserSetting:
        settings = await self.get_settings(user_id)
        if settings is None:
            settings = UserSetting(user_id=user_id)
            self._session.add(settings)
            await self._session.flush()

        for key, value in fields.items():
            setattr(settings, key, value)

        await self._session.flush()
        stmt = select(UserSetting).where(UserSetting.user_id == user_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def commit(self) -> None:
        await self._session.commit()
