from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StageStatus:
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    COMPLETED = "completed"


class LearningPathStageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stage_index: int
    stage_id: str
    status: str
    best_run_id: UUID | None = None
    best_score: int = 0
    completed_at: datetime | None = None


class LearningPathResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    mode: str
    stages: list[LearningPathStageResponse]
    current_stage_index: int
    completed_stages_count: int
    total_stages_count: int


class GenerateLearningPathRequest(BaseModel):
    document_id: UUID
    mode: str
    knowledge_points: list[str] = Field(default_factory=list)
