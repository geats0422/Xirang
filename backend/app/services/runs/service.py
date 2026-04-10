from __future__ import annotations

import math
import re
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
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
from app.services.runs.schemas import (
    AnswerResult,
    QuestionData,
    Settlement,
    SubmitAnswerResult,
)

_TRAILING_ZH_SUFFIXES = (
    "字符",
    "操作",
    "命令",
    "标记",
    "符号",
    "符",
)

_CANONICAL_EQUIVALENT_GROUPS: tuple[set[str], ...] = (
    {
        "\\n",
        "newline",
        "linebreak",
        "linefeed",
        "换行",
        "换行符",
        "换行操作",
    },
)


def _normalize_fill_answer(text: str) -> str:
    normalized = text.strip().lower()
    normalized = normalized.replace("\u3000", " ")
    normalized = re.sub(r"\s+", "", normalized)
    strip_chars = "'\"`"
    strip_chars += "\u201c\u201d\u2018\u2019"
    strip_chars += "()[]{}:,.!?"
    strip_chars += "\u3002\u3001\uff01\uff1f\uff1b\uff1a\uff08\uff09\uff0c"
    normalized = normalized.strip(strip_chars)
    return normalized


def _strip_zh_suffixes(text: str) -> set[str]:
    variants = {text}
    for suffix in _TRAILING_ZH_SUFFIXES:
        if text.endswith(suffix) and len(text) > len(suffix):
            variants.add(text[: -len(suffix)])
    return variants


