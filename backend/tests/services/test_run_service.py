from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.db.models.runs import RunMode, RunStatus
from app.services.runs.exceptions import (
    DuplicateAnswerError,
    InvalidRunStateError,
    RunNotCompletedError,
    RunNotFoundError,
)
from app.services.runs.schemas import Settlement


@dataclass
class FakeQuestion:
    id: UUID
    document_id: UUID
    question_type: str
    prompt: str
    options: list[dict[str, str]]
    correct_option_ids: list[UUID]
    difficulty: int = 1


@dataclass
class FakeRun:
    id: UUID
    owner_user_id: UUID
    document_id: UUID
    mode: RunMode
    status: RunStatus
    question_count: int
    questions: list[dict[str, Any]]
    score: int = 0
    combo: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None

    def mark_answered(self, question_id: UUID, is_correct: bool) -> None:
        for q in self.questions:
            if q["id"] == question_id:
                q["answered"] = True
                q["is_correct"] = is_correct
                break

    def is_answered(self, question_id: UUID) -> bool:
        for q in self.questions:
            if q["id"] == question_id:
                return q.get("answered", False)
        return False

    @property
    def answered_count(self) -> int:
        return sum(1 for q in self.questions if q.get("answered"))

    @property
    def correct_count(self) -> int:
        return sum(1 for q in self.questions if q.get("is_correct"))


@dataclass
class FakeRunRepository:
    runs: dict[UUID, FakeRun] = field(default_factory=dict)
    answers: dict[tuple[UUID, UUID], bool] = field(default_factory=dict)

    async def create_run(
        self,
        *,
        owner_user_id: UUID,
        document_id: UUID,
        mode: RunMode,
        question_count: int,
        questions: list[dict[str, Any]],
    ) -> FakeRun:
        run = FakeRun(
            id=uuid4(),
            owner_user_id=owner_user_id,
            document_id=document_id,
            mode=mode,
            status=RunStatus.RUNNING,
            question_count=question_count,
            questions=questions,
        )
        self.runs[run.id] = run
        return run

    async def get_run(self, run_id: UUID) -> FakeRun | None:
        return self.runs.get(run_id)

    async def update_run(
        self,
        run_id: UUID,
        *,
        status: RunStatus | None = None,
        score: int | None = None,
        combo: int | None = None,
        finished_at: datetime | None = None,
    ) -> None:
        run = self.runs.get(run_id)
        if run:
            if status is not None:
                run.status = status
            if score is not None:
                run.score = score
            if combo is not None:
                run.combo = combo
            if finished_at is not None:
                run.finished_at = finished_at

    async def record_answer(
        self,
        run_id: UUID,
        question_id: UUID,
        is_correct: bool,
    ) -> None:
        key = (run_id, question_id)
        if key in self.answers:
            raise DuplicateAnswerError("Answer already recorded")
        self.answers[key] = is_correct
        run = self.runs.get(run_id)
        if run:
            run.mark_answered(question_id, is_correct)

    async def has_answer(self, run_id: UUID, question_id: UUID) -> bool:
        return (run_id, question_id) in self.answers

    async def commit(self) -> None:
        pass


@dataclass
class FakeQuestionSelector:
    def select_questions(
        self,
        questions: list[FakeQuestion],
        document_id: UUID,
        mode: RunMode,
        count: int,
    ) -> list[FakeQuestion]:
        if mode == RunMode.ENDLESS:
            return questions[:count]
        elif mode == RunMode.SPEED:
            return sorted(questions, key=lambda q: q.difficulty, reverse=True)[:count]
        elif mode == RunMode.DRAFT:
            hard_questions = [q for q in questions if q.difficulty >= 3]
            return hard_questions[:count] if hard_questions else questions[:count]
        return questions[:count]


@dataclass
class FakeScoringEngine:
    def calculate_score(
        self,
        mode: RunMode,
        correct_count: int,
        total_count: int,
        combo: int,
    ) -> int:
        base_score = correct_count * 10
        combo_bonus = 1 + (combo * 0.1) if combo > 0 else 1
        if mode == RunMode.SPEED:
            base_score = int(base_score * 1.5)
        return int(base_score * combo_bonus)


