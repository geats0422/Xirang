from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.db.models.runs import RunMode, RunStatus
from app.services.runs.exceptions import DuplicateAnswerError, RunNotCompletedError
from app.services.runs.schemas import AnswerResult, QuestionData
from app.services.runs.service import RunService


@dataclass
class FakeRun:
    id: UUID
    user_id: UUID
    document_id: UUID
    mode: RunMode
    status: RunStatus
    score: int
    total_questions: int
    correct_answers: int
    combo_count: int
    started_at: datetime
    ended_at: datetime | None = None


@dataclass
class FakeSettlementRow:
    run_id: UUID
    user_id: UUID
    xp_gained: int
    coin_reward: int
    combo_count: int
    accuracy_pct: float
    payload: dict[str, object]


class InMemoryRunRepository:
    def __init__(self, questions: list[QuestionData]) -> None:
        self._source_questions = questions
        self._runs: dict[UUID, FakeRun] = {}
        self._run_questions: dict[UUID, list[dict[str, Any]]] = {}
        self._answers: dict[UUID, list[AnswerResult]] = {}
        self._settlements: dict[UUID, FakeSettlementRow] = {}

    async def create_run(
        self,
        *,
        user_id: UUID,
        document_id: UUID,
        mode: RunMode,
        total_questions: int,
    ) -> FakeRun:
        run = FakeRun(
            id=uuid4(),
            user_id=user_id,
            document_id=document_id,
            mode=mode,
            status=RunStatus.RUNNING,
            score=0,
            total_questions=total_questions,
            correct_answers=0,
            combo_count=0,
            started_at=datetime.now(UTC),
        )
        self._runs[run.id] = run
        return run

    async def get_run(self, run_id: UUID) -> FakeRun | None:
        return self._runs.get(run_id)

    async def list_runs(self, user_id: UUID) -> list[FakeRun]:
        return [run for run in self._runs.values() if run.user_id == user_id]

    async def update_run(
        self,
        run_id: UUID,
        *,
        status: RunStatus | None = None,
        score: int | None = None,
        total_questions: int | None = None,
        correct_answers: int | None = None,
        combo_count: int | None = None,
        ended_at: datetime | None = None,
    ) -> None:
        run = self._runs[run_id]
        if status is not None:
            run.status = status
        if score is not None:
            run.score = score
        if total_questions is not None:
            run.total_questions = total_questions
        if correct_answers is not None:
            run.correct_answers = correct_answers
        if combo_count is not None:
            run.combo_count = combo_count
        if ended_at is not None:
            run.ended_at = ended_at

    async def list_document_questions(
        self,
        *,
        document_id: UUID,
        mode: RunMode,
        count: int,
    ) -> list[QuestionData]:
        return [q for q in self._source_questions if q.document_id == document_id][:count]

    async def add_run_questions(self, run_id: UUID, questions: list[QuestionData]) -> None:
        self._run_questions[run_id] = [
            {
                "run_question_id": uuid4(),
                "question_id": question.id,
                "correct_option_ids": [str(v) for v in question.correct_option_ids],
            }
            for question in questions
        ]

    async def get_run_questions(self, run_id: UUID) -> list[dict[str, Any]]:
        return self._run_questions.get(run_id, [])

    async def has_question_answer(self, run_id: UUID, question_id: UUID) -> bool:
        answers = self._answers.get(run_id, [])
        return any(answer.question_id == question_id for answer in answers)

    async def record_answer(
        self,
        run_id: UUID,
        question_id: UUID,
        selected_option_ids: list[str],
        is_correct: bool,
        answer_time_ms: int | None,
    ) -> AnswerResult:
        result = AnswerResult(
            id=uuid4(),
            run_id=run_id,
            question_id=question_id,
            selected_option_ids=[UUID(v) for v in selected_option_ids],
            is_correct=is_correct,
            time_spent_ms=answer_time_ms,
            created_at=datetime.now(UTC),
        )
        self._answers.setdefault(run_id, []).append(result)
        return result

    async def count_answers(self, run_id: UUID) -> int:
        return len(self._answers.get(run_id, []))

    async def count_correct_answers(self, run_id: UUID) -> int:
        return sum(1 for answer in self._answers.get(run_id, []) if answer.is_correct)

    async def get_combo_count(self, run_id: UUID) -> int:
        combo = 0
        for answer in reversed(self._answers.get(run_id, [])):
            if not answer.is_correct:
                break
            combo += 1
        return combo

    async def get_combo_max(self, run_id: UUID) -> int:
        combo = 0
        best = 0
        for answer in self._answers.get(run_id, []):
            if answer.is_correct:
                combo += 1
                best = max(best, combo)
            else:
                combo = 0
        return best

    async def upsert_settlement(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        xp_gained: int,
        coin_reward: int,
        combo_count: int,
        accuracy_pct: float,
        payload: dict[str, object],
    ) -> FakeSettlementRow:
        row = FakeSettlementRow(
            run_id=run_id,
            user_id=user_id,
            xp_gained=xp_gained,
            coin_reward=coin_reward,
            combo_count=combo_count,
            accuracy_pct=accuracy_pct,
            payload=payload,
        )
        self._settlements[run_id] = row
        return row

    async def get_settlement(self, run_id: UUID) -> FakeSettlementRow | None:
        return self._settlements.get(run_id)

    async def commit(self) -> None:
        return

    async def rollback(self) -> None:
        return


