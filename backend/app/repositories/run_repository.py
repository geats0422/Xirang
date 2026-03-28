from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Select, func, select

from app.db.models.economy import DailyRewardCapUsage
from app.db.models.learning_paths import (
    LearningPathNode,
    LearningPathNodeType,
    LearningPathProgress,
    LearningPathProgressStatus,
    LearningPathStatus,
    LearningPathVersion,
    LegendReviewProgress,
)
from app.db.models.questions import Question, QuestionOption
from app.db.models.runs import Run, RunAnswer, RunMode, RunQuestion, RunStatus, Settlement
from app.db.models.subscriptions import Subscription, SubscriptionStatus
from app.services.runs.schemas import AnswerResult, QuestionData

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
    ) -> Run:
        run = Run(
            user_id=user_id,
            document_id=document_id,
            mode=mode,
            status=RunStatus.RUNNING,
            score=0,
            total_questions=total_questions,
            correct_answers=0,
            combo_count=0,
            mode_state=mode_state or {},
            source_path_version_id=source_path_version_id,
            source_level_node_id=source_level_node_id,
            is_legend_review=is_legend_review,
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_run(self, run_id: UUID) -> Run | None:
        stmt = select(Run).where(Run.id == run_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_runs(self, user_id: UUID) -> list[Run]:
        stmt = select(Run).where(Run.user_id == user_id).order_by(Run.started_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

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
        run = await self.get_run(run_id)
        if run is None:
            return

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

        await self._session.flush()

    async def list_document_questions(
        self,
        *,
        document_id: UUID,
        mode: RunMode,
        count: int,
        path_id: str | None = None,
    ) -> list[QuestionData]:
        stmt: Select[tuple[Question]] = select(Question).where(Question.document_id == document_id)
        if mode == RunMode.ENDLESS and path_id:
            target_difficulty = self._target_endless_difficulty(path_id)
            stmt = stmt.order_by(
                func.abs(Question.difficulty - target_difficulty).asc(), Question.created_at.asc()
            )
        elif mode == RunMode.SPEED and path_id == "speed-route-burst":
            stmt = stmt.order_by(Question.difficulty.desc(), Question.created_at.asc())
        elif mode == RunMode.SPEED and path_id == "speed-route-endurance":
            stmt = stmt.order_by(Question.created_at.asc(), Question.difficulty.asc())
        elif mode == RunMode.SPEED:
            stmt = stmt.order_by(Question.difficulty.asc(), Question.created_at.asc())
        elif mode == RunMode.DRAFT and path_id == "draft-route-theory":
            stmt = stmt.order_by(Question.difficulty.desc(), Question.created_at.asc())
        elif mode == RunMode.DRAFT and path_id == "draft-route-memory":
            stmt = stmt.order_by(func.length(Question.prompt).asc(), Question.created_at.asc())
        else:
            stmt = stmt.order_by(Question.created_at.asc())

        fetch_limit = max(count, 1)
        if mode == RunMode.DRAFT:
            fetch_limit = max(count * 3, count)
        stmt = stmt.limit(fetch_limit)

        result = await self._session.execute(stmt)
        question_rows = list(result.scalars().all())

        if mode == RunMode.DRAFT:
            hard = [q for q in question_rows if q.difficulty >= 3]
            soft = [q for q in question_rows if q.difficulty < 3]
            ordered = hard + soft
            question_rows = ordered[:count]
        else:
            question_rows = question_rows[:count]

        question_ids = [q.id for q in question_rows]
        option_map = await self._load_option_map(question_ids)

        questions: list[QuestionData] = []
        for question in question_rows:
            options = option_map.get(question.id, [])
            source_locator = self._extract_source_locator(question.source_locator)
            supporting_excerpt = self._extract_supporting_excerpt(question.question_metadata)
            questions.append(
                QuestionData(
                    id=question.id,
                    document_id=question.document_id,
                    question_text=question.prompt,
                    question_type=question.question_type.value,
                    options=[{"id": str(option.id), "text": option.content} for option in options],
                    correct_option_ids=[option.id for option in options if option.is_correct],
                    difficulty=question.difficulty,
                    chapter_reference=None,
                    source_locator=source_locator,
                    supporting_excerpt=supporting_excerpt,
                )
            )

        return questions

    @staticmethod
    def _target_endless_difficulty(path_id: str) -> int:
        if path_id.startswith("F") and len(path_id) >= 2:
            try:
                floor_index = int(path_id[1:])
            except ValueError:
                return 1
            return max(1, min(5, floor_index))
        return 1

    async def add_run_questions(self, run_id: UUID, questions: list[QuestionData]) -> None:
        for sequence_no, question in enumerate(questions, start=1):
            snapshot = {
                "question_text": question.question_text,
                "question_type": question.question_type,
                "options": question.options,
                "correct_option_ids": [str(v) for v in question.correct_option_ids],
                "difficulty": question.difficulty,
                "chapter_reference": question.chapter_reference,
                "source_locator": question.source_locator,
                "supporting_excerpt": question.supporting_excerpt,
            }
            run_question = RunQuestion(
                run_id=run_id,
                question_id=question.id,
                sequence_no=sequence_no,
                selection_reason="mode_selection",
                prompt_snapshot=snapshot,
            )
            self._session.add(run_question)
        await self._session.flush()

    async def get_run_questions(self, run_id: UUID) -> list[dict[str, Any]]:
        stmt = (
            select(RunQuestion)
            .where(RunQuestion.run_id == run_id)
            .order_by(RunQuestion.sequence_no.asc())
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())

        payload: list[dict[str, Any]] = []
        for row in rows:
            snapshot = row.prompt_snapshot or {}
            raw_difficulty = snapshot.get("difficulty", 1)
            difficulty = 1
            if isinstance(raw_difficulty, int):
                difficulty = raw_difficulty
            elif isinstance(raw_difficulty, float):
                difficulty = int(raw_difficulty)
            elif isinstance(raw_difficulty, str):
                try:
                    difficulty = int(raw_difficulty)
                except ValueError:
                    difficulty = 1
            payload.append(
                {
                    "run_question_id": row.id,
                    "question_id": row.question_id,
                    "question_text": snapshot.get("question_text", ""),
                    "question_type": snapshot.get("question_type", "single_choice"),
                    "options": snapshot.get("options", []),
                    "correct_option_ids": snapshot.get("correct_option_ids", []),
                    "difficulty": difficulty,
                    "source_locator": snapshot.get("source_locator"),
                    "supporting_excerpt": snapshot.get("supporting_excerpt"),
                }
            )
        return payload

    @staticmethod
    def _extract_source_locator(source_locator: dict[str, object] | None) -> str | None:
        if not isinstance(source_locator, dict):
            return None
        raw_value = source_locator.get("source")
        return raw_value.strip() if isinstance(raw_value, str) and raw_value.strip() else None

    @staticmethod
    def _extract_supporting_excerpt(metadata: dict[str, object] | None) -> str | None:
        if not isinstance(metadata, dict):
            return None
        raw_value = metadata.get("supporting_excerpt")
        return raw_value.strip() if isinstance(raw_value, str) and raw_value.strip() else None

    async def has_question_answer(self, run_id: UUID, question_id: UUID) -> bool:
        stmt = (
            select(func.count())
            .select_from(RunAnswer)
            .join(RunQuestion, RunAnswer.run_question_id == RunQuestion.id)
            .where(RunAnswer.run_id == run_id, RunQuestion.question_id == question_id)
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one()) > 0

    async def record_answer(
        self,
        run_id: UUID,
        question_id: UUID,
        selected_option_ids: list[str],
        is_correct: bool,
        answer_time_ms: int | None,
    ) -> AnswerResult:
        run_question_stmt = (
            select(RunQuestion)
            .where(RunQuestion.run_id == run_id, RunQuestion.question_id == question_id)
            .limit(1)
        )
        run_question_result = await self._session.execute(run_question_stmt)
        run_question = run_question_result.scalar_one_or_none()
        if run_question is None:
            raise ValueError(f"Question {question_id} not found in run {run_id}")

        answer = RunAnswer(
            run_id=run_id,
            run_question_id=run_question.id,
            question_id=question_id,
            selected_option_ids=selected_option_ids,
            is_correct=is_correct,
            answer_time_ms=answer_time_ms,
        )
        self._session.add(answer)
        await self._session.flush()

        return AnswerResult(
            id=answer.id,
            run_id=answer.run_id,
            question_id=answer.question_id,
            selected_option_ids=[UUID(v) for v in answer.selected_option_ids],
            is_correct=bool(answer.is_correct),
            time_spent_ms=answer.answer_time_ms,
            created_at=answer.answered_at,
        )

    async def count_answers(self, run_id: UUID) -> int:
        stmt = select(func.count()).select_from(RunAnswer).where(RunAnswer.run_id == run_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def count_correct_answers(self, run_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(RunAnswer)
            .where(RunAnswer.run_id == run_id, RunAnswer.is_correct.is_(True))
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_combo_count(self, run_id: UUID) -> int:
        stmt = (
            select(RunAnswer.is_correct)
            .where(RunAnswer.run_id == run_id)
            .order_by(RunAnswer.answered_at.asc())
        )
        result = await self._session.execute(stmt)
        flags = [bool(v) for v in result.scalars().all()]
        combo = 0
        for flag in reversed(flags):
            if not flag:
                break
            combo += 1
        return combo

    async def get_combo_max(self, run_id: UUID) -> int:
        stmt = (
            select(RunAnswer.is_correct)
            .where(RunAnswer.run_id == run_id)
            .order_by(RunAnswer.answered_at.asc())
        )
        result = await self._session.execute(stmt)
        flags = [bool(v) for v in result.scalars().all()]
        best = 0
        current = 0
        for flag in flags:
            if flag:
                current += 1
                if current > best:
                    best = current
            else:
                current = 0
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
    ) -> Settlement:
        stmt = select(Settlement).where(Settlement.run_id == run_id).limit(1)
        result = await self._session.execute(stmt)
        settlement = result.scalar_one_or_none()
        if settlement is None:
            settlement = Settlement(
                run_id=run_id,
                user_id=user_id,
                xp_gained=xp_gained,
                coin_reward=coin_reward,
                combo_count=combo_count,
                accuracy_pct=accuracy_pct,
                payload=payload,
            )
            self._session.add(settlement)
        else:
            settlement.xp_gained = xp_gained
            settlement.coin_reward = coin_reward
            settlement.combo_count = combo_count
            settlement.accuracy_pct = accuracy_pct
            settlement.payload = payload
        await self._session.flush()
        return settlement

    async def get_settlement(self, run_id: UUID) -> Settlement | None:
        stmt = select(Settlement).where(Settlement.run_id == run_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_path_version_meta(self, *, path_version_id: UUID) -> tuple[UUID, str, int] | None:
        stmt = select(LearningPathVersion).where(LearningPathVersion.id == path_version_id).limit(1)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return row.document_id, row.mode, int(row.version_no)

    async def get_latest_ready_path_version_no(self, *, document_id: UUID, mode: str) -> int | None:
        stmt = select(func.max(LearningPathVersion.version_no)).where(
            LearningPathVersion.document_id == document_id,
            LearningPathVersion.mode == mode,
            LearningPathVersion.status == LearningPathStatus.READY,
        )
        result = await self._session.execute(stmt)
        value = result.scalar_one_or_none()
        if value is None:
            return None
        return int(value)

    async def get_legend_round_count(
        self,
        *,
        user_id: UUID,
        path_version_id: UUID,
        unit_node_id: UUID,
    ) -> int:
        stmt = (
            select(LegendReviewProgress.legend_round_count)
            .where(
                LegendReviewProgress.user_id == user_id,
                LegendReviewProgress.path_version_id == path_version_id,
                LegendReviewProgress.unit_node_id == unit_node_id,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        value = result.scalar_one_or_none()
        return int(value or 0)

    async def is_subscription_active(self, *, user_id: UUID, at: datetime) -> bool:
        stmt = (
            select(Subscription.id)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.current_period_start <= at,
                Subscription.current_period_end >= at,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_daily_reward_cap_usage(
        self, *, user_id: UUID, date_key: date
    ) -> DailyRewardCapUsage | None:
        stmt = (
            select(DailyRewardCapUsage)
            .where(
                DailyRewardCapUsage.user_id == user_id,
                DailyRewardCapUsage.date_key == date_key,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_daily_reward_cap_usage(
        self,
        *,
        user_id: UUID,
        date_key: date,
        xp_delta: int,
        coin_delta: int,
    ) -> DailyRewardCapUsage:
        row = await self.get_daily_reward_cap_usage(user_id=user_id, date_key=date_key)
        if row is None:
            row = DailyRewardCapUsage(
                user_id=user_id,
                date_key=date_key,
                xp_legend_earned=max(0, xp_delta),
                coin_legend_earned=max(0, coin_delta),
            )
            self._session.add(row)
            await self._session.flush()
            return row

        row.xp_legend_earned = int(row.xp_legend_earned) + max(0, xp_delta)
        row.coin_legend_earned = int(row.coin_legend_earned) + max(0, coin_delta)
        await self._session.flush()
        return row

    async def upsert_learning_path_progress(
        self,
        *,
        user_id: UUID,
        path_version_id: UUID,
        node_id: UUID,
        completed_run_id: UUID,
        completed_at: datetime,
    ) -> None:
        stmt = (
            select(LearningPathProgress)
            .where(
                LearningPathProgress.user_id == user_id,
                LearningPathProgress.path_version_id == path_version_id,
                LearningPathProgress.node_id == node_id,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            row = LearningPathProgress(
                user_id=user_id,
                path_version_id=path_version_id,
                node_id=node_id,
                status=LearningPathProgressStatus.COMPLETED,
                first_completed_run_id=completed_run_id,
                completed_runs_count=1,
                last_completed_at=completed_at,
            )
            self._session.add(row)
        else:
            row.status = LearningPathProgressStatus.COMPLETED
            if row.first_completed_run_id is None:
                row.first_completed_run_id = completed_run_id
            row.completed_runs_count = int(row.completed_runs_count) + 1
            row.last_completed_at = completed_at
        await self._session.flush()

    async def resolve_unit_node_id(self, *, node_id: UUID) -> UUID | None:
        stmt = select(LearningPathNode).where(LearningPathNode.id == node_id).limit(1)
        result = await self._session.execute(stmt)
        node = result.scalar_one_or_none()
        if node is None:
            return None
        if node.node_type == LearningPathNodeType.UNIT:
            return node.id

        parent_node_id = node.parent_node_id
        while parent_node_id is not None:
            parent_stmt = (
                select(LearningPathNode).where(LearningPathNode.id == parent_node_id).limit(1)
            )
            parent_result = await self._session.execute(parent_stmt)
            parent = parent_result.scalar_one_or_none()
            if parent is None:
                return None
            if parent.node_type == LearningPathNodeType.UNIT:
                return parent.id
            parent_node_id = parent.parent_node_id

        return None

    async def increment_legend_review_progress(
        self,
        *,
        user_id: UUID,
        path_version_id: UUID,
        unit_node_id: UUID,
        completed_at: datetime,
    ) -> None:
        stmt = (
            select(LegendReviewProgress)
            .where(
                LegendReviewProgress.user_id == user_id,
                LegendReviewProgress.path_version_id == path_version_id,
                LegendReviewProgress.unit_node_id == unit_node_id,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            row = LegendReviewProgress(
                user_id=user_id,
                path_version_id=path_version_id,
                unit_node_id=unit_node_id,
                legend_round_count=1,
                last_legend_run_at=completed_at,
            )
            self._session.add(row)
        else:
            row.legend_round_count = int(row.legend_round_count) + 1
            row.last_legend_run_at = completed_at
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def _load_option_map(self, question_ids: list[UUID]) -> dict[UUID, list[QuestionOption]]:
        if not question_ids:
            return {}
        stmt = (
            select(QuestionOption)
            .where(QuestionOption.question_id.in_(question_ids))
            .order_by(QuestionOption.sort_order.asc(), QuestionOption.option_key.asc())
        )
        result = await self._session.execute(stmt)
        options = list(result.scalars().all())
        option_map: dict[UUID, list[QuestionOption]] = defaultdict(list)
        for option in options:
            option_map[option.question_id].append(option)
        return option_map