def _expand_equivalent_group(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for group in _CANONICAL_EQUIVALENT_GROUPS:
        if tokens.intersection(group):
            expanded.update(group)
    return expanded


def _build_fill_answer_variants(answer: str) -> set[str]:
    base = _normalize_fill_answer(answer)
    if not base:
        return set()
    variants = _strip_zh_suffixes(base)
    variants = _expand_equivalent_group(variants)
    return {item for item in variants if item}


def _is_fill_in_blank_correct(text_answer: str | None, correct_answer: str | None) -> bool:
    if not text_answer or not correct_answer:
        return False
    submitted_variants = _build_fill_answer_variants(text_answer)
    correct_variants = _build_fill_answer_variants(correct_answer)
    if not submitted_variants or not correct_variants:
        return False
    return bool(submitted_variants.intersection(correct_variants))


class RunRepositoryProtocol(Protocol):
    async def create_run(
        self,
        *,
        user_id: UUID,
        document_id: UUID | None,
        mode: RunMode,
        total_questions: int,
        mode_state: Mapping[str, object] | None = None,
    ) -> Any: ...

    async def get_run(self, run_id: UUID) -> Any: ...
    async def list_runs(self, user_id: UUID) -> list[Any]: ...

    async def get_completed_path_ids(
        self, user_id: UUID, document_id: UUID | None, mode: RunMode
    ) -> set[str]: ...

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
        clear_ended_at: bool = False,
    ) -> None: ...

    async def list_document_questions(
        self,
        *,
        document_id: UUID | None,
        mode: RunMode,
        count: int,
        path_id: str | None = None,
        user_id: UUID | None = None,
    ) -> list[QuestionData]: ...

    async def count_review_questions(self, *, document_id: UUID | None, user_id: UUID) -> int: ...

    async def create_mistake(
        self,
        *,
        user_id: UUID,
        question_id: UUID,
        document_id: UUID,
        run_id: UUID,
        explanation: str | None = None,
    ) -> None: ...

    async def remove_mistake(
        self,
        *,
        user_id: UUID,
        question_id: UUID,
        document_id: UUID | None = None,
    ) -> None: ...

    async def count_document_questions(self, *, document_id: UUID) -> int: ...

    async def list_document_knowledge_points(
        self,
        *,
        document_id: UUID,
        limit: int = 8,
    ) -> list[str]: ...

    async def get_user_language_code(self, user_id: UUID) -> str: ...

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
    REVIVE_COIN_COST = 10
    REVIVE_SHIELD_SECONDS = 180

    def __init__(
        self,
        *,
        repository: Any,
        wallet_service: Any | None = None,
        effect_repo: Any | None = None,
        shop_repo: Any | None = None,
    ) -> None:
        self._repository = cast("RunRepositoryProtocol", repository)
        self._wallet_service = wallet_service
        self._effect_repo = effect_repo
        self._shop_repo = shop_repo

    async def create_run(
        self,
        *,
        user_id: UUID,
        document_id: UUID | None,
        mode: RunMode,
        question_count: int,
        path_id: str | None = None,
    ) -> tuple[Any, list[QuestionData]]:
        strategy = await self._resolve_path_strategy(
            mode=mode,
            path_id=path_id,
            document_id=document_id,
            user_id=user_id,
        )
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
            user_id=user_id,
        )
        if not questions:
            if mode == RunMode.REVIEW:
                raise QuestionNotFoundError("No review questions available")
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
        )
        await self._repository.add_run_questions(run.id, questions)
        await self._repository.commit()
        return run, questions

    async def list_path_options(
        self,
        *,
        mode: RunMode,
        document_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> list[dict[str, object]]:
        question_count = 0
        knowledge_points: list[str] = []
        language_code = "en"
        if mode == RunMode.REVIEW and user_id is not None:
            question_count = await self._repository.count_review_questions(
                document_id=document_id,
                user_id=user_id,
            )
        elif document_id is not None:
            question_count = await self._repository.count_document_questions(
                document_id=document_id
            )
        if document_id is not None:
            knowledge_points = await self._repository.list_document_knowledge_points(
                document_id=document_id
            )
        if user_id is not None:
            language_code = await self._repository.get_user_language_code(user_id)

        if mode == RunMode.REVIEW and question_count == 0:
            return []

        path_items = self._generate_dynamic_path_options(
            mode,
            question_count,
            knowledge_points,
            language_code,
        )

        completed_path_ids: set[str] = set()
        if user_id is not None:
            completed_path_ids = await self._repository.get_completed_path_ids(
                user_id, document_id, mode
            )

        result: list[dict[str, object]] = []
        for idx, item in enumerate(path_items):
            path_id = item["path_id"]
            if path_id in completed_path_ids:
                status = "completed"
            elif idx == 0 or path_items[idx - 1]["path_id"] in completed_path_ids:
                status = "unlocked"
            else:
                all_prev_completed = all(
                    path_items[j]["path_id"] in completed_path_ids for j in range(idx)
                )
                status = "unlocked" if all_prev_completed else "locked"
            result.append(
                {
                    "path_id": path_id,
                    "label": item["label"],
                    "kind": item["kind"],
                    "description": item["description"],
                    "goal_total": item["goal_total"],
                    "status": status,
                }
            )
        return result

    async def get_run(self, run_id: UUID, owner_user_id: UUID | None = None) -> Any:
        run = await self._repository.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")
        if owner_user_id is not None and run.user_id != owner_user_id:
            raise RunNotFoundError(f"Run {run_id} not found")
        return run

    async def list_runs(self, user_id: UUID) -> list[Any]:
        return await self._repository.list_runs(user_id)

    async def get_question_info(self, run_id: UUID, question_id: UUID) -> dict[str, Any] | None:
        """Get question details including correct answer and explanation for feedback."""
        run_questions = await self._repository.get_run_questions(run_id)
        for q in run_questions:
            if q["question_id"] == question_id:
                return q
        return None

    async def submit_answer(
        self,
        *,
        run_id: UUID,
        question_id: UUID,
        selected_option_ids: list[UUID],
        answer_time_ms: int | None = None,
        owner_user_id: UUID | None = None,
        text_answer: str | None = None,  # For FILL_IN_BLANK questions
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

        # Handle FILL_IN_BLANK questions (text comparison) vs option-based questions
        question_type = target_question.get("question_type", "single_choice")
        is_correct = False

        if question_type == "fill_in_blank":
            correct_answer = target_question.get("correct_answer")
            is_correct = _is_fill_in_blank_correct(
                text_answer=text_answer,
                correct_answer=str(correct_answer) if correct_answer is not None else None,
            )
        else:
            # For choice-based questions, compare option IDs
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

        if run.mode == RunMode.REVIEW:
            goal_current = min(goal_total, answered_count)
        else:
            goal_current = min(goal_total, study_seconds // 60)

        # Mode-specific answer handling
        current_combo = int(mode_state.get("combo_count", 0))
        revive_shield_count = int(mode_state.get("revive_shield_count", 0))
        revive_shield_expires_at = str(mode_state.get("revive_shield_expires_at") or "")
        shield_active = False
        if revive_shield_count > 0 and revive_shield_expires_at:
            try:
                shield_active = datetime.fromisoformat(revive_shield_expires_at) > datetime.now(UTC)
            except ValueError:
                shield_active = False
        if not shield_active:
            revive_shield_count = 0
            revive_shield_expires_at = ""

        if is_correct:
            if run.mode == RunMode.ENDLESS:
                floor = min(floor_total, floor + 1)
                pending_coins = pending_coins + 10
            elif run.mode == RunMode.SPEED:
                current_combo = current_combo + 1
            elif run.mode == RunMode.REVIEW:
                floor = min(floor_total, answered_count + 1)
                await self._repository.remove_mistake(
                    user_id=run.user_id,
                    question_id=question_id,
                    document_id=run.document_id,
                )
        else:
            if run.mode == RunMode.ENDLESS:
                if shield_active and revive_shield_count > 0:
                    revive_shield_count = 0
                    revive_shield_expires_at = ""
                else:
                    hp = max(0, hp - 1)
            elif run.mode == RunMode.SPEED:
                current_combo = 0

            if run.document_id is not None:
                await self._repository.create_mistake(
                    user_id=run.user_id,
                    question_id=question_id,
                    document_id=run.document_id,
                    run_id=run.id,
                    explanation=target_question.get("explanation"),
                )

        mode_state["hp"] = hp
        mode_state["floor"] = floor
        mode_state["floor_total"] = floor_total
        mode_state["time_left_sec"] = time_left_sec
        mode_state["pending_coins"] = pending_coins
        mode_state["study_seconds"] = study_seconds
        mode_state["goal_current"] = goal_current
        mode_state["goal_total"] = goal_total
        mode_state["combo_count"] = current_combo
        mode_state["revive_shield_count"] = revive_shield_count
        mode_state["revive_shield_expires_at"] = revive_shield_expires_at

        if run.mode == RunMode.ENDLESS and hp <= 0:
            run_status = RunStatus.ABORTED
            ended_at = datetime.now(UTC)

        if answered_count >= run.total_questions:
            run_status = RunStatus.COMPLETED
            ended_at = datetime.now(UTC)
            settlement = await self._build_settlement(
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

        await self._repository.update_run(
            run_id,
            status=run_status,
            score=score,
            total_questions=run.total_questions,
            correct_answers=correct_count,
            combo_count=combo_count,
            mode_state=mode_state,
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

    async def use_revive(
        self, *, run_id: UUID, owner_user_id: UUID | None = None
    ) -> tuple[Any, int, int]:
        run = await self._repository.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")
        if owner_user_id is not None and run.user_id != owner_user_id:
            raise RunNotFoundError(f"Run {run_id} not found")
        if run.mode != RunMode.ENDLESS:
            raise InvalidRunStateError("revive_only_supported_for_endless")

        mode_state = self._normalize_mode_state(
            raw_mode_state=run.mode_state,
            total_questions=run.total_questions,
        )
        hp = int(mode_state["hp"])
        max_hp = int(mode_state["max_hp"])
        if hp > 0 and run.status == RunStatus.RUNNING:
            raise InvalidRunStateError("revive_not_needed")
        if run.status not in (RunStatus.ABORTED, RunStatus.RUNNING):
            raise InvalidRunStateError("run_not_revivable")

        use_revival_from_inventory = False
        coin_cost = 0

        if self._shop_repo is not None:
            inventory = await self._shop_repo.get_inventory(run.user_id)
            inv_item = next((i for i in inventory if i.item_code == "revival"), None)
            use_revival_from_inventory = inv_item is not None and inv_item.quantity > 0

        if use_revival_from_inventory and self._shop_repo is not None:
            await self._shop_repo.upsert_inventory(run.user_id, "revival", -1)
            coin_cost = 0
        elif self._wallet_service is not None:
            coin_cost = self.REVIVE_COIN_COST
            await self._wallet_service.debit(
                user_id=run.user_id,
                amount=self.REVIVE_COIN_COST,
                asset_code="COIN",
                reason_code="run_revive_purchase",
                source_type="run",
                source_id=run.id,
                idempotency_key=f"run:{run.id}:revive:{await self._repository.count_answers(run.id)}",
            )

        mode_state["hp"] = min(max_hp, hp + 1)
        mode_state["revive_shield_count"] = 1
        mode_state["revive_shield_expires_at"] = (
            datetime.now(UTC) + timedelta(seconds=self.REVIVE_SHIELD_SECONDS)
        ).isoformat()

        await self._repository.update_run(
            run_id,
            status=RunStatus.RUNNING,
            mode_state=mode_state,
            clear_ended_at=True,
        )
        await self._repository.commit()
        refreshed_run = await self.get_run(run_id)
        balance = 0
        if self._wallet_service is not None:
            bal = await self._wallet_service.get_balance(run.user_id, asset_code="COIN")
            balance = bal.balance
        return refreshed_run, balance, coin_cost

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
        pending_coins: int | None = None,
        path_id: str | None = None,
        goal_current: int | None = None,
        goal_total: int | None = None,
    ) -> Settlement:
        combo_max = await self._repository.get_combo_max(run_id)
        score = self._calculate_score(
            mode=mode,
            correct_count=correct_count,
            answered_count=total_count,
            combo_count=combo_max,
        )
        xp_gained = await self._calculate_settlement_xp(user_id, score)
        accuracy = (correct_count / total_count) if total_count > 0 else 0.0
        coins = max(0, score // 10)
        if mode == RunMode.ENDLESS and pending_coins is not None:
            coins = max(0, pending_coins)

        await self._repository.upsert_settlement(
            run_id=run_id,
            user_id=user_id,
            xp_gained=xp_gained,
            coin_reward=coins,
            combo_count=combo_max,
            accuracy_pct=accuracy,
            payload={
                "correct_count": correct_count,
                "total_count": total_count,
                "accuracy": accuracy,
                "path_id": path_id,
                "goal_current": goal_current,
                "goal_total": goal_total,
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
                amount=xp_gained,
                asset_code="XP",
                reason_code="run_settlement",
                source_type="run",
                source_id=run_id,
                idempotency_key=f"run:{run_id}:xp",
            )
        return Settlement(
            run_id=run_id,
            xp_earned=xp_gained,
            coins_earned=coins,
            combo_max=combo_max,
            accuracy=accuracy,
            correct_count=correct_count,
            total_count=total_count,
        )

    async def _calculate_settlement_xp(self, user_id: UUID, base_xp: int) -> int:
        if self._effect_repo is None:
            return base_xp
        now = datetime.now(tz=UTC)
        active = await self._effect_repo.list_active_effects(user_id)
        xp_boosts = [
            e
            for e in active
            if e.effect_type == "xp_boost" and (e.expires_at is None or e.expires_at > now)
        ]
        if xp_boosts:
            max_mult = max((float(e.multiplier or 1.0) for e in xp_boosts), default=1.0)
            return int(base_xp * max_mult)
        return base_xp

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
            "goal_metric": "questions_answered" if mode == RunMode.REVIEW else "study_minutes",
            "goal_current": 0,
            "goal_total": max(1, goal_total),
            "study_seconds": 0,
            "revive_shield_count": 0,
            "revive_shield_expires_at": "",
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
            "revive_shield_count": parse_int("revive_shield_count", 0),
            "revive_shield_expires_at": str(state.get("revive_shield_expires_at") or ""),
        }

    @staticmethod
    def _resolve_language_family(language_code: str | None) -> str:
        normalized = (language_code or "en").strip().lower()
        if normalized.startswith("zh"):
            return "zh"
        if normalized.startswith("en"):
            return "en"
        return "en"

    @staticmethod
    def _generate_dynamic_path_options(
        mode: RunMode,
        question_count: int,
        knowledge_points: list[str] | None = None,
        language_code: str = "en",
    ) -> list[dict[str, object]]:
        """Generate path options dynamically based on question count.

        Each unit/path contains 10-12 questions. The number of paths is determined
        by the total question count.
        """
        import math

        language_family = RunService._resolve_language_family(language_code)
        use_zh = language_family == "zh"

        if question_count <= 0:
            if mode == RunMode.REVIEW:
                return []
            # Fallback to defaults if no questions available
            return RunService._path_options(mode, language_code)

        # Calculate number of units based on question count
        # Each unit has 10-12 questions, target 10-11 average
        if question_count <= 12:
            num_units = 1
        else:
            num_units = math.ceil(question_count / 11)
            num_units = max(1, min(num_units, 8))  # Cap between 1 and 8 units

        topics = [str(item).strip() for item in (knowledge_points or []) if str(item).strip()]
        if topics:
            num_units = max(num_units, min(len(topics), 8))

        def topic_for(index: int) -> str | None:
            if not topics:
                return None
            return topics[index % len(topics)]

        def describe(base_description: str, index: int) -> str:
            topic = topic_for(index)
            if topic is None:
                return base_description
            if use_zh:
                return f"{topic}章节: {base_description}"
            return f"{topic}: {base_description}"

        def draft_describe(base_description: str, index: int) -> str:
            topic = topic_for(index)
            if topic is None:
                return base_description
            if use_zh:
                if index == 0:
                    route_title = "基础章节线"
                elif index == 1:
                    route_title = "进阶深化线"
                else:
                    route_title = "巩固强化线"
            elif index == 0:
                route_title = "Foundation Route"
            elif index == 1:
                route_title = "Deep-dive Route"
            else:
                route_title = "Consolidation Route"
            return f"{route_title} · {topic}"

        questions_per_unit = max(10, min(12, math.ceil(question_count / num_units)))

        if mode == RunMode.ENDLESS:
            path_items = []
            for i in range(num_units):
                floor_num = i + 1
                path_id = f"F{floor_num}"
                label = f"F{floor_num}"

                # Vary difficulty and time based on floor
                if floor_num == 1:
                    description = "热身关, 先把节奏找回来" if use_zh else "Warm-up floor"
                    time_sec = 900
                elif floor_num == num_units:
                    description = (
                        ("深渊终章, 拿下收官战" if num_units > 2 else "终章冲刺, 完成最后挑战")
                        if use_zh
                        else ("Abyss boss" if num_units > 2 else "Final challenge")
                    )
                    time_sec = 780
                else:
                    mid = num_units // 2
                    if floor_num <= mid:
                        description = (
                            ("稳扎稳打, 夯实基础" if floor_num == 2 else "题型磨合, 形成手感")
                            if use_zh
                            else ("Steady learning" if floor_num == 2 else "Pattern practice")
                        )
                        time_sec = 840
                    else:
                        description = "高压冲刺, 保持准确率" if use_zh else "High pressure"
                        time_sec = 800

                path_items.append(
                    {
                        "path_id": path_id,
                        "label": label,
                        "kind": "floor",
                        "description": describe(description, i),
                        "question_count": questions_per_unit,
                        "time_left_sec": time_sec,
                        "goal_total": questions_per_unit,
                    }
                )
            return path_items

        if mode == RunMode.SPEED:
            # Speed mode: fewer questions per path, shorter times
            if num_units == 1:
                focus_desc = (
                    "短局快练, 命中率越高收益越好"
                    if use_zh
                    else "Short rounds, higher accuracy bonus"
                )
                return [
                    {
                        "path_id": "speed-route-focus",
                        "label": "R1",
                        "kind": "checkpoint",
                        "description": describe(focus_desc, 0),
                        "question_count": min(questions_per_unit, 10),
                        "time_left_sec": 90,
                        "goal_total": 8,
                    }
                ]
            routes = []
            route_configs = [
                (
                    "speed-route-focus",
                    "R1",
                    "短局快练, 命中率越高收益越好"
                    if use_zh
                    else "Short rounds, higher accuracy bonus",
                    90,
                    8,
                ),
                (
                    "speed-route-burst",
                    "R2",
                    "极速连击线, 连对越多加成越高" if use_zh else "Fast tempo with combo scaling",
                    60,
                    8,
                ),
                (
                    "speed-route-endurance",
                    "R3",
                    "耐力节奏线, 更长计时更稳推进" if use_zh else "Long timer, stable output",
                    150,
                    10,
                ),
            ]
            for _i, (path_id, label, desc, time_sec, goal) in enumerate(
                route_configs[: min(num_units, 3)]
            ):
                routes.append(
                    {
                        "path_id": path_id,
                        "label": label,
                        "kind": "checkpoint",
                        "description": describe(desc, _i),
                        "question_count": min(questions_per_unit, 10),
                        "time_left_sec": time_sec,
                        "goal_total": goal,
                    }
                )
            return routes

        if mode == RunMode.REVIEW:
            review_units = max(1, min(math.ceil(question_count / 20), 8))
            return [
                {
                    "path_id": f"review-stage-{index + 1}",
                    "label": f"S{index + 1}",
                    "kind": "review",
                    "description": (
                        f"错题回顾 · 第{index + 1}关"
                        if use_zh
                        else f"Mistake review · Stage {index + 1}"
                    ),
                    "question_count": 20,
                    "time_left_sec": 1200,
                    "goal_total": 20,
                }
                for index in range(review_units)
            ]

        # DRAFT mode
        if num_units == 1:
            classic_desc = "均衡组卡线, 覆盖核心考点" if use_zh else "Balanced drafting journey"
            return [
                {
                    "path_id": "draft-route-classic",
                    "label": "R1",
                    "kind": "round",
                    "description": draft_describe(classic_desc, 0),
                    "question_count": questions_per_unit,
                    "time_left_sec": 600,
                    "goal_total": 10,
                }
            ]
        return [
            {
                "path_id": "draft-route-classic",
                "label": "R1",
                "kind": "round",
                "description": draft_describe(
                    "均衡组卡线, 覆盖核心考点" if use_zh else "Balanced drafting journey",
                    0,
                ),
                "question_count": questions_per_unit,
                "time_left_sec": 600,
                "goal_total": 10,
            },
            {
                "path_id": "draft-route-theory",
                "label": "R2",
                "kind": "round",
                "description": draft_describe(
                    "概念强化线, 聚焦高权重知识点" if use_zh else "Focus on concept-heavy cards",
                    1,
                ),
                "question_count": questions_per_unit,
                "time_left_sec": 720,
                "goal_total": 10,
            },
            {
                "path_id": "draft-route-memory",
                "label": "R3",
                "kind": "round",
                "description": draft_describe(
                    "记忆回收线, 强化长期留存" if use_zh else "Retention-oriented drafting",
                    2,
                ),
                "question_count": questions_per_unit,
                "time_left_sec": 540,
                "goal_total": 10,
            },
        ]

    # @staticmethod removed - needs async and repository access
    async def _resolve_path_strategy(
        self,
        *,
        mode: RunMode,
        path_id: str | None,
        document_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> dict[str, object]:
        # Get question count for dynamic path generation
        question_count = 0
        knowledge_points: list[str] = []
        if mode == RunMode.REVIEW and user_id is not None:
            question_count = await self._repository.count_review_questions(
                document_id=document_id,
                user_id=user_id,
            )
        elif document_id is not None:
            question_count = await self._repository.count_document_questions(
                document_id=document_id
            )
        if document_id is not None:
            knowledge_points = await self._repository.list_document_knowledge_points(
                document_id=document_id
            )

        language_code = "en"
        if user_id is not None:
            language_code = await self._repository.get_user_language_code(user_id)

        # Generate dynamic options
        options = self._generate_dynamic_path_options(
            mode,
            question_count,
            knowledge_points,
            language_code,
        )

        if mode == RunMode.REVIEW and path_id and options:
            prefix = "review-stage-"
            if path_id.startswith(prefix):
                try:
                    requested_stage = int(path_id[len(prefix) :])
                except ValueError:
                    requested_stage = 1
                requested_stage = max(1, min(requested_stage, len(options)))
                clamped_path_id = f"{prefix}{requested_stage}"
                for option in options:
                    if option["path_id"] == clamped_path_id:
                        return option

        for option in options:
            if option["path_id"] == path_id:
                return option
        return options[0] if options else self._path_options(mode)[0]

    @staticmethod
    def _path_options(mode: RunMode, language_code: str = "en") -> list[dict[str, object]]:
        use_zh = RunService._resolve_language_family(language_code) == "zh"

        if mode == RunMode.REVIEW:
            return [
                {
                    "path_id": "review-stage-1",
                    "label": "S1",
                    "kind": "review",
                    "description": "错题回顾 · 第1关" if use_zh else "Mistake review · Stage 1",
                    "question_count": 20,
                    "time_left_sec": 1200,
                    "goal_total": 20,
                }
            ]
        if mode == RunMode.ENDLESS:
            return [
                {
                    "path_id": "F1",
                    "label": "F1",
                    "kind": "floor",
                    "description": "热身关, 先把节奏找回来" if use_zh else "Warm-up floor",
                    "question_count": 8,
                    "time_left_sec": 900,
                    "goal_total": 10,
                },
                {
                    "path_id": "F2",
                    "label": "F2",
                    "kind": "floor",
                    "description": "稳扎稳打, 夯实基础" if use_zh else "Steady learning",
                    "question_count": 8,
                    "time_left_sec": 900,
                    "goal_total": 10,
                },
                {
                    "path_id": "F3",
                    "label": "F3",
                    "kind": "floor",
                    "description": "风险试探, 别丢关键分" if use_zh else "Risk check",
                    "question_count": 9,
                    "time_left_sec": 840,
                    "goal_total": 10,
                },
                {
                    "path_id": "F4",
                    "label": "F4",
                    "kind": "floor",
                    "description": "题型磨合, 形成手感" if use_zh else "Pattern practice",
                    "question_count": 10,
                    "time_left_sec": 840,
                    "goal_total": 10,
                },
                {
                    "path_id": "F5",
                    "label": "F5",
                    "kind": "floor",
                    "description": "高压冲刺, 保持准确率" if use_zh else "High pressure",
                    "question_count": 10,
                    "time_left_sec": 780,
                    "goal_total": 10,
                },
                {
                    "path_id": "F6",
                    "label": "F6",
                    "kind": "floor",
                    "description": "深渊终章, 拿下收官战" if use_zh else "Abyss boss",
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
                    "description": "短局快练, 命中率越高收益越好"
                    if use_zh
                    else "Short rounds, higher accuracy bonus",
                    "question_count": 8,
                    "time_left_sec": 90,
                    "goal_total": 8,
                },
                {
                    "path_id": "speed-route-burst",
                    "label": "R2",
                    "kind": "checkpoint",
                    "description": "极速连击线, 连对越多加成越高"
                    if use_zh
                    else "Fast tempo with combo scaling",
                    "question_count": 10,
                    "time_left_sec": 60,
                    "goal_total": 8,
                },
                {
                    "path_id": "speed-route-endurance",
                    "label": "R3",
                    "kind": "checkpoint",
                    "description": "耐力节奏线, 更长计时更稳推进"
                    if use_zh
                    else "Long timer, stable output",
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
                "description": "均衡组卡线, 覆盖核心考点"
                if use_zh
                else "Balanced drafting journey",
                "question_count": 8,
                "time_left_sec": 600,
                "goal_total": 10,
            },
            {
                "path_id": "draft-route-theory",
                "label": "R2",
                "kind": "round",
                "description": "概念强化线, 聚焦高权重知识点"
                if use_zh
                else "Focus on concept-heavy cards",
                "question_count": 10,
                "time_left_sec": 720,
                "goal_total": 10,
            },
            {
                "path_id": "draft-route-memory",
                "label": "R3",
                "kind": "round",
                "description": "记忆回收线, 强化长期留存"
                if use_zh
                else "Retention-oriented drafting",
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