@dataclass
class FakeSettlementEngine:
    def generate_settlement(
        self,
        run: FakeRun,
    ) -> Settlement:
        correct_count = run.correct_count
        total_count = run.question_count
        accuracy = correct_count / total_count if total_count > 0 else 0.0
        scoring = FakeScoringEngine()
        score = scoring.calculate_score(
            mode=run.mode,
            correct_count=correct_count,
            total_count=total_count,
            combo=run.combo,
        )
        return Settlement(
            run_id=run.id,
            xp_earned=score,
            coins_earned=int(score * 0.1),
            combo_max=run.combo,
            accuracy=accuracy,
            correct_count=correct_count,
            total_count=total_count,
        )


class RunService:
    def __init__(
        self,
        repository: FakeRunRepository,
        question_selector: FakeQuestionSelector,
        scoring_engine: FakeScoringEngine,
        settlement_engine: FakeSettlementEngine,
    ) -> None:
        self._repository = repository
        self._question_selector = question_selector
        self._scoring_engine = scoring_engine
        self._settlement_engine = settlement_engine

    async def create_run(
        self,
        *,
        owner_user_id: UUID,
        document_id: UUID,
        mode: RunMode,
        question_count: int,
        questions: list[FakeQuestion],
    ) -> tuple[FakeRun, list[FakeQuestion]]:
        selected = self._question_selector.select_questions(
            questions, document_id, mode, question_count
        )
        question_dicts = [
            {
                "id": q.id,
                "document_id": q.document_id,
                "question_type": q.question_type,
                "prompt": q.prompt,
                "options": q.options,
                "correct_option_ids": q.correct_option_ids,
                "difficulty": q.difficulty,
            }
            for q in selected
        ]
        run = await self._repository.create_run(
            owner_user_id=owner_user_id,
            document_id=document_id,
            mode=mode,
            question_count=len(selected),
            questions=question_dicts,
        )
        await self._repository.commit()
        return run, selected

    async def get_run(self, run_id: UUID, owner_user_id: UUID | None = None) -> FakeRun:
        run = await self._repository.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")
        if owner_user_id and run.owner_user_id != owner_user_id:
            raise RunNotFoundError(f"Run {run_id} not found")
        return run

    async def list_runs(self, owner_user_id: UUID) -> list[FakeRun]:
        return [r for r in self._repository.runs.values() if r.owner_user_id == owner_user_id]

    async def submit_answer(
        self,
        run_id: UUID,
        question_id: UUID,
        selected_option_ids: list[UUID],
    ) -> tuple[bool, FakeRun, Settlement | None]:
        run = await self._repository.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")

        if run.status != RunStatus.RUNNING:
            raise InvalidRunStateError(f"Run {run_id} is not running")

        if await self._repository.has_answer(run_id, question_id):
            raise DuplicateAnswerError(f"Question {question_id} already answered")

        question_data = None
        for q in run.questions:
            if q["id"] == question_id:
                question_data = q
                break

        if question_data is None:
            raise ValueError(f"Question {question_id} not in run")

        correct_ids = set(question_data["correct_option_ids"])
        is_correct = correct_ids == set(selected_option_ids)

        await self._repository.record_answer(run_id, question_id, is_correct)

        if is_correct:
            run.combo += 1
        else:
            run.combo = 0

        run.score = self._scoring_engine.calculate_score(
            mode=run.mode,
            correct_count=run.correct_count,
            total_count=run.answered_count,
            combo=run.combo,
        )

        settlement = None
        if run.answered_count >= run.question_count:
            run.status = RunStatus.COMPLETED
            run.finished_at = datetime.now(UTC)
            settlement = self._settlement_engine.generate_settlement(run)

        await self._repository.update_run(
            run_id,
            status=run.status,
            score=run.score,
            combo=run.combo,
            finished_at=run.finished_at,
        )
        await self._repository.commit()

        return is_correct, run, settlement

    async def get_settlement(self, run_id: UUID) -> Settlement:
        run = await self._repository.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")

        if run.status != RunStatus.COMPLETED:
            raise RunNotCompletedError(f"Run {run_id} not completed")

        return self._settlement_engine.generate_settlement(run)


def build_run_service() -> tuple[RunService, FakeRunRepository]:
    repo = FakeRunRepository()
    selector = FakeQuestionSelector()
    scoring = FakeScoringEngine()
    settlement = FakeSettlementEngine()
    service = RunService(
        repository=repo,
        question_selector=selector,
        scoring_engine=scoring,
        settlement_engine=settlement,
    )
    return service, repo


