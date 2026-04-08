from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from hashlib import sha1
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import func, select

from app.db.models.profile import UserSetting
from app.db.models.questions import Question, QuestionOption, QuestionType
from app.db.models.review import Mistake
from app.db.models.runs import Run, RunAnswer, RunMode, RunQuestion, RunStatus, Settlement
from app.services.runs.schemas import AnswerResult, QuestionData

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


_BLANK_TOKEN = "____"
_MAX_TOPIC_SOURCE_QUESTIONS = 200
_GENERIC_TOPIC_TERMS = {
    "question",
    "questions",
    "document",
    "based",
    "answer",
    "answers",
    "true",
    "false",
    "correct",
    "incorrect",
    "根据文档",
    "文档内容",
    "正确",
    "错误",
}
_TOPIC_METADATA_KEYS = {
    "knowledge_point",
    "knowledge_points",
    "knowledge",
    "topic",
    "topics",
    "keyword",
    "keywords",
    "tag",
    "tags",
    "concept",
    "concepts",
    "cluster",
    "clusters",
}


def _has_blank_placeholder(prompt: str) -> bool:
    return _BLANK_TOKEN in prompt or "___" in prompt


def _resolve_language_family(language_code: str | None) -> str:
    normalized = (language_code or "en").strip().lower()
    if normalized.startswith("zh"):
        return "zh"
    if normalized.startswith("en"):
        return "en"
    return "other"


def _blank_separator(language_family: str) -> str:
    return "、" if language_family == "zh" else ", "


def _strip_trailing_question(text: str) -> str:
    return re.sub(r"[\s\uFF1F?\u3002.!\uFF01]+$", "", text.strip())


def _stable_int(text: str) -> int:
    return int.from_bytes(sha1(text.encode("utf-8")).digest()[:8], "big", signed=False)


def _canonical_topic_term(raw: str) -> str | None:
    cleaned = (
        re.sub(r"\s+", " ", raw)
        .strip()
        .strip("\uff0c\u3002,.!?\uff01\uff1f:\uff1a;\uff1b()[]{}\"'")
    )
    if not cleaned:
        return None
    lowered = cleaned.lower()
    if lowered in _GENERIC_TOPIC_TERMS:
        return None
    if len(cleaned) <= 1:
        return None
    return cleaned


def _extract_topic_terms_from_value(value: object, sink: list[str]) -> None:
    if isinstance(value, str):
        candidate = _canonical_topic_term(value)
        if candidate is not None:
            sink.append(candidate)
        return
    if isinstance(value, list):
        for item in value:
            _extract_topic_terms_from_value(item, sink)
        return
    if isinstance(value, dict):
        for key, nested in value.items():
            key_normalized = str(key).strip().lower()
            if key_normalized in _TOPIC_METADATA_KEYS:
                _extract_topic_terms_from_value(nested, sink)
                continue
            if isinstance(nested, (dict, list)):
                _extract_topic_terms_from_value(nested, sink)


