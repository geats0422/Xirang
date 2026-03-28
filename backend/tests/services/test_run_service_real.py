from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.db.models.learning_paths import LearningPathNodeType, LearningPathProgressStatus
from app.db.models.runs import RunMode, RunStatus
from app.services.learning_paths.reward_policy import RewardPolicy
from app.services.runs.exceptions import (
    DuplicateAnswerError,
    QuestionNotFoundError,
    RunNotCompletedError,
)
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
    mode_state: dict[str, object]
    started_at: datetime
    source_path_version_id: UUID | None = None
    source_level_node_id: UUID | None = None
    is_legend_review: bool = False
    legend_reward_rate: float = 1.0
    version_reward_discount: float = 1.0
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


@dataclass
class FakeLearningPathProgress:
    user_id: UUID
    path_version_id: UUID
    node_id: UUID
    status: LearningPathProgressStatus
    first_completed_run_id: UUID
    completed_runs_count: int
    last_completed_at: datetime


@dataclass
class FakeLegendReviewProgress:
    user_id: UUID
    path_version_id: UUID
    unit_node_id: UUID
    legend_round_count: int
    last_legend_run_at: datetime


@dataclass
class FakeLearningPathNode:
    id: UUID
    node_type: LearningPathNodeType
    parent_node_id: UUID | None = None


@dataclass
class FakeDailyRewardCapUsage:
    xp_legend_earned: int
    coin_legend_earned: int


