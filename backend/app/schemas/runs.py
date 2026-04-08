from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.runs import RunMode, RunStatus


class RunCreateRequest(BaseModel):
    document_id: UUID | None = None
    mode: RunMode
    question_count: int = Field(ge=1, le=50)


class QuestionOptionResponse(BaseModel):
    id: str
    text: str


class QuestionResponse(BaseModel):
    id: UUID
    document_id: UUID
    question_text: str
    question_type: str
    options: list[QuestionOptionResponse]
    difficulty: int
    chapter_reference: str | None = None


class RunCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: UUID
    document_id: UUID | None
    mode: RunMode
    status: RunStatus
    questions: list[QuestionResponse]


class AnswerSubmitRequest(BaseModel):
    question_id: UUID
    selected_option_ids: list[UUID]
    answer_time_ms: int | None = None


class AnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    question_id: UUID
    selected_option_ids: list[str] = Field(default_factory=list)
    is_correct: bool
    answer_time_ms: int | None = None
    answered_at: datetime | None = None


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    document_id: UUID | None
    mode: RunMode
    status: RunStatus
    score: int
    total_questions: int
    correct_answers: int
    combo_count: int
    started_at: datetime
    ended_at: datetime | None = None


class SettlementResponse(BaseModel):
    run_id: UUID
    xp_earned: int
    coins_earned: int
    combo_max: int
    accuracy: float
    correct_count: int
    total_count: int


class AnswerSubmitResponse(BaseModel):
    answer: AnswerResponse
    is_correct: bool
    run: RunResponse
    settlement: SettlementResponse | None = None


class RunListResponse(BaseModel):
    runs: list[RunResponse]
    total: int
