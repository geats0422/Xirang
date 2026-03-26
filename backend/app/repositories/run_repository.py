from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Select, func, select

from app.db.models.documents import DocumentQuestionSet, QuestionSetStatus
from app.db.models.questions import Question, QuestionOption, QuestionType
from app.db.models.runs import Run, RunAnswer, RunMode, RunQuestion, RunStatus, Settlement
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

        if not question_rows:
            fallback_stmt: Select[tuple[Question]] = select(Question).order_by(
                Question.created_at.asc()
            )
            fallback_stmt = fallback_stmt.limit(fetch_limit)
            fallback_result = await self._session.execute(fallback_stmt)
            question_rows = list(fallback_result.scalars().all())

        if not question_rows:
            generated_question = await self._ensure_fallback_question(document_id=document_id)
            question_rows = [generated_question]

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
                }
            )
        return payload

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

    async def _ensure_fallback_question(self, *, document_id: UUID) -> Question:
        question_set_stmt = (
            select(DocumentQuestionSet)
            .where(DocumentQuestionSet.document_id == document_id)
            .order_by(DocumentQuestionSet.generation_version.desc())
            .limit(1)
        )
        question_set_result = await self._session.execute(question_set_stmt)
        question_set = question_set_result.scalar_one_or_none()

        if question_set is None:
            question_set = DocumentQuestionSet(
                document_id=document_id,
                generation_version=1,
                status=QuestionSetStatus.READY,
                question_count=1,
                generated_at=datetime.now(UTC),
            )
            self._session.add(question_set)
            await self._session.flush()

        question = Question(
            question_set_id=question_set.id,
            document_id=document_id,
            question_type=QuestionType.SINGLE_CHOICE,
            prompt="In Daoist thought, which concept emphasizes flowing in harmony with nature?",
            explanation="Wu wei highlights effortless alignment with the natural order.",
            source_locator={"kind": "fallback"},
            difficulty=1,
            question_metadata={"source": "runtime_fallback"},
        )
        self._session.add(question)
        await self._session.flush()

        self._session.add_all(
            [
                QuestionOption(
                    question_id=question.id,
                    option_key="A",
                    content="Wu wei",
                    is_correct=True,
                    sort_order=1,
                ),
                QuestionOption(
                    question_id=question.id,
                    option_key="B",
                    content="Legalism",
                    is_correct=False,
                    sort_order=2,
                ),
            ]
        )
        await self._session.flush()

        return question