class FakeWalletService:
    def __init__(self) -> None:
        self.credits: list[dict[str, object]] = []

    async def credit(self, **payload: object) -> dict[str, object]:
        self.credits.append(payload)
        return payload


def _build_questions(document_id: UUID) -> list[QuestionData]:
    return [
        QuestionData(
            id=uuid4(),
            document_id=document_id,
            question_text=f"Question {i + 1}",
            question_type="single_choice",
            options=[
                {"id": str(uuid4()), "text": "A"},
                {"id": str(uuid4()), "text": "B"},
            ],
            correct_option_ids=[],
            difficulty=1,
        )
        for i in range(3)
    ]


@pytest.mark.asyncio
async def test_real_run_service_completes_and_generates_settlement() -> None:
    user_id = uuid4()
    document_id = uuid4()
    questions = _build_questions(document_id)
    for question in questions:
        question.correct_option_ids = [UUID(question.options[0]["id"])]

    repository = InMemoryRunRepository(questions)
    wallet_service = FakeWalletService()
    service = RunService(repository=repository, wallet_service=wallet_service)

    run, generated = await service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=RunMode.ENDLESS,
        question_count=3,
    )
    assert len(generated) == 3

    for question in generated:
        await service.submit_answer(
            run_id=run.id,
            question_id=question.id,
            selected_option_ids=[question.correct_option_ids[0]],
        )

    completed_run = await service.get_run(run.id)
    assert completed_run.status == RunStatus.COMPLETED

    settlement = await service.get_settlement(run.id)
    assert settlement.correct_count == 3
    assert settlement.total_count == 3
    assert settlement.xp_earned > 0
    assert len(wallet_service.credits) == 2
    credited_assets = {str(item["asset_code"]) for item in wallet_service.credits}
    assert credited_assets == {"COIN", "XP"}


@pytest.mark.asyncio
async def test_real_run_service_rejects_duplicate_answer() -> None:
    user_id = uuid4()
    document_id = uuid4()
    questions = _build_questions(document_id)[:2]
    questions[0].correct_option_ids = [UUID(questions[0].options[0]["id"])]
    questions[1].correct_option_ids = [UUID(questions[1].options[0]["id"])]

    repository = InMemoryRunRepository(questions)
    service = RunService(repository=repository)
    run, generated = await service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=RunMode.ENDLESS,
        question_count=2,
    )

    await service.submit_answer(
        run_id=run.id,
        question_id=generated[0].id,
        selected_option_ids=[generated[0].correct_option_ids[0]],
    )

    with pytest.raises(DuplicateAnswerError):
        await service.submit_answer(
            run_id=run.id,
            question_id=generated[0].id,
            selected_option_ids=[generated[0].correct_option_ids[0]],
        )


@pytest.mark.asyncio
async def test_real_run_service_get_settlement_requires_completion() -> None:
    user_id = uuid4()
    document_id = uuid4()
    questions = _build_questions(document_id)
    questions[0].correct_option_ids = [UUID(questions[0].options[0]["id"])]

    repository = InMemoryRunRepository(questions)
    service = RunService(repository=repository)
    run, _ = await service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=RunMode.ENDLESS,
        question_count=1,
    )

    with pytest.raises(RunNotCompletedError):
        await service.get_settlement(run.id)