def make_questions(count: int, document_id: UUID) -> list[FakeQuestion]:
    questions = []
    for i in range(count):
        option_ids = [uuid4(), uuid4(), uuid4(), uuid4()]
        questions.append(
            FakeQuestion(
                id=uuid4(),
                document_id=document_id,
                question_type="single_choice",
                prompt=f"Question {i + 1}?",
                options=[
                    {"id": str(option_ids[0]), "text": "A"},
                    {"id": str(option_ids[1]), "text": "B"},
                    {"id": str(option_ids[2]), "text": "C"},
                    {"id": str(option_ids[3]), "text": "D"},
                ],
                correct_option_ids=[option_ids[0]],
                difficulty=(i % 5) + 1,
            )
        )
    return questions


class TestRunService:
    @pytest.mark.asyncio
    async def test_create_run_creates_run_with_selected_questions(self) -> None:
        service, _repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(10, doc_id)

        run, selected = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=5,
            questions=questions,
        )

        assert run.id is not None
        assert run.owner_user_id == user_id
        assert run.document_id == doc_id
        assert run.mode == RunMode.ENDLESS
        assert run.status == RunStatus.RUNNING
        assert len(selected) == 5

    @pytest.mark.asyncio
    async def test_create_run_respects_question_count(self) -> None:
        service, _repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(10, doc_id)

        _run, selected = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=3,
            questions=questions,
        )

        assert len(selected) == 3

    @pytest.mark.asyncio
    async def test_create_run_different_modes(self) -> None:
        service, _repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(10, doc_id)

        for mode in [RunMode.ENDLESS, RunMode.SPEED, RunMode.DRAFT, RunMode.REVIEW]:
            run, _ = await service.create_run(
                owner_user_id=user_id,
                document_id=doc_id,
                mode=mode,
                question_count=5,
                questions=questions,
            )
            assert run.mode == mode

    @pytest.mark.asyncio
    async def test_submit_answer_records_correct_answer(self) -> None:
        service, _repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(5, doc_id)

        run, selected = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=5,
            questions=questions,
        )

        question = selected[0]
        is_correct, updated_run, _settlement = await service.submit_answer(
            run_id=run.id,
            question_id=question.id,
            selected_option_ids=[question.correct_option_ids[0]],
        )

        assert is_correct is True
        assert updated_run.combo == 1
        assert updated_run.score > 0

    @pytest.mark.asyncio
    async def test_submit_answer_detects_incorrect_answer(self) -> None:
        service, _repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(5, doc_id)

        run, selected = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=5,
            questions=questions,
        )

        question = selected[0]
        wrong_id = uuid4()
        while wrong_id in question.correct_option_ids:
            wrong_id = uuid4()

        is_correct, updated_run, _ = await service.submit_answer(
            run_id=run.id,
            question_id=question.id,
            selected_option_ids=[wrong_id],
        )

        assert is_correct is False
        assert updated_run.combo == 0

    @pytest.mark.asyncio
    async def test_submit_answer_increases_combo_on_streak(self) -> None:
        service, repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(5, doc_id)

        run, selected = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=5,
            questions=questions,
        )

        for i in range(3):
            question = selected[i]
            await service.submit_answer(
                run_id=run.id,
                question_id=question.id,
                selected_option_ids=[question.correct_option_ids[0]],
            )

        run = await repo.get_run(run.id)
        assert run is not None
        assert run.combo == 3

    @pytest.mark.asyncio
    async def test_submit_answer_resets_combo_on_wrong_answer(self) -> None:
        service, repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(5, doc_id)

        run, selected = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=5,
            questions=questions,
        )

        for i in range(3):
            question = selected[i]
            await service.submit_answer(
                run_id=run.id,
                question_id=question.id,
                selected_option_ids=[question.correct_option_ids[0]],
            )

        wrong_question = selected[3]
        wrong_id = uuid4()
        await service.submit_answer(
            run_id=run.id,
            question_id=wrong_question.id,
            selected_option_ids=[wrong_id],
        )

        run = await repo.get_run(run.id)
        assert run is not None
        assert run.combo == 0

    @pytest.mark.asyncio
    async def test_submit_answer_rejects_duplicate_submission(self) -> None:
        service, _repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(5, doc_id)

        run, selected = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=5,
            questions=questions,
        )

        question = selected[0]
        await service.submit_answer(
            run_id=run.id,
            question_id=question.id,
            selected_option_ids=[question.correct_option_ids[0]],
        )

        with pytest.raises(DuplicateAnswerError):
            await service.submit_answer(
                run_id=run.id,
                question_id=question.id,
                selected_option_ids=[question.correct_option_ids[0]],
            )

    @pytest.mark.asyncio
    async def test_submit_answer_rejects_invalid_run_state(self) -> None:
        service, _repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(1, doc_id)

        run, selected = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=1,
            questions=questions,
        )

        question = selected[0]
        await service.submit_answer(
            run_id=run.id,
            question_id=question.id,
            selected_option_ids=[question.correct_option_ids[0]],
        )

        with pytest.raises(InvalidRunStateError):
            await service.submit_answer(
                run_id=run.id,
                question_id=uuid4(),
                selected_option_ids=[uuid4()],
            )

    @pytest.mark.asyncio
    async def test_submit_answer_returns_settlement_on_completion(self) -> None:
        service, _repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(1, doc_id)

        run, selected = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=1,
            questions=questions,
        )

        question = selected[0]
        _is_correct, updated_run, settlement = await service.submit_answer(
            run_id=run.id,
            question_id=question.id,
            selected_option_ids=[question.correct_option_ids[0]],
        )

        assert settlement is not None
        assert settlement.xp_earned > 0
        assert settlement.coins_earned >= 0
        assert updated_run.status == RunStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_get_settlement_returns_settlement_for_completed_run(self) -> None:
        service, _repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(1, doc_id)

        run, selected = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=1,
            questions=questions,
        )

        question = selected[0]
        await service.submit_answer(
            run_id=run.id,
            question_id=question.id,
            selected_option_ids=[question.correct_option_ids[0]],
        )

        settlement = await service.get_settlement(run.id)

        assert settlement is not None
        assert settlement.run_id == run.id
        assert settlement.xp_earned > 0

    @pytest.mark.asyncio
    async def test_get_settlement_raises_for_incomplete_run(self) -> None:
        service, _repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(5, doc_id)

        run, _ = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=5,
            questions=questions,
        )

        with pytest.raises(RunNotCompletedError):
            await service.get_settlement(run.id)

    @pytest.mark.asyncio
    async def test_get_run_raises_for_nonexistent_run(self) -> None:
        service, _repo = build_run_service()

        with pytest.raises(RunNotFoundError):
            await service.get_run(uuid4())

    @pytest.mark.asyncio
    async def test_list_runs_returns_only_owner_runs(self) -> None:
        service, _repo = build_run_service()
        user_id = uuid4()
        other_user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(5, doc_id)

        await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=5,
            questions=questions,
        )
        await service.create_run(
            owner_user_id=other_user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=5,
            questions=questions,
        )

        runs = await service.list_runs(owner_user_id=user_id)

        assert len(runs) == 1
        assert runs[0].owner_user_id == user_id

    @pytest.mark.asyncio
    async def test_scoring_engine_gives_bonus_for_speed_mode(self) -> None:
        service, repo = build_run_service()
        user_id = uuid4()
        doc_id = uuid4()
        questions = make_questions(5, doc_id)

        run_speed, selected_speed = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.SPEED,
            question_count=5,
            questions=questions,
        )

        run_endless, selected_endless = await service.create_run(
            owner_user_id=user_id,
            document_id=doc_id,
            mode=RunMode.ENDLESS,
            question_count=5,
            questions=questions,
        )

        for i in range(5):
            await service.submit_answer(
                run_id=run_speed.id,
                question_id=selected_speed[i].id,
                selected_option_ids=[selected_speed[i].correct_option_ids[0]],
            )
            await service.submit_answer(
                run_id=run_endless.id,
                question_id=selected_endless[i].id,
                selected_option_ids=[selected_endless[i].correct_option_ids[0]],
            )

        speed_run = await repo.get_run(run_speed.id)
        endless_run = await repo.get_run(run_endless.id)

        assert speed_run is not None
        assert endless_run is not None
        assert speed_run.score > endless_run.score