class InMemoryRunRepository:
    def __init__(self, questions: list[QuestionData]) -> None:
        self._source_questions = questions
        self._runs: dict[UUID, FakeRun] = {}
        self._run_questions: dict[UUID, list[dict[str, Any]]] = {}
        self._answers: dict[UUID, list[AnswerResult]] = {}
        self._settlements: dict[UUID, FakeSettlementRow] = {}
        self._learning_path_progress: dict[tuple[UUID, UUID, UUID], FakeLearningPathProgress] = {}
        self._legend_review_progress: dict[tuple[UUID, UUID, UUID], FakeLegendReviewProgress] = {}
        self._path_nodes: dict[UUID, FakeLearningPathNode] = {}
        self._path_version_meta: dict[UUID, tuple[UUID, str, int]] = {}
        self._latest_ready_versions: dict[tuple[UUID, str], int] = {}
        self._subscription_active = False
        self._daily_cap_usage: dict[tuple[UUID, date], FakeDailyRewardCapUsage] = {}

    async def create_run(
        self,
        *,
        user_id: UUID,
        document_id: UUID,
        mode: RunMode,
        total_questions: int,
        mode_state: dict[str, object] | None = None,
        source_path_version_id: UUID | None = None,
        source_level_node_id: UUID | None = None,
        is_legend_review: bool = False,
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
            mode_state=mode_state or {},
            started_at=datetime.now(UTC),
            source_path_version_id=source_path_version_id,
            source_level_node_id=source_level_node_id,
            is_legend_review=is_legend_review,
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
        mode_state: dict[str, object] | None = None,
        ended_at: datetime | None = None,
        legend_reward_rate: float | None = None,
        version_reward_discount: float | None = None,
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
        if mode_state is not None:
            run.mode_state = mode_state
        if ended_at is not None:
            run.ended_at = ended_at
        if legend_reward_rate is not None:
            run.legend_reward_rate = legend_reward_rate
        if version_reward_discount is not None:
            run.version_reward_discount = version_reward_discount

    async def list_document_questions(
        self,
        *,
        document_id: UUID,
        mode: RunMode,
        count: int,
        path_id: str | None = None,
    ) -> list[QuestionData]:
        return [q for q in self._source_questions if q.document_id == document_id][:count]

    async def add_run_questions(self, run_id: UUID, questions: list[QuestionData]) -> None:
        self._run_questions[run_id] = [
            {
                "run_question_id": uuid4(),
                "question_id": question.id,
                "options": question.options,
                "correct_option_ids": [str(v) for v in question.correct_option_ids],
                "explanation": question.explanation,
                "source_locator": question.source_locator,
                "supporting_excerpt": question.supporting_excerpt,
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

    async def upsert_learning_path_progress(
        self,
        *,
        user_id: UUID,
        path_version_id: UUID,
        node_id: UUID,
        completed_run_id: UUID,
        completed_at: datetime,
    ) -> None:
        key = (user_id, path_version_id, node_id)
        row = self._learning_path_progress.get(key)
        if row is None:
            self._learning_path_progress[key] = FakeLearningPathProgress(
                user_id=user_id,
                path_version_id=path_version_id,
                node_id=node_id,
                status=LearningPathProgressStatus.COMPLETED,
                first_completed_run_id=completed_run_id,
                completed_runs_count=1,
                last_completed_at=completed_at,
            )
            return

        row.status = LearningPathProgressStatus.COMPLETED
        row.completed_runs_count += 1
        row.last_completed_at = completed_at

    async def resolve_unit_node_id(self, *, node_id: UUID) -> UUID | None:
        node = self._path_nodes.get(node_id)
        if node is None:
            return None
        if node.node_type == LearningPathNodeType.UNIT:
            return node.id

        parent_id = node.parent_node_id
        while parent_id is not None:
            parent = self._path_nodes.get(parent_id)
            if parent is None:
                return None
            if parent.node_type == LearningPathNodeType.UNIT:
                return parent.id
            parent_id = parent.parent_node_id

        return None

    async def increment_legend_review_progress(
        self,
        *,
        user_id: UUID,
        path_version_id: UUID,
        unit_node_id: UUID,
        completed_at: datetime,
    ) -> None:
        key = (user_id, path_version_id, unit_node_id)
        row = self._legend_review_progress.get(key)
        if row is None:
            self._legend_review_progress[key] = FakeLegendReviewProgress(
                user_id=user_id,
                path_version_id=path_version_id,
                unit_node_id=unit_node_id,
                legend_round_count=1,
                last_legend_run_at=completed_at,
            )
            return

        row.legend_round_count += 1
        row.last_legend_run_at = completed_at

    async def get_path_version_meta(self, *, path_version_id: UUID) -> tuple[UUID, str, int] | None:
        return self._path_version_meta.get(path_version_id)

    async def get_latest_ready_path_version_no(self, *, document_id: UUID, mode: str) -> int | None:
        return self._latest_ready_versions.get((document_id, mode))

    async def get_legend_round_count(
        self,
        *,
        user_id: UUID,
        path_version_id: UUID,
        unit_node_id: UUID,
    ) -> int:
        row = self._legend_review_progress.get((user_id, path_version_id, unit_node_id))
        return 0 if row is None else int(row.legend_round_count)

    async def is_subscription_active(self, *, user_id: UUID, at: datetime) -> bool:
        return self._subscription_active

    async def get_daily_reward_cap_usage(
        self, *, user_id: UUID, date_key: date
    ) -> FakeDailyRewardCapUsage | None:
        return self._daily_cap_usage.get((user_id, date_key))

    async def upsert_daily_reward_cap_usage(
        self,
        *,
        user_id: UUID,
        date_key: date,
        xp_delta: int,
        coin_delta: int,
    ) -> FakeDailyRewardCapUsage:
        key = (user_id, date_key)
        row = self._daily_cap_usage.get(key)
        if row is None:
            row = FakeDailyRewardCapUsage(
                xp_legend_earned=max(0, xp_delta),
                coin_legend_earned=max(0, coin_delta),
            )
            self._daily_cap_usage[key] = row
            return row

        row.xp_legend_earned += max(0, xp_delta)
        row.coin_legend_earned += max(0, coin_delta)
        return row

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
            explanation=f"Explanation {i + 1}",
            source_locator=f"Section {i + 1}",
            supporting_excerpt=f"Excerpt {i + 1}",
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


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", [RunMode.ENDLESS, RunMode.SPEED, RunMode.DRAFT])
async def test_real_run_service_returns_feedback_for_wrong_answers(mode: RunMode) -> None:
    user_id = uuid4()
    document_id = uuid4()
    questions = _build_questions(document_id)[:1]
    questions[0].correct_option_ids = [UUID(questions[0].options[0]["id"])]

    repository = InMemoryRunRepository(questions)
    service = RunService(repository=repository)
    run, generated = await service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=mode,
        question_count=1,
    )

    wrong_option_id = UUID(generated[0].options[1]["id"])
    result = await service.submit_answer(
        run_id=run.id,
        question_id=generated[0].id,
        selected_option_ids=[wrong_option_id],
    )

    assert result.is_correct is False
    assert result.feedback is not None
    assert [option.text for option in result.feedback.correct_options] == [
        generated[0].options[0]["text"]
    ]
    assert result.feedback.explanation == generated[0].explanation
    assert result.feedback.source_locator == generated[0].source_locator
    assert result.feedback.supporting_excerpt == generated[0].supporting_excerpt


@pytest.mark.asyncio
async def test_real_run_service_builds_fallback_explanation_for_wrong_answers() -> None:
    user_id = uuid4()
    document_id = uuid4()
    questions = _build_questions(document_id)[:1]
    questions[0].correct_option_ids = [UUID(questions[0].options[0]["id"])]
    questions[0].explanation = None
    questions[0].supporting_excerpt = "Python语法和动态类型，以及解释型语言的本质。"

    repository = InMemoryRunRepository(questions)
    service = RunService(repository=repository)
    run, generated = await service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=RunMode.ENDLESS,
        question_count=1,
    )

    wrong_option_id = UUID(generated[0].options[1]["id"])
    result = await service.submit_answer(
        run_id=run.id,
        question_id=generated[0].id,
        selected_option_ids=[wrong_option_id],
    )

    assert result.feedback is not None
    assert result.feedback.explanation is not None
    assert "Python语法和动态类型" in result.feedback.explanation


@pytest.mark.asyncio
async def test_real_run_service_accumulates_study_seconds_and_goal_progress() -> None:
    user_id = uuid4()
    document_id = uuid4()
    questions = _build_questions(document_id)
    for question in questions:
        question.correct_option_ids = [UUID(question.options[0]["id"])]

    repository = InMemoryRunRepository(questions)
    service = RunService(repository=repository)

    run, generated = await service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=RunMode.SPEED,
        question_count=3,
        path_id="speed-route-focus",
    )
    assert run.mode_state["study_seconds"] == 0
    assert run.mode_state["goal_current"] == 0
    assert run.mode_state["goal_total"] == 8

    await service.submit_answer(
        run_id=run.id,
        question_id=generated[0].id,
        selected_option_ids=[generated[0].correct_option_ids[0]],
        answer_time_ms=61_000,
    )
    after_first = await service.get_run(run.id)
    assert after_first.mode_state["study_seconds"] == 61
    assert after_first.mode_state["goal_current"] == 1
    assert after_first.mode_state["goal_total"] == 8

    await service.submit_answer(
        run_id=run.id,
        question_id=generated[1].id,
        selected_option_ids=[generated[1].correct_option_ids[0]],
        answer_time_ms=61_000,
    )
    after_second = await service.get_run(run.id)
    assert after_second.mode_state["study_seconds"] == 122
    assert after_second.mode_state["goal_current"] == 2
    assert after_second.mode_state["goal_total"] == 8


