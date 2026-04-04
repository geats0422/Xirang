from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.db.models.questions import QuestionType
from app.db.models.runs import RunMode
from app.repositories.run_repository import (
    _normalize_draft_prompt,
    _resolve_path_selection_count,
    _select_questions_for_path,
)


def test_normalize_draft_prompt_keeps_existing_blank() -> None:
    prompt = "Python的创始人是 ____。"
    result = _normalize_draft_prompt(
        prompt,
        question_type=QuestionType.SINGLE_CHOICE,
        correct_option_texts=["吉多范罗苏姆"],
        language_code="zh-CN",
    )
    assert result == prompt


def test_normalize_draft_prompt_appends_single_blank_when_missing() -> None:
    result = _normalize_draft_prompt(
        "Python的创始人是谁?",
        question_type=QuestionType.SINGLE_CHOICE,
        correct_option_texts=["吉多范罗苏姆"],
        language_code="zh-CN",
    )
    assert result == "Python的创始人是____。"


def test_normalize_draft_prompt_uses_multiple_blanks_for_multi_choice() -> None:
    result = _normalize_draft_prompt(
        "以下哪些是Python的应用领域?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        correct_option_texts=["Web开发", "网络爬虫", "人工智能"],
        language_code="zh-CN",
    )
    assert result.count("____") == 3
    assert result == "Python的应用领域包括____、____、____。"


def test_normalize_draft_prompt_generates_natural_english_cloze() -> None:
    result = _normalize_draft_prompt(
        "Which key can open the debug selector in PyCharm?",
        question_type=QuestionType.SINGLE_CHOICE,
        correct_option_texts=["Shift + F9"],
        language_code="en-US",
    )
    assert result == "____ key can open the debug selector in PyCharm."


@dataclass
class _QuestionRow:
    id: UUID
    created_at: datetime


def _build_question_rows(count: int) -> list[_QuestionRow]:
    base_time = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        _QuestionRow(id=UUID(int=i + 1), created_at=base_time + timedelta(minutes=i))
        for i in range(count)
    ]


def test_select_questions_for_path_is_stable_for_same_path() -> None:
    rows = _build_question_rows(20)

    first = _select_questions_for_path(rows, count=8, path_id="F1")
    second = _select_questions_for_path(rows, count=8, path_id="F1")

    assert [item.id for item in first] == [item.id for item in second]


def test_select_questions_for_different_paths_not_identical_with_controlled_overlap() -> None:
    rows = _build_question_rows(24)

    floor_1 = _select_questions_for_path(rows, count=8, path_id="F1")
    floor_2 = _select_questions_for_path(rows, count=8, path_id="F2")

    floor_1_ids = {item.id for item in floor_1}
    floor_2_ids = {item.id for item in floor_2}
    assert floor_1_ids != floor_2_ids
    assert len(floor_1_ids & floor_2_ids) >= 1


def test_select_questions_for_small_pool_falls_back_to_prefix() -> None:
    rows = _build_question_rows(5)

    selected = _select_questions_for_path(rows, count=8, path_id="F1")

    assert [item.id for item in selected] == [item.id for item in rows]


def test_resolve_path_selection_count_reduces_draft_when_pool_equals_request() -> None:
    count = _resolve_path_selection_count(
        mode=RunMode.DRAFT,
        available_count=10,
        requested_count=10,
        path_id="draft-route-classic",
    )
    assert count == 9


def test_draft_small_pool_different_paths_not_fully_overlapping() -> None:
    rows = _build_question_rows(10)
    selected_count = _resolve_path_selection_count(
        mode=RunMode.DRAFT,
        available_count=len(rows),
        requested_count=10,
        path_id="draft-route-classic",
    )

    classic = _select_questions_for_path(
        rows,
        count=selected_count,
        path_id="draft-route-classic",
    )
    theory = _select_questions_for_path(
        rows,
        count=selected_count,
        path_id="draft-route-theory",
    )

    classic_ids = {item.id for item in classic}
    theory_ids = {item.id for item in theory}
    assert len(classic_ids) == 9
    assert len(theory_ids) == 9
    assert classic_ids != theory_ids
