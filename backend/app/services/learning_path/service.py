from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from app.schemas.learning_path import (
    GenerateLearningPathRequest,
    LearningPathResponse,
    LearningPathStageResponse,
    StageStatus,
)
from app.services.learning_path.generator import generate_learning_path_stages

if TYPE_CHECKING:
    from app.integrations.agents.client import AgentsClient
    from app.repositories.learning_path_repository import LearningPathRepository


class LearningPathService:
    def __init__(
        self,
        repo: LearningPathRepository,
        llm_client: AgentsClient | None = None,
    ) -> None:
        self._repo = repo
        self._llm_client = llm_client

    async def get_learning_path(
        self, document_id: UUID, user_id: UUID, mode: str
    ) -> LearningPathResponse | None:
        path = await self._repo.get_by_document(document_id, user_id, mode)
        if not path:
            return None

        stages = await self._repo.get_stages(path.id)
        completed_count = sum(1 for s in stages if s.completed_at is not None)
        current_index = completed_count

        stage_responses = []
        for idx, stage in enumerate(stages):
            if stage.completed_at is not None:
                status = StageStatus.COMPLETED
            elif idx == current_index:
                status = StageStatus.UNLOCKED
            else:
                status = StageStatus.LOCKED

            stage_responses.append(
                LearningPathStageResponse(
                    stage_index=idx,
                    stage_id=stage.stage_id,
                    status=status,
                    best_run_id=stage.best_run_id,
                    best_score=stage.best_score,
                    completed_at=stage.completed_at,
                )
            )

        return LearningPathResponse(
            document_id=document_id,
            mode=mode,
            stages=stage_responses,
            current_stage_index=current_index,
            completed_stages_count=completed_count,
            total_stages_count=len(stages),
        )

    async def mark_stage_completed(
        self, path_id: UUID, stage_index: int, run_id: UUID, score: int
    ) -> None:
        stages = await self._repo.get_stages(path_id)
        if stage_index < len(stages):
            await self._repo.update_stage_completion(stages[stage_index].id, run_id, score)

    async def generate_learning_path(
        self, request: GenerateLearningPathRequest, user_id: UUID
    ) -> LearningPathResponse:
        if not self._llm_client:
            raise RuntimeError("LLM client not configured")

        stages_data = await generate_learning_path_stages(
            llm_client=self._llm_client,
            knowledge_points=request.knowledge_points,
            mode=request.mode,
        )

        await self._repo.create(
            document_id=request.document_id,
            user_id=user_id,
            mode=request.mode,
            stages_data=stages_data,
        )

        result = await self.get_learning_path(request.document_id, user_id, request.mode)
        if result is None:
            raise RuntimeError("Failed to create learning path")
        return result
