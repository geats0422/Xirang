from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from app.db.models.runs import Run


@dataclass(slots=True)
class QuestionData:
    id: UUID
    document_id: UUID
    question_text: str
    question_type: str
    options: list[dict[str, str]]
    correct_option_ids: list[UUID]
    difficulty: int
    chapter_reference: str | None = None
    source_locator: str | None = None
    supporting_excerpt: str | None = None


@dataclass(slots=True)
class RunCreateResult:
    run: Run
    questions: list[QuestionData]


@dataclass(slots=True)
class AnswerResult:
    id: UUID
    run_id: UUID
    question_id: UUID
    selected_option_ids: list[UUID]
    is_correct: bool
    time_spent_ms: int | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class SubmitAnswerResult:
    answer: AnswerResult
    is_correct: bool
    run: Run
    settlement: Settlement | None = None


@dataclass(slots=True)
class Settlement:
    run_id: UUID
    xp_earned: int
    coins_earned: int
    combo_max: int
    accuracy: float
    correct_count: int
    total_count: int
