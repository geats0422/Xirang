from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.db.models.questions import QuestionType
from app.services.questions.validator import QuestionValidator, ValidationError


class LLMClientProtocol(Protocol):
    """Protocol for LLM client used in question generation."""

    async def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]: ...


class QuestionGenerationError(Exception):
    """Error during question generation."""

    pass


# Mode-specific prompt templates for different game modes
# Each game mode requires different question formats

# Endless Abyss: Fill-in-the-blank questions (填空题)
ENDLESS_ABYSS_PROMPT = """Context from study material:
{context}

Generate {count} fill-in-the-blank questions for "Endless Abyss" game mode.
Requirements:
- Each question MUST be fill-in-the-blank format with "____" placeholder
- The blank should hide a KEY TERM or important concept from the context
- Provide 1-3 hints for each blank (starting letter, length, related concept)
- The correct_answer field should contain the exact word(s) that fill the blank

For each question, provide:
- question_type: "fill_in_blank"
- prompt: the question text with "____" where the blank should be
- options: empty array [] (fill-in-blank has no options)
- correct_answer: the exact word/phrase that fills the blank
- hints: array of hint strings (e.g., ["Starts with D", "5 letters", "A philosophical concept"])
- explanation: why this answer is correct
- difficulty: 1-5 scale

Return as JSON with a "questions" array."""

# Speed Survival: True/False questions (判断题)
SPEED_SURVIVAL_PROMPT = """Context from study material:
{context}

Generate {count} true/false questions for "Speed Survival" game mode.
Requirements:
- Each question is a statement that is either TRUE or FALSE based on the context
- Statements should test understanding of key concepts
- Avoid trivially true/false statements - make them thought-provoking
- Mix of true and false statements (approximately 50/50)

For each question, provide:
- question_type: "true_false"
- prompt: a declarative statement (NOT a question)
- options: array with two items:
  - {option_key: "A", content: "正确 / True", is_correct: true/false}
  - {option_key: "B", content: "错误 / False", is_correct: true/false}
- explanation: why the statement is true or false
- difficulty: 1-5 scale

Return as JSON with a "questions" array."""

# The Knowledge Draft: Single/Multiple choice (displayed as fill-in-blank in frontend)
KNOWLEDGE_DRAFT_PROMPT = """Context from study material:
{context}

Generate {count} multiple-choice questions for "The Knowledge Draft" game mode.
Requirements:
- Questions can be single_choice or multiple_choice
- All questions will be DISPLAYED as fill-in-blank in the frontend
- The prompt should contain a statement with "____" blank
- Options should be possible words/phrases that could fill the blank
- For single_choice: exactly one correct answer
- For multiple_choice: two or more correct answers

For each question, provide:
- question_type: "single_choice" or "multiple_choice"
- prompt: statement with "____" blank (e.g., "The concept of ____ emphasizes harmony")
- options: array of possible answers:
  - {option_key: "A", content: "possible answer 1", is_correct: true/false}
  - {option_key: "B", content: "possible answer 2", is_correct: true/false}
  - {option_key: "C", content: "possible answer 3", is_correct: true/false}
  - {option_key: "D", content: "possible answer 4", is_correct: true/false}
- explanation: why the correct answer(s) fill the blank
- difficulty: 1-5 scale

Return as JSON with a "questions" array."""

# Default/fallback prompt (legacy)
_PROMPT_TEMPLATE = """Context:
{context}

Question types to generate: {type_names_str}

For each question, provide:
- question_type: one of "single_choice", "multiple_choice", "true_false", "fill_in_blank"
- prompt: the question text
- options: array of options with option_key (A, B, C, D), content, and is_correct
- correct_answer: for fill_in_blank questions, the answer that fills the blank
- hints: for fill_in_blank questions, array of hint strings
- explanation: why the correct answer is correct
- difficulty: 1-5 scale

Return as JSON with a "questions" array."""

# Game mode to prompt mapping
GAME_MODE_PROMPTS = {
    "endless-abyss": ENDLESS_ABYSS_PROMPT,
    "speed-survival": SPEED_SURVIVAL_PROMPT,
    "knowledge-draft": KNOWLEDGE_DRAFT_PROMPT,
}

