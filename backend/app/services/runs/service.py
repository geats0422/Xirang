from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import UTC, date, datetime
from typing import Any, Protocol, cast
from uuid import UUID

from app.db.models.runs import RunMode, RunStatus
from app.services.learning_paths.reward_policy import DailyCapUsage, RewardComputation, RewardPolicy
from app.services.runs.exceptions import (
    DuplicateAnswerError,
    InvalidRunStateError,
    QuestionNotFoundError,
    RunNotCompletedError,
    RunNotFoundError,
)
from app.services.runs.schemas import (
    AnswerFeedback,
    AnswerFeedbackOption,
    AnswerResult,
    QuestionData,
    Settlement,
    SubmitAnswerResult,
)


class RunRepositoryProtocol(Protocol):
    async def create_run(
        self,
        *,
        user_id: UUID,
        document_id: UUID,
        mode: RunMode,
        total_questions: int,
        mode_state: Mapping[str, object] | None = None,
        source_path_version_id: UUID | None = None,
        source_level_node_id: UUID | None = None,
        is_legend_review: bool = False,
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
        mode_state: Mapping[str, object] | None = None,
        ended_at: datetime | None = None,
        legend_reward_rate: float | None = None,
        version_reward_discount: float | None = None,
    ) -> None: ...

    async def list_document_questions(
        self,
        *,
        document_id: UUID,
        mode: RunMode,
        count: int,
        path_id: str | None = None,
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

    async def upsert_learning_path_progress(
        self,
        *,
        user_id: UUID,
        path_version_id: UUID,
        node_id: UUID,
        completed_run_id: UUID,
        completed_at: datetime,
    ) -> None: ...

    async def resolve_unit_node_id(self, *, node_id: UUID) -> UUID | None: ...

    async def increment_legend_review_progress(
        self,
        *,
        user_id: UUID,
        path_version_id: UUID,
        unit_node_id: UUID,
        completed_at: datetime,
    ) -> None: ...

    async def get_path_version_meta(
        self, *, path_version_id: UUID
    ) -> tuple[UUID, str, int] | None: ...

    async def get_latest_ready_path_version_no(
        self, *, document_id: UUID, mode: str
    ) -> int | None: ...

    async def get_legend_round_count(
        self,
        *,
        user_id: UUID,
        path_version_id: UUID,
        unit_node_id: UUID,
    ) -> int: ...

    async def is_subscription_active(self, *, user_id: UUID, at: datetime) -> bool: ...

    async def get_daily_reward_cap_usage(self, *, user_id: UUID, date_key: date) -> Any | None: ...

    async def upsert_daily_reward_cap_usage(
        self,
        *,
        user_id: UUID,
        date_key: date,
        xp_delta: int,
        coin_delta: int,
    ) -> Any: ...

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
        path_id: str | None = None,
        path_version_id: UUID | None = None,
        level_node_id: UUID | None = None,
        is_legend_review: bool = False,
    ) -> tuple[Any, list[QuestionData]]:
        strategy = self._resolve_path_strategy(mode=mode, path_id=path_id)
        strategy_path_id = str(strategy.get("path_id") or "")
        strategy_goal_total_raw = strategy.get("goal_total")
        strategy_time_left_raw = strategy.get("time_left_sec")
        strategy_question_count_raw = strategy.get("question_count")

        effective_question_count = (
            strategy_question_count_raw
            if isinstance(strategy_question_count_raw, int)
            else question_count
        )
        strategy_goal_total = (
            strategy_goal_total_raw if isinstance(strategy_goal_total_raw, int) else 10
        )
        strategy_time_left = (
            strategy_time_left_raw if isinstance(strategy_time_left_raw, int) else 900
        )
        questions = await self._repository.list_document_questions(
            document_id=document_id,
            mode=mode,
            count=effective_question_count,
            path_id=strategy_path_id,
        )
        if not questions:
            raise QuestionNotFoundError(f"No questions available for document {document_id}")

        run = await self._repository.create_run(
            user_id=user_id,
            document_id=document_id,
            mode=mode,
            total_questions=len(questions),
            mode_state=self._build_initial_mode_state(
                mode=mode,
                total_questions=len(questions),
                path_id=strategy_path_id,
                goal_total=strategy_goal_total,
                time_left_sec=strategy_time_left,
            ),
            source_path_version_id=path_version_id,
            source_level_node_id=level_node_id,
            is_legend_review=is_legend_review,
        )
        await self._repository.add_run_questions(run.id, questions)
        await self._repository.commit()
        return run, questions

    def list_path_options(self, *, mode: RunMode) -> list[dict[str, object]]:
        return [
            {
                "path_id": item["path_id"],
                "label": item["label"],
                "kind": item["kind"],
                "description": item["description"],
                "goal_total": item["goal_total"],
            }
            for item in self._path_options(mode)
        ]

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
        owner_user_id: UUID | None = None,
    ) -> SubmitAnswerResult:
        run = await self._repository.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")
        if owner_user_id is not None and run.user_id != owner_user_id:
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
        feedback = None if is_correct else self._build_wrong_answer_feedback(target_question)

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
        reward_meta = RewardComputation(
            xp=0,
            coins=0,
            legend_rate=1.0,
            version_discount=1.0,
            free_cap_applied=False,
        )
        run_status: RunStatus = RunStatus.RUNNING
        ended_at: datetime | None = None
        mode_state = self._normalize_mode_state(
            raw_mode_state=run.mode_state, total_questions=run.total_questions
        )
        hp = int(mode_state["hp"])
        floor = int(mode_state["floor"])
        floor_total = int(mode_state["floor_total"])
        time_left_sec = int(mode_state["time_left_sec"])
        pending_coins = int(mode_state["pending_coins"])
        study_seconds = int(mode_state["study_seconds"])
        goal_total = int(mode_state["goal_total"])
        elapsed_sec = 0
        if answer_time_ms is not None and answer_time_ms > 0:
            elapsed_sec = math.ceil(answer_time_ms / 1000)
            time_left_sec = max(0, time_left_sec - elapsed_sec)
            study_seconds = study_seconds + elapsed_sec

        goal_current = min(goal_total, study_seconds // 60)

        if is_correct:
            floor = min(floor_total, floor + 1)
            pending_coins = pending_coins + 10
        else:
            hp = max(0, hp - 1)

        mode_state["hp"] = hp
        mode_state["floor"] = floor
        mode_state["floor_total"] = floor_total
        mode_state["time_left_sec"] = time_left_sec
        mode_state["pending_coins"] = pending_coins
        mode_state["study_seconds"] = study_seconds
        mode_state["goal_current"] = goal_current
        mode_state["goal_total"] = goal_total

        if hp <= 0:
            run_status = RunStatus.ABORTED
            ended_at = datetime.now(UTC)

        if answered_count >= run.total_questions:
            run_status = RunStatus.COMPLETED
            ended_at = datetime.now(UTC)
            settlement, reward_meta = await self._build_settlement(
                run=run,
                run_id=run.id,
                user_id=run.user_id,
                mode=run.mode,
                correct_count=correct_count,
                total_count=run.total_questions,
                pending_coins=pending_coins,
                path_id=str(mode_state["path_id"]),
                goal_current=goal_current,
                goal_total=goal_total,
            )
            mode_state["pending_coins"] = 0
            await self._record_learning_path_progress(run=run, completed_at=ended_at)

        await self._repository.update_run(
            run_id,
            status=run_status,
            score=score,
            total_questions=run.total_questions,
            correct_answers=correct_count,
            combo_count=combo_count,
            mode_state=mode_state,
            ended_at=ended_at,
            legend_reward_rate=reward_meta.legend_rate
            if run_status == RunStatus.COMPLETED
            else None,
            version_reward_discount=reward_meta.version_discount
            if run_status == RunStatus.COMPLETED
            else None,
        )

        await self._repository.commit()
        refreshed_run = await self.get_run(run_id)
        return SubmitAnswerResult(
            answer=answer,
            is_correct=is_correct,
            run=refreshed_run,
            settlement=settlement,
            feedback=feedback,
        )

    @staticmethod
    def _build_wrong_answer_feedback(target_question: dict[str, Any]) -> AnswerFeedback:
        correct_ids = {str(v) for v in target_question.get("correct_option_ids", [])}
        raw_options = target_question.get("options", [])
        correct_options = [
            AnswerFeedbackOption(id=str(option.get("id", "")), text=str(option.get("text", "")))
            for option in raw_options
            if isinstance(option, dict) and str(option.get("id", "")) in correct_ids
        ]

        explanation = target_question.get("explanation")
        source_locator = target_question.get("source_locator")
        supporting_excerpt = target_question.get("supporting_excerpt")
        explanation_text = explanation if isinstance(explanation, str) else None
        source_locator_text = source_locator if isinstance(source_locator, str) else None
        supporting_excerpt_text = (
            supporting_excerpt if isinstance(supporting_excerpt, str) else None
        )
        if explanation_text is None or len(explanation_text.strip()) < 12:
            explanation_text = RunService._build_fallback_explanation(
                correct_options=correct_options,
                supporting_excerpt=supporting_excerpt_text,
            )

        return AnswerFeedback(
            correct_options=correct_options,
            explanation=explanation_text,
            source_locator=source_locator_text,
            supporting_excerpt=supporting_excerpt_text,
        )

    @staticmethod
    def _build_fallback_explanation(
        *,
        correct_options: list[AnswerFeedbackOption],
        supporting_excerpt: str | None,
    ) -> str | None:
        correct_answer_text = "/".join(option.text for option in correct_options if option.text)
        if supporting_excerpt and correct_answer_text:
            return f"The document excerpt supports the correct answer ({correct_answer_text}): {supporting_excerpt}"
        if supporting_excerpt:
            return f"The document excerpt explains the correct answer: {supporting_excerpt}"
        if correct_answer_text:
            return f"The correct answer is {correct_answer_text}."
        return None

    async def get_settlement(self, run_id: UUID) -> Settlement:
        run = await self._repository.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")
        if run.status != RunStatus.COMPLETED:
            raise RunNotCompletedError(f"Run {run_id} not completed")

        stored = await self._repository.get_settlement(run_id)
        if stored is None:
            settlement, _ = await self._build_settlement(
                run=run,
                run_id=run.id,
                user_id=run.user_id,
                mode=run.mode,
                correct_count=run.correct_answers,
                total_count=run.total_questions,
            )
            return settlement

        return Settlement(
            run_id=stored.run_id,
            xp_earned=int(stored.xp_gained),
            coins_earned=int(stored.coin_reward),
            combo_max=int(stored.combo_count),
            accuracy=float(stored.accuracy_pct),
            correct_count=run.correct_answers,
            total_count=run.total_questions,
        )

    async def _record_learning_path_progress(self, *, run: Any, completed_at: datetime) -> None:
        path_version_id = getattr(run, "source_path_version_id", None)
        level_node_id = getattr(run, "source_level_node_id", None)

        if not isinstance(path_version_id, UUID) or not isinstance(level_node_id, UUID):
            return

        await self._repository.upsert_learning_path_progress(
            user_id=run.user_id,
            path_version_id=path_version_id,
            node_id=level_node_id,
            completed_run_id=run.id,
            completed_at=completed_at,
        )

        if not bool(getattr(run, "is_legend_review", False)):
            return

        unit_node_id = await self._repository.resolve_unit_node_id(node_id=level_node_id)
        if unit_node_id is None:
            return

        await self._repository.increment_legend_review_progress(
            user_id=run.user_id,
            path_version_id=path_version_id,
            unit_node_id=unit_node_id,
            completed_at=completed_at,
        )

    async def _compute_reward(
        self,
        *,
        run: Any,
        base_xp: int,
        base_coins: int,
    ) -> RewardComputation:
        now = datetime.now(UTC)

        path_version_id = getattr(run, "source_path_version_id", None)
        level_node_id = getattr(run, "source_level_node_id", None)
        is_latest_ready_version: bool | None = None

        if isinstance(path_version_id, UUID):
            path_meta = await self._repository.get_path_version_meta(
                path_version_id=path_version_id
            )
            if path_meta is not None:
                document_id, mode_value, version_no = path_meta
                latest_ready_version_no = await self._repository.get_latest_ready_path_version_no(
                    document_id=document_id,
                    mode=mode_value,
                )
                if latest_ready_version_no is not None:
                    is_latest_ready_version = version_no >= latest_ready_version_no

        legend_round_count = 0
        if (
            bool(getattr(run, "is_legend_review", False))
            and isinstance(path_version_id, UUID)
            and isinstance(level_node_id, UUID)
        ):
            unit_node_id = await self._repository.resolve_unit_node_id(node_id=level_node_id)
            if unit_node_id is not None:
                legend_round_count = await self._repository.get_legend_round_count(
                    user_id=run.user_id,
                    path_version_id=path_version_id,
                    unit_node_id=unit_node_id,
                )

        subscription_active = await self._repository.is_subscription_active(
            user_id=run.user_id, at=now
        )
        usage = DailyCapUsage(xp_earned=0, coin_earned=0)
        usage_date_key = RewardPolicy.utc8_date_key(now)
        if not subscription_active:
            usage_row = await self._repository.get_daily_reward_cap_usage(
                user_id=run.user_id,
                date_key=usage_date_key,
            )
            if usage_row is not None:
                usage = DailyCapUsage(
                    xp_earned=int(usage_row.xp_legend_earned),
                    coin_earned=int(usage_row.coin_legend_earned),
                )

        reward = RewardPolicy.build_reward(
            base_xp=base_xp,
            base_coins=base_coins,
            is_legend_review=bool(getattr(run, "is_legend_review", False)),
            historical_legend_round_count=legend_round_count,
            is_latest_ready_version=is_latest_ready_version,
            subscription_active=subscription_active,
            daily_usage=usage,
        )

        if not subscription_active and (reward.xp > 0 or reward.coins > 0):
            await self._repository.upsert_daily_reward_cap_usage(
                user_id=run.user_id,
                date_key=usage_date_key,
                xp_delta=reward.xp,
                coin_delta=reward.coins,
            )

        return reward

    async def _build_settlement(
        self,
        *,
        run: Any,
        run_id: UUID,
        user_id: UUID,
        mode: RunMode,
        correct_count: int,
        total_count: int,
        pending_coins: int | None = None,
        path_id: str | None = None,
        goal_current: int | None = None,
        goal_total: int | None = None,
    ) -> tuple[Settlement, RewardComputation]:
        combo_max = await self._repository.get_combo_max(run_id)
        score = self._calculate_score(
            mode=mode,
            correct_count=correct_count,
            answered_count=total_count,
            combo_count=combo_max,
        )
        accuracy = (correct_count / total_count) if total_count > 0 else 0.0
        base_coins = max(0, score // 10)
        if mode == RunMode.ENDLESS and pending_coins is not None:
            base_coins = max(0, pending_coins)

        reward_meta = await self._compute_reward(
            run=run,
            base_xp=score,
            base_coins=base_coins,
        )

        await self._repository.upsert_settlement(
            run_id=run_id,
            user_id=user_id,
            xp_gained=reward_meta.xp,
            coin_reward=reward_meta.coins,
            combo_count=combo_max,
            accuracy_pct=accuracy,
            payload={
                "correct_count": correct_count,
                "total_count": total_count,
                "accuracy": accuracy,
                "path_id": path_id,
                "goal_current": goal_current,
                "goal_total": goal_total,
                "base_xp": score,
                "base_coins": base_coins,
                "legend_rate": reward_meta.legend_rate,
                "version_discount": reward_meta.version_discount,
                "free_cap_applied": reward_meta.free_cap_applied,
            },
        )

        if self._wallet_service is not None:
            if reward_meta.coins > 0:
                await self._wallet_service.credit(
                    user_id=user_id,
                    amount=reward_meta.coins,
                    asset_code="COIN",
                    reason_code="run_settlement",
                    source_type="run",
                    source_id=run_id,
                    idempotency_key=f"run:{run_id}:coins",
                )
            if reward_meta.xp > 0:
                await self._wallet_service.credit(
                    user_id=user_id,
                    amount=reward_meta.xp,
                    asset_code="XP",
                    reason_code="run_settlement",
                    source_type="run",
                    source_id=run_id,
                    idempotency_key=f"run:{run_id}:xp",
                )
        return (
            Settlement(
                run_id=run_id,
                xp_earned=reward_meta.xp,
                coins_earned=reward_meta.coins,
                combo_max=combo_max,
                accuracy=accuracy,
                correct_count=correct_count,
                total_count=total_count,
            ),
            reward_meta,
        )

    @staticmethod
    def _build_initial_mode_state(
        *,
        mode: RunMode,
        total_questions: int,
        path_id: str,
        goal_total: int,
        time_left_sec: int,
    ) -> dict[str, int | str]:
        base_state: dict[str, int | str] = {
            "hp": 3,
            "max_hp": 3,
            "floor": 1,
            "floor_total": max(1, total_questions),
            "time_left_sec": time_left_sec,
            "pending_coins": 0,
            "path_id": path_id,
            "goal_metric": "study_minutes",
            "goal_current": 0,
            "goal_total": max(1, goal_total),
            "study_seconds": 0,
        }
        if mode != RunMode.ENDLESS:
            base_state["floor"] = 1
            base_state["floor_total"] = max(1, total_questions)
        return base_state

    @staticmethod
    def _normalize_mode_state(
        *, raw_mode_state: dict[str, object] | None, total_questions: int
    ) -> dict[str, int | str]:
        state = raw_mode_state or {}

        def parse_int(key: str, default: int) -> int:
            raw = state.get(key)
            if isinstance(raw, int):
                return raw
            if isinstance(raw, float):
                return int(raw)
            if isinstance(raw, str):
                try:
                    return int(raw)
                except ValueError:
                    return default
            return default

        return {
            "hp": parse_int("hp", 3),
            "max_hp": parse_int("max_hp", 3),
            "floor": parse_int("floor", 1),
            "floor_total": parse_int("floor_total", max(1, total_questions)),
            "time_left_sec": parse_int("time_left_sec", 900),
            "pending_coins": parse_int("pending_coins", 0),
            "path_id": str(state.get("path_id") or ""),
            "goal_metric": str(state.get("goal_metric") or "study_minutes"),
            "goal_current": parse_int("goal_current", 0),
            "goal_total": parse_int("goal_total", 10),
            "study_seconds": parse_int("study_seconds", 0),
        }

    @staticmethod
    def _resolve_path_strategy(mode: RunMode, path_id: str | None) -> dict[str, object]:
        options = RunService._path_options(mode)
        for option in options:
            if option["path_id"] == path_id:
                return option
        return options[0]

    @staticmethod
    def _path_options(mode: RunMode) -> list[dict[str, object]]:
        if mode == RunMode.ENDLESS:
            return [
                {
                    "path_id": "F1",
                    "label": "F1",
                    "kind": "floor",
                    "description": "Warm-up floor",
                    "question_count": 8,
                    "time_left_sec": 900,
                    "goal_total": 10,
                },
                {
                    "path_id": "F2",
                    "label": "F2",
                    "kind": "floor",
                    "description": "Steady learning",
                    "question_count": 8,
                    "time_left_sec": 900,
                    "goal_total": 10,
                },
                {
                    "path_id": "F3",
                    "label": "F3",
                    "kind": "floor",
                    "description": "Risk check",
                    "question_count": 9,
                    "time_left_sec": 840,
                    "goal_total": 10,
                },
                {
                    "path_id": "F4",
                    "label": "F4",
                    "kind": "floor",
                    "description": "Pattern practice",
                    "question_count": 10,
                    "time_left_sec": 840,
                    "goal_total": 10,
                },
                {
                    "path_id": "F5",
                    "label": "F5",
                    "kind": "floor",
                    "description": "High pressure",
                    "question_count": 10,
                    "time_left_sec": 780,
                    "goal_total": 10,
                },
                {
                    "path_id": "F6",
                    "label": "F6",
                    "kind": "floor",
                    "description": "Abyss boss",
                    "question_count": 12,
                    "time_left_sec": 780,
                    "goal_total": 10,
                },
            ]
        if mode == RunMode.SPEED:
            return [
                {
                    "path_id": "speed-route-focus",
                    "label": "R1",
                    "kind": "checkpoint",
                    "description": "Short rounds, higher accuracy bonus",
                    "question_count": 8,
                    "time_left_sec": 90,
                    "goal_total": 8,
                },
                {
                    "path_id": "speed-route-burst",
                    "label": "R2",
                    "kind": "checkpoint",
                    "description": "Fast tempo with combo scaling",
                    "question_count": 10,
                    "time_left_sec": 60,
                    "goal_total": 8,
                },
                {
                    "path_id": "speed-route-endurance",
                    "label": "R3",
                    "kind": "checkpoint",
                    "description": "Long timer, stable output",
                    "question_count": 12,
                    "time_left_sec": 150,
                    "goal_total": 8,
                },
            ]
        return [
            {
                "path_id": "draft-route-classic",
                "label": "R1",
                "kind": "round",
                "description": "Balanced drafting journey",
                "question_count": 8,
                "time_left_sec": 600,
                "goal_total": 10,
            },
            {
                "path_id": "draft-route-theory",
                "label": "R2",
                "kind": "round",
                "description": "Focus on concept-heavy cards",
                "question_count": 10,
                "time_left_sec": 720,
                "goal_total": 10,
            },
            {
                "path_id": "draft-route-memory",
                "label": "R3",
                "kind": "round",
                "description": "Retention-oriented drafting",
                "question_count": 8,
                "time_left_sec": 540,
                "goal_total": 10,
            },
        ]

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
