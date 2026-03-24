from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreateRequest(BaseModel):
    question_id: UUID
    document_id: UUID
    run_id: UUID | None = None
    feedback_type: str = Field(..., min_length=1, max_length=50)
    detail_text: str | None = Field(None, max_length=2000)


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    question_id: UUID
    document_id: UUID
    run_id: UUID | None
    feedback_type: str
    detail_text: str | None
    status: str
    created_at: datetime


class FeedbackListResponse(BaseModel):
    items: list[FeedbackResponse]
    total: int


class MistakeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    question_id: UUID
    document_id: UUID
    run_id: UUID
    explanation: str | None
    created_at: datetime


class MistakeListResponse(BaseModel):
    items: list[MistakeResponse]
    total: int


class ExplainMistakeRequest(BaseModel):
    question_text: str = Field(..., min_length=1)
    document_context: str | None = None


class ExplainMistakeResponse(BaseModel):
    mistake_id: UUID
    explanation: str


class FeedbackSummaryRequest(BaseModel):
    feedback_ids: list[UUID] = Field(..., min_length=1)


class FeedbackSummaryResponse(BaseModel):
    summary: str
    suggestions: list[dict[str, str]]


class RuleCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_type: str
    title: str
    content: str
    status: str
    source_job_id: UUID
    created_at: datetime | None = None


class RuleCandidateListResponse(BaseModel):
    items: list[RuleCandidateResponse]
    total: int