@pytest.mark.asyncio
async def test_real_run_service_create_run_raises_when_document_has_no_questions() -> None:
    user_id = uuid4()
    document_id = uuid4()

    repository = InMemoryRunRepository([])
    service = RunService(repository=repository)

    with pytest.raises(QuestionNotFoundError):
        await service.create_run(
            user_id=user_id,
            document_id=document_id,
            mode=RunMode.ENDLESS,
            question_count=3,
        )


@pytest.mark.asyncio
async def test_real_run_service_records_learning_path_progress_on_completion() -> None:
    user_id = uuid4()
    document_id = uuid4()
    path_version_id = uuid4()
    unit_node_id = uuid4()
    level_node_id = uuid4()

    questions = _build_questions(document_id)[:1]
    questions[0].correct_option_ids = [UUID(questions[0].options[0]["id"])]

    repository = InMemoryRunRepository(questions)
    repository._path_nodes[unit_node_id] = FakeLearningPathNode(
        id=unit_node_id,
        node_type=LearningPathNodeType.UNIT,
        parent_node_id=None,
    )
    repository._path_nodes[level_node_id] = FakeLearningPathNode(
        id=level_node_id,
        node_type=LearningPathNodeType.LEVEL,
        parent_node_id=unit_node_id,
    )
    service = RunService(repository=repository)

    run, generated = await service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=RunMode.ENDLESS,
        question_count=1,
        path_version_id=path_version_id,
        level_node_id=level_node_id,
    )

    await service.submit_answer(
        run_id=run.id,
        question_id=generated[0].id,
        selected_option_ids=[generated[0].correct_option_ids[0]],
    )

    progress_key = (user_id, path_version_id, level_node_id)
    progress = repository._learning_path_progress.get(progress_key)
    assert progress is not None
    assert progress.status == LearningPathProgressStatus.COMPLETED
    assert progress.completed_runs_count == 1
    assert progress.first_completed_run_id == run.id


@pytest.mark.asyncio
async def test_real_run_service_records_legend_review_progress() -> None:
    user_id = uuid4()
    document_id = uuid4()
    path_version_id = uuid4()
    unit_node_id = uuid4()
    level_node_id = uuid4()

    questions = _build_questions(document_id)[:1]
    questions[0].correct_option_ids = [UUID(questions[0].options[0]["id"])]

    repository = InMemoryRunRepository(questions)
    repository._path_nodes[unit_node_id] = FakeLearningPathNode(
        id=unit_node_id,
        node_type=LearningPathNodeType.UNIT,
        parent_node_id=None,
    )
    repository._path_nodes[level_node_id] = FakeLearningPathNode(
        id=level_node_id,
        node_type=LearningPathNodeType.LEVEL,
        parent_node_id=unit_node_id,
    )
    service = RunService(repository=repository)

    run, generated = await service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=RunMode.ENDLESS,
        question_count=1,
        path_version_id=path_version_id,
        level_node_id=level_node_id,
        is_legend_review=True,
    )

    await service.submit_answer(
        run_id=run.id,
        question_id=generated[0].id,
        selected_option_ids=[generated[0].correct_option_ids[0]],
    )

    legend_key = (user_id, path_version_id, unit_node_id)
    legend_progress = repository._legend_review_progress.get(legend_key)
    assert legend_progress is not None
    assert legend_progress.legend_round_count == 1