def _extract_topic_terms(
    *,
    metadata: dict[str, object] | None,
    prompt: str,
    explanation: str | None,
) -> list[str]:
    candidates: list[str] = []
    if isinstance(metadata, dict):
        _extract_topic_terms_from_value(metadata, candidates)

    text_blob = f"{prompt}\n{explanation or ''}"
    for token in re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,}|[\u4e00-\u9fff]{2,8}", text_blob):
        candidate = _canonical_topic_term(token)
        if candidate is not None:
            candidates.append(candidate)

    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def _select_questions_for_path(
    question_rows: list[Any],
    *,
    count: int,
    path_id: str | None,
) -> list[Any]:
    if count <= 0:
        return []
    if not path_id or len(question_rows) <= count:
        return question_rows[:count]

    pool_size = len(question_rows)
    offset = _stable_int(f"offset:{path_id}") % pool_size
    rotated = question_rows[offset:] + question_rows[:offset]

    sample_size = min(pool_size, max(count * 3, count))
    sampled_pool = rotated[:sample_size]
    ordered = sorted(
        sampled_pool,
        key=lambda item: (
            _stable_int(f"{path_id}:{item.id}"),
            item.created_at,
            str(item.id),
        ),
    )

    anchor_count = min(max(1, count // 4), count)
    anchor = question_rows[:anchor_count]
    selected: list[Any] = list(anchor)
    selected_ids = {item.id for item in selected}

    for item in ordered:
        if item.id in selected_ids:
            continue
        selected.append(item)
        selected_ids.add(item.id)
        if len(selected) >= count:
            return selected

    for item in rotated:
        if item.id in selected_ids:
            continue
        selected.append(item)
        if len(selected) >= count:
            break
    return selected[:count]


def _resolve_path_selection_count(
    *,
    mode: RunMode,
    available_count: int,
    requested_count: int,
    path_id: str | None,
) -> int:
    if available_count <= 0 or requested_count <= 0:
        return 0

    target_count = min(available_count, requested_count)

    if (
        mode == RunMode.DRAFT
        and path_id
        and available_count > 1
        and target_count >= available_count
    ):
        return available_count - 1

    return target_count


def _apply_zh_cloze_patterns(stem: str, blank_segment: str) -> str | None:
    direct_patterns = (
        (r"^(.+?)是谁$", rf"\1是{_BLANK_TOKEN}"),
        (r"^(.+?)是什么$", rf"\1是{_BLANK_TOKEN}"),
        (r"^以下哪些是(.+)$", rf"\1包括{blank_segment}"),
        (r"^哪些是(.+)$", rf"\1包括{blank_segment}"),
    )
    for pattern, replacement in direct_patterns:
        if re.search(pattern, stem):
            return re.sub(pattern, replacement, stem)

    token_replacements = (
        ("哪一年", "____年"),
        ("哪一个", _BLANK_TOKEN),
        ("哪一项", _BLANK_TOKEN),
        ("哪一位", _BLANK_TOKEN),
        ("什么时候", _BLANK_TOKEN),
        ("哪个", _BLANK_TOKEN),
        ("哪项", _BLANK_TOKEN),
        ("哪种", _BLANK_TOKEN),
        ("哪位", _BLANK_TOKEN),
        ("哪些", blank_segment),
        ("什么", _BLANK_TOKEN),
        ("谁", _BLANK_TOKEN),
        ("何时", _BLANK_TOKEN),
        ("哪里", _BLANK_TOKEN),
        ("哪儿", _BLANK_TOKEN),
        ("是否", _BLANK_TOKEN),
    )
    for source, target in token_replacements:
        if source in stem:
            return stem.replace(source, target, 1)
    return None


def _apply_en_cloze_patterns(stem: str, blank_segment: str) -> str | None:
    normalized = stem.strip()
    direct_patterns = (
        (r"^Who\s+(.+)$", rf"{_BLANK_TOKEN} \1"),
        (r"^Which\s+(.+)$", rf"{_BLANK_TOKEN} \1"),
        (r"^What is\s+(.+)$", rf"\1 is {_BLANK_TOKEN}"),
        (r"^What are\s+(.+)$", rf"\1 are {blank_segment}"),
        (r"^When was\s+(.+)$", rf"\1 was {_BLANK_TOKEN}"),
        (r"^Where is\s+(.+)$", rf"\1 is {_BLANK_TOKEN}"),
        (r"^How many\s+(.+)$", rf"\1: {_BLANK_TOKEN}"),
    )
    for pattern, replacement in direct_patterns:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    return None


def _normalize_draft_prompt(
    prompt: str,
    *,
    question_type: QuestionType,
    correct_option_texts: list[str],
    language_code: str = "en",
) -> str:
    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        return normalized_prompt

    language_family = _resolve_language_family(language_code)
    if _has_blank_placeholder(normalized_prompt):
        return normalized_prompt

    blank_count = max(1, len(correct_option_texts))
    if question_type != QuestionType.MULTIPLE_CHOICE:
        blank_count = 1
    blank_segment = _blank_separator(language_family).join([_BLANK_TOKEN] * blank_count)

    if correct_option_texts:
        replaced_prompt = normalized_prompt
        replacements = 0
        for answer_text in correct_option_texts:
            candidate = answer_text.strip()
            if not candidate or candidate not in replaced_prompt:
                continue
            replaced_prompt = replaced_prompt.replace(candidate, _BLANK_TOKEN, 1)
            replacements += 1
            if replacements >= blank_count:
                break
        if _has_blank_placeholder(replaced_prompt):
            return replaced_prompt

    stem = _strip_trailing_question(normalized_prompt)

    if language_family == "zh":
        zh_prompt = _apply_zh_cloze_patterns(stem, blank_segment)
        if zh_prompt is not None:
            return f"{zh_prompt}。"
        return f"请根据文档将空格补充完整: {stem} {blank_segment}。"

    en_prompt = _apply_en_cloze_patterns(stem, blank_segment)
    if en_prompt is not None:
        return f"{en_prompt}."
    return f"{stem} {blank_segment}."


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(
        self,
        *,
        user_id: UUID,
        document_id: UUID | None,
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
        clear_ended_at: bool = False,
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
        if clear_ended_at:
            run.ended_at = None
        elif ended_at is not None:
            run.ended_at = ended_at

        await self._session.flush()

    async def list_document_questions(
        self,
        *,
        document_id: UUID | None,
        mode: RunMode,
        count: int,
        path_id: str | None = None,
        user_id: UUID | None = None,
    ) -> list[QuestionData]:
        language_code = "en"
        if mode == RunMode.DRAFT and user_id is not None:
            language_code = await self.get_user_language_code(user_id)

        if mode == RunMode.REVIEW and user_id is not None:
            stmt = select(Question).join(Mistake, Mistake.question_id == Question.id)
            stmt = stmt.where(Mistake.user_id == user_id)
            if document_id is not None:
                stmt = stmt.where(Mistake.document_id == document_id)
            stmt = stmt.distinct(Question.id)
        else:
            if document_id is None:
                return []
            stmt = select(Question).where(Question.document_id == document_id)

        # Filter by question type based on mode
        if mode == RunMode.SPEED:
            # Speed mode uses TRUE_FALSE questions
            stmt = stmt.where(Question.question_type == QuestionType.TRUE_FALSE)
        elif mode == RunMode.DRAFT:
            # Draft mode prefers SINGLE_CHOICE and MULTIPLE_CHOICE
            stmt = stmt.where(
                Question.question_type.in_(
                    [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE]
                )
            )
        elif mode == RunMode.ENDLESS:
            # Endless mode uses FILL_IN_BLANK questions
            stmt = stmt.where(Question.question_type == QuestionType.FILL_IN_BLANK)

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
        if path_id:
            fetch_limit = max(fetch_limit, count * 4)
        stmt = stmt.limit(fetch_limit)

        result = await self._session.execute(stmt)
        question_rows = list(result.scalars().all())

        if not question_rows:
            return []

        target_count = _resolve_path_selection_count(
            mode=mode,
            available_count=len(question_rows),
            requested_count=count,
            path_id=path_id,
        )

        if mode == RunMode.DRAFT:
            hard = [q for q in question_rows if q.difficulty >= 3]
            soft = [q for q in question_rows if q.difficulty < 3]
            ordered = hard + soft
            question_rows = _select_questions_for_path(
                ordered,
                count=target_count,
                path_id=path_id,
            )
        else:
            question_rows = _select_questions_for_path(
                question_rows,
                count=target_count,
                path_id=path_id,
            )

        question_ids = [q.id for q in question_rows]
        option_map = await self._load_option_map(question_ids)

        questions: list[QuestionData] = []
        for question in question_rows:
            options = option_map.get(question.id, [])
            correct_options = [option for option in options if option.is_correct]
            # Extract correct_answer from metadata for FILL_IN_BLANK questions
            metadata = question.question_metadata or {}
            raw_answer = (
                metadata.get("answer")
                if question.question_type == QuestionType.FILL_IN_BLANK
                else None
            )
            correct_answer: str | None = str(raw_answer) if raw_answer is not None else None
            prompt_text = question.prompt
            if mode == RunMode.DRAFT:
                prompt_text = _normalize_draft_prompt(
                    question.prompt,
                    question_type=question.question_type,
                    correct_option_texts=[option.content for option in correct_options],
                    language_code=language_code,
                )
            questions.append(
                QuestionData(
                    id=question.id,
                    document_id=question.document_id,
                    question_text=prompt_text,
                    question_type=question.question_type.value,
                    options=[{"id": str(option.id), "text": option.content} for option in options],
                    correct_option_ids=[option.id for option in correct_options],
                    difficulty=question.difficulty,
                    chapter_reference=None,
                    correct_answer=correct_answer,
                    explanation=question.explanation,
                )
            )

        return questions

    async def count_review_questions(self, *, document_id: UUID | None, user_id: UUID) -> int:
        stmt = select(func.count(func.distinct(Mistake.question_id))).select_from(Mistake)
        stmt = stmt.where(Mistake.user_id == user_id)
        if document_id is not None:
            stmt = stmt.where(Mistake.document_id == document_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def create_mistake(
        self,
        *,
        user_id: UUID,
        question_id: UUID,
        document_id: UUID,
        run_id: UUID,
        explanation: str | None = None,
    ) -> None:
        mistake = Mistake(
            user_id=user_id,
            question_id=question_id,
            document_id=document_id,
            run_id=run_id,
            explanation=explanation,
        )
        self._session.add(mistake)
        await self._session.flush()

    async def get_user_language_code(self, user_id: UUID) -> str:
        stmt = select(UserSetting.language_code).where(UserSetting.user_id == user_id)
        result = await self._session.execute(stmt)
        language_code = result.scalar_one_or_none()
        return str(language_code or "en")

    async def count_document_questions(self, *, document_id: UUID) -> int:
        """Count total questions available for a document."""
        stmt = select(func.count()).select_from(Question).where(Question.document_id == document_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def list_document_knowledge_points(
        self,
        *,
        document_id: UUID,
        limit: int = 8,
    ) -> list[str]:
        if limit <= 0:
            return []

        stmt = (
            select(Question.question_metadata, Question.prompt, Question.explanation)
            .where(Question.document_id == document_id)
            .order_by(Question.created_at.asc())
            .limit(_MAX_TOPIC_SOURCE_QUESTIONS)
        )
        result = await self._session.execute(stmt)
        rows = list(result.all())
        if not rows:
            return []

        counts: dict[str, int] = defaultdict(int)
        first_seen: dict[str, int] = {}
        for idx, (metadata, prompt, explanation) in enumerate(rows):
            terms = _extract_topic_terms(
                metadata=metadata if isinstance(metadata, dict) else None,
                prompt=str(prompt or ""),
                explanation=str(explanation) if explanation is not None else None,
            )
            for term in terms:
                normalized = term.lower()
                counts[normalized] += 1
                if normalized not in first_seen:
                    first_seen[normalized] = idx

        ranked = sorted(counts.keys(), key=lambda key: (-counts[key], first_seen[key], key))
        return list(ranked[:limit])

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
                "correct_answer": question.correct_answer,  # For FILL_IN_BLANK
                "explanation": question.explanation,  # For feedback
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
                    "correct_answer": snapshot.get("correct_answer"),  # For FILL_IN_BLANK
                    "explanation": snapshot.get("explanation"),  # For feedback
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
