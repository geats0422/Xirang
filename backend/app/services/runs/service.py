from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol, cast
from uuid import UUID

from app.db.models.runs import RunMode, RunStatus
from app.services.runs.exceptions import (
    DuplicateAnswerError,
    InvalidRunStateError,
    QuestionNotFoundError,
    RunNotCompletedError,
    RunNotFoundError,
)
from app.services.runs.schemas import AnswerResult, QuestionData, Settlement, SubmitAnswerResult


class RunRepositoryProtocol(Protocol):
    async def create_run(
        self,
        *,
        user_id: UUID,
        document_id: UUID,
        mode: RunMode,
        total_questions: int,
    ) -> Any: ...

    async def get_run(self, run_id: UUID) -> Any: ...
    async def list_runs(self, user_id: UUID) -> list[Any]: ...

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
    ) -> None: ...

    async def list_document_questions(
        self,
        *,
        document_id: UUID,
        mode: RunMode,
        count: int,
    ) -> list[QuestionData]: ...

    async def add_run_questions(self, run_id: UUID, questions: list[QuestionData]) -> None: ...
    async def get_run_questions(self, run_id: UUID) -> list[dict[str, Any]]: ...
    async def has_question_answer(self, run_id: UUID, question_id: UUID) -> bool: ...
    async def record_answer(
        self,
        run_id: UUID,
        question_id: UUID,
        selected_option_ids: list[str],
        is_correct: bool,
        answer_time_ms: int | None,
    ) -> AnswerResult: ...

    async def count_answers(self, run_id: UUID) -> int: ...
    async def count_correct_answers(self, run_id: UUID) -> int: ...
    async def get_combo_count(self, run_id: UUID) -> int: ...
    async def get_combo_max(self, run_id: UUID) -> int: ...

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
    ) -> Any: ...

    async def get_settlement(self, run_id: UUID) -> Any | None: ...

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class RunService:
    def __init__(self, *, repository: Any, wallet_service: Any | None = None) -> None:
        self._repository = cast("RunRepositoryProtocol", repository)
        self._wallet_service = wallet_service

    async def create_run(
        self,
        *,
        user_id: UUID,
        document_id: UUID,
        mode: RunMode,
        question_count: int,
    ) -> tuple[Any, list[QuestionData]]:
        questions = await self._repository.list_document_questions(
            document_id=document_id,
            mode=mode,
            count=question_count,
        )
        if not questions:
            raise QuestionNotFoundError(f"No questions available for document {document_id}")

        run = await self._repository.create_run(
            user_id=user_id,
            document_id=document_id,
            mode=mode,
            total_questions=len(questions),
        )
        await self._repository.add_run_questions(run.id, questions)
        await self._repository.commit()
        return run, questions

    async def get_run(self, run_id: UUID, owner_user_id: UUID | None = None) -> Any:
        run = await self._repository.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")
        if owner_user_id is not None and run.user_id != owner_user_id:
            raise RunNotFoundError(f"Run {run_id} not found")
        return run

    async def list_runs(self, user_id: UUID) -> list[Any]:
        return await self._repository.list_runs(user_id)

    async def submit_answer(
        self,
        *,
        run_id: UUID,
        question_id: UUID,
        selected_option_ids: list[UUID],
        answer_time_ms: int | None = None,
    ) -> SubmitAnswerResult:
        run = await self._repository.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")
        if run.status != RunStatus.RUNNING:
            raise InvalidRunStateError(f"Run {run_id} is not running")

        if await self._repository.has_question_answer(run_id, question_id):
            raise DuplicateAnswerError(f"Question {question_id} already answered")

        run_questions = await self._repository.get_run_questions(run_id)
        target_question: dict[str, Any] | None = None
        for item in run_questions:
            if item["question_id"] == question_id:
                target_question = item
                break

        if target_question is None:
            raise QuestionNotFoundError(f"Question {question_id} not in run {run_id}")

        provided_ids = {str(v) for v in selected_option_ids}
        correct_ids = {str(v) for v in target_question.get("correct_option_ids", [])}
        is_correct = provided_ids == correct_ids

        answer = await self._repository.record_answer(
            run_id,
            question_id,
            [str(v) for v in selected_option_ids],
            is_correct,
            answer_time_ms,
        )

        answered_count = await self._repository.count_answers(run_id)
        correct_count = await self._repository.count_correct_answers(run_id)
        combo_count = await self._repository.get_combo_count(run_id)
        score = self._calculate_score(
            mode=run.mode,
            correct_count=correct_count,
            answered_count=answered_count,
            combo_count=combo_count,
        )

        settlement: Settlement | None = None
        run_status: RunStatus = RunStatus.RUNNING
        ended_at: datetime | None = None
        if answered_count >= run.total_questions:
            run_status = RunStatus.COMPLETED
            ended_at = datetime.now(UTC)
            settlement = await self._build_settlement(
                run_id=run.id,
                user_id=run.user_id,
                mode=run.mode,
                correct_count=correct_count,
                total_count=run.total_questions,
            )

        await self._repository.update_run(
            run_id,
            status=run_status,
            score=score,
            total_questions=run.total_questions,
            correct_answers=correct_count,
            combo_count=combo_count,
            ended_at=ended_at,
        )

        await self._repository.commit()
        refreshed_run = await self.get_run(run_id)
        return SubmitAnswerResult(
            answer=answer,
            is_correct=is_correct,
            run=refreshed_run,
            settlement=settlement,
        )

    async def get_settlement(self, run_id: UUID) -> Settlement:
        run = await self._repository.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")
        if run.status != RunStatus.COMPLETED:
            raise RunNotCompletedError(f"Run {run_id} not completed")

        stored = await self._repository.get_settlement(run_id)
        if stored is None:
            return await self._build_settlement(
                run_id=run.id,
                user_id=run.user_id,
                mode=run.mode,
                correct_count=run.correct_answers,
                total_count=run.total_questions,
            )

        return Settlement(
            run_id=stored.run_id,
            xp_earned=int(stored.xp_gained),
            coins_earned=int(stored.coin_reward),
            combo_max=int(stored.combo_count),
            accuracy=float(stored.accuracy_pct),
            correct_count=run.correct_answers,
            total_count=run.total_questions,
        )

    async def _build_settlement(
        self,
        *,
        run_id: UUID,
        user_id: UUID,
        mode: RunMode,
        correct_count: int,
        total_count: int,
    ) -> Settlement:
        combo_max = await self._repository.get_combo_max(run_id)
        score = self._calculate_score(
            mode=mode,
            correct_count=correct_count,
            answered_count=total_count,
            combo_count=combo_max,
        )
        accuracy = (correct_count / total_count) if total_count > 0 else 0.0
        coins = max(0, score // 10)

        await self._repository.upsert_settlement(
            run_id=run_id,
            user_id=user_id,
            xp_gained=score,
            coin_reward=coins,
            combo_count=combo_max,
            accuracy_pct=accuracy,
            payload={
                "correct_count": correct_count,
                "total_count": total_count,
                "accuracy": accuracy,
            },
        )

        if self._wallet_service is not None:
            await self._wallet_service.credit(
                user_id=user_id,
                amount=coins,
                asset_code="COIN",
                reason_code="run_settlement",
                source_type="run",
                source_id=run_id,
                idempotency_key=f"run:{run_id}:coins",
            )
            await self._wallet_service.credit(
                user_id=user_id,
                amount=score,
                asset_code="XP",
                reason_code="run_settlement",
                source_type="run",
                source_id=run_id,
                idempotency_key=f"run:{run_id}:xp",
            )
        return Settlement(
            run_id=run_id,
            xp_earned=score,
            coins_earned=coins,
            combo_max=combo_max,
            accuracy=accuracy,
            correct_count=correct_count,
            total_count=total_count,
        )

    @staticmethod
    def _calculate_score(
        *,
        mode: RunMode,
        correct_count: int,
        answered_count: int,
        combo_count: int,
    ) -> int:
        if answered_count <= 0:
            return 0

        base = correct_count * 10
        if mode == RunMode.SPEED:
            base = int(base * 1.5)
        if mode == RunMode.DRAFT:
            base = int(base * 1.2)

        combo_multiplier = 1 + (combo_count * 0.1) if combo_count > 0 else 1
        return int(base * combo_multiplier)