# Question types required per game mode
GAME_MODE_QUESTION_TYPES = {
    "endless-abyss": ["fill_in_blank"],
    "speed-survival": ["true_false"],
    "knowledge-draft": ["single_choice", "multiple_choice"],
}


_QUESTION_TYPE_MAP = {
    "single_choice": QuestionType.SINGLE_CHOICE,
    "multiple_choice": QuestionType.MULTIPLE_CHOICE,
    "true_false": QuestionType.TRUE_FALSE,
    "fill_in_blank": QuestionType.FILL_IN_BLANK,
}


@dataclass
class GeneratedQuestion:
    question_type: QuestionType
    prompt: str
    options: list[dict[str, Any]]
    explanation: str | None = None
    source_locator: str | None = None
    difficulty: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    correct_answer: str | None = None
    hints: list[str] | None = None


class QuestionGeneratorProtocol(Protocol):
    async def generate(
        self,
        context: str,
        question_types: list[QuestionType],
        count: int,
        *,
        document_id: Any = None,
        game_mode: str | None = None,
        model: str | None = None,
    ) -> list[GeneratedQuestion]: ...


class QuestionGenerator:
    def __init__(self, llm_client: LLMClientProtocol) -> None:
        self._llm = llm_client
        self._validator = QuestionValidator()

    async def generate(
        self,
        context: str,
        question_types: list[QuestionType],
        count: int,
        *,
        document_id: Any = None,
        game_mode: str | None = None,
        model: str | None = None,
    ) -> list[GeneratedQuestion]:
        # Select prompt template based on game mode
        if game_mode and game_mode in GAME_MODE_PROMPTS:
            prompt_template = GAME_MODE_PROMPTS[game_mode]
            # Override question_types with mode-specific types
            mode_types = GAME_MODE_QUESTION_TYPES.get(game_mode, [])
            question_types = [_QUESTION_TYPE_MAP[t] for t in mode_types if t in _QUESTION_TYPE_MAP]
        else:
            prompt_template = _PROMPT_TEMPLATE

        type_names = [qt.value if hasattr(qt, "value") else str(qt) for qt in question_types]
        type_names_str = ", ".join(type_names)
        prompt = prompt_template.format(
            context=context[:4000],  # Limit context length to avoid token limits
            type_names_str=type_names_str,
            count=count,
        )

        generate_kwargs: dict[str, Any] = {
            "response_format": {"type": "json_object"},
        }
        if model:
            generate_kwargs["model"] = model

        try:
            response_raw = await self._llm.generate(
                prompt=prompt,
                **generate_kwargs,
            )
        except Exception as exc:
            raise QuestionGenerationError(f"Failed to generate questions: {exc}") from exc

        response_data: dict[str, Any]
        if isinstance(response_raw, dict):
            response_data = response_raw
        else:
            response_data = {"content": str(response_raw)}

        parsed = self._parse_response(response_data)
        questions = [self._build_question(data) for data in parsed]

        # Validate each question
        valid_questions = []
        for q in questions:
            try:
                self._validator.validate_question(
                    q.question_type,
                    q.prompt,
                    q.options,
                )
                valid_questions.append(q)
            except ValidationError:
                continue

        return valid_questions

    def _parse_response(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        if "structured_output" in response:
            output = response["structured_output"]
            if isinstance(output, dict) and "questions" in output:
                questions = output["questions"]
                if isinstance(questions, list):
                    return [item for item in questions if isinstance(item, dict)]
                return []
        if "content" in response:
            try:
                parsed = json.loads(response["content"])
                if isinstance(parsed, dict) and "questions" in parsed:
                    questions = parsed["questions"]
                    if isinstance(questions, list):
                        return [item for item in questions if isinstance(item, dict)]
                    return []
            except ValueError:
                pass
        return []

    def _build_question(self, data: dict[str, Any]) -> GeneratedQuestion:
        type_str = data.get("question_type", "single_choice")
        question_type = _QUESTION_TYPE_MAP.get(type_str, QuestionType.SINGLE_CHOICE)

        return GeneratedQuestion(
            question_type=question_type,
            prompt=data.get("prompt", ""),
            options=data.get("options", []),
            explanation=data.get("explanation"),
            source_locator=data.get("source_locator"),
            difficulty=data.get("difficulty", 1),
            metadata=data.get("metadata", {}),
        )
