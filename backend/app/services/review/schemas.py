from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


@dataclass(slots=True)
class FeedbackCreate:
    question_id: UUID
    document_id: UUID
    run_id: UUID | None
    feedback_type: str
    detail_text: str | None


@dataclass(slots=True)
class FeedbackRecord:
    id: UUID
    user_id: UUID
    question_id: UUID
    document_id: UUID
    run_id: UUID | None
    feedback_type: str
    detail_text: str | None
    status: str
    created_at: datetime


@dataclass(slots=True)
class MistakeRecord:
    id: UUID
    user_id: UUID
    question_id: UUID
    document_id: UUID
    run_id: UUID
    explanation: str | None
    created_at: datetime


@dataclass(slots=True)
class MistakeWithEmbedding:
    mistake: MistakeRecord
    embedding: list[float] | None
    embedding_model: str | None


@dataclass(slots=True)
class SimilarMistake:
    mistake_id: UUID
    question_id: UUID
    document_id: UUID
    similarity: float
    explanation: str | None


@dataclass(slots=True)
class EnhancedExplanation:
    mistake_id: UUID
    base_explanation: str | None
    enhanced_explanation: str
    similar_mistakes: list[SimilarMistake]
    document_context: str | None


@dataclass(slots=True)
class FeedbackSummary:
    job_id: UUID
    feedback_count: int
    summary: str
    rule_candidates: list[RuleCandidate]


@dataclass(slots=True)
class RuleCandidate:
    id: UUID
    rule_type: str
    title: str
    content: str
    status: str
    source_job_id: UUID


@dataclass(slots=True)
class RuleCandidateCreate:
    rule_type: str
    title: str
    content: str
    source_job_id: UUID
