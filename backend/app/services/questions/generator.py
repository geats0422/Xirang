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


_PROMPT_TEMPLATE = """Context:
{context}

Question types to generate: {type_names_str}

For each question, provide:
- question_type: one of "single_choice", "multiple_choice", "true_false"
- prompt: the question text
- options: array of options with option_key (A, B, C, D), content, and is_correct
- explanation: why the correct answer is correct
- difficulty: 1-5 scale

Return as JSON with a "questions" array."""


_QUESTION_TYPE_MAP = {
    "single_choice": QuestionType.SINGLE_CHOICE,
    "multiple_choice": QuestionType.MULTIPLE_CHOICE,
    "true_false": QuestionType.TRUE_FALSE,
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


class QuestionGeneratorProtocol(Protocol):
    async def generate(
        self,
        context: str,
        question_types: list[QuestionType],
        count: int,
        *,
        document_id: Any = None,
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
    ) -> list[GeneratedQuestion]:
        # Convert question types to strings
        type_names = [qt.value if hasattr(qt, "value") else str(qt) for qt in question_types]
        type_names_str = ", ".join(type_names)
        prompt = _PROMPT_TEMPLATE.format(
            context=context,
            type_names_str=type_names_str,
        )

        try:
            response_raw = await self._llm.generate(
                prompt=prompt,
                response_format={"type": "json_object"},
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
