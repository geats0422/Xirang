from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from app.db.models.learning_path import LearningPath, LearningPathStage

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class LearningPathRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_document(
        self, document_id: UUID, user_id: UUID, mode: str
    ) -> LearningPath | None:
        stmt = select(LearningPath).where(
            LearningPath.document_id == document_id,
            LearningPath.user_id == user_id,
            LearningPath.mode == mode,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        document_id: UUID,
        user_id: UUID,
        mode: str,
        stages_data: list[dict[str, object]],
    ) -> LearningPath:
        path = LearningPath(
            user_id=user_id,
            document_id=document_id,
            mode=mode,
            path_structure={"stages": stages_data},
        )
        self._session.add(path)
        await self._session.flush()

        for idx, stage_data in enumerate(stages_data):
            stage = LearningPathStage(
                path_id=path.id,
                stage_index=idx,
                stage_id=stage_data["stage_id"],
            )
            self._session.add(stage)

        await self._session.commit()
        await self._session.refresh(path)
        return path

    async def get_stages(self, path_id: UUID) -> list[LearningPathStage]:
        stmt = (
            select(LearningPathStage)
            .where(LearningPathStage.path_id == path_id)
            .order_by(LearningPathStage.stage_index)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_stage_completion(self, stage_id: UUID, run_id: UUID, score: int) -> None:
        stmt = select(LearningPathStage).where(LearningPathStage.id == stage_id)
        result = await self._session.execute(stmt)
        stage = result.scalar_one()
        if score > stage.best_score:
            stage.best_run_id = run_id
            stage.best_score = score
        if score > 0:
            stage.completed_at = datetime.utcnow()
        await self._session.commit()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