@pytest.mark.asyncio
async def test_real_run_service_applies_legend_decay_and_old_version_discount() -> None:
    user_id = uuid4()
    document_id = uuid4()
    path_version_id = uuid4()
    unit_node_id = uuid4()
    level_node_id = uuid4()

    questions = _build_questions(document_id)[:1]
    questions[0].correct_option_ids = [UUID(questions[0].options[0]["id"])]

    repository = InMemoryRunRepository(questions)
    repository._path_nodes[unit_node_id] = FakeLearningPathNode(
        id=unit_node_id,
        node_type=LearningPathNodeType.UNIT,
        parent_node_id=None,
    )
    repository._path_nodes[level_node_id] = FakeLearningPathNode(
        id=level_node_id,
        node_type=LearningPathNodeType.LEVEL,
        parent_node_id=unit_node_id,
    )
    repository._path_version_meta[path_version_id] = (document_id, "endless", 1)
    repository._latest_ready_versions[(document_id, "endless")] = 2
    repository._legend_review_progress[(user_id, path_version_id, unit_node_id)] = (
        FakeLegendReviewProgress(
            user_id=user_id,
            path_version_id=path_version_id,
            unit_node_id=unit_node_id,
            legend_round_count=1,
            last_legend_run_at=datetime.now(UTC),
        )
    )

    service = RunService(repository=repository)
    run, generated = await service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=RunMode.ENDLESS,
        question_count=1,
        path_version_id=path_version_id,
        level_node_id=level_node_id,
        is_legend_review=True,
    )

    await service.submit_answer(
        run_id=run.id,
        question_id=generated[0].id,
        selected_option_ids=[generated[0].correct_option_ids[0]],
    )

    completed = await service.get_run(run.id)
    assert float(completed.legend_reward_rate) == 0.3
    assert float(completed.version_reward_discount) == 0.7

    settlement = await service.get_settlement(run.id)
    assert settlement.xp_earned == 2
    assert settlement.coins_earned == 2


@pytest.mark.asyncio
async def test_real_run_service_applies_free_daily_cap_but_not_for_subscription() -> None:
    user_id = uuid4()
    document_id = uuid4()

    questions: list[QuestionData] = []
    for i in range(20):
        option_id = uuid4()
        questions.append(
            QuestionData(
                id=uuid4(),
                document_id=document_id,
                question_text=f"Q{i}",
                question_type="single_choice",
                options=[{"id": str(option_id), "text": "A"}],
                correct_option_ids=[option_id],
                difficulty=1,
            )
        )

    free_repo = InMemoryRunRepository(questions)
    free_day = RewardPolicy.utc8_date_key(datetime.now(UTC))
    free_repo._daily_cap_usage[(user_id, free_day)] = FakeDailyRewardCapUsage(
        xp_legend_earned=290,
        coin_legend_earned=55,
    )

    free_service = RunService(repository=free_repo)
    free_run, free_questions = await free_service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=RunMode.ENDLESS,
        question_count=20,
    )

    for question in free_questions:
        await free_service.submit_answer(
            run_id=free_run.id,
            question_id=question.id,
            selected_option_ids=[question.correct_option_ids[0]],
        )

    free_settlement = await free_service.get_settlement(free_run.id)
    assert free_settlement.xp_earned == 10
    assert free_settlement.coins_earned == 5

    subscribed_repo = InMemoryRunRepository(questions)
    subscribed_repo._subscription_active = True
    subscribed_repo._daily_cap_usage[(user_id, free_day)] = FakeDailyRewardCapUsage(
        xp_legend_earned=290,
        coin_legend_earned=55,
    )

    subscribed_service = RunService(repository=subscribed_repo)
    subscribed_run, subscribed_questions = await subscribed_service.create_run(
        user_id=user_id,
        document_id=document_id,
        mode=RunMode.ENDLESS,
        question_count=20,
    )

    for question in subscribed_questions:
        await subscribed_service.submit_answer(
            run_id=subscribed_run.id,
            question_id=question.id,
            selected_option_ids=[question.correct_option_ids[0]],
        )

    subscribed_settlement = await subscribed_service.get_settlement(subscribed_run.id)
    assert subscribed_settlement.xp_earned > free_settlement.xp_earned
    assert subscribed_settlement.coins_earned > free_settlement.coins_earned
