from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from app.db.models.questions import QuestionType
from app.services.llm.provider_registry import (
    LLMProvider,
    ProviderNotFoundError,
    ProviderRegistry,
)
from app.services.questions.generator import (
    GeneratedQuestion,
    QuestionGenerationError,
    QuestionGenerator,
)
from app.services.questions.validator import (
    QuestionValidator,
    ValidationError,
)


class FakeLLMProvider:
    def __init__(self, responses: list[dict[str, Any]] | None = None) -> None:
        self.responses = responses or []
        self.call_count = 0
        self.last_prompt: str | None = None

    async def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        self.call_count += 1
        self.last_prompt = prompt
        if self.call_count <= len(self.responses):
            return self.responses[self.call_count - 1]
        raise RuntimeError("No more responses configured")


class TestProviderRegistry:
    def test_register_provider_stores_by_name(self) -> None:
        registry = ProviderRegistry()
        provider = FakeLLMProvider()
        registry.register("openai", LLMProvider(name="openai", client=provider))

        result = registry.get("openai")
        assert result is not None
        assert result.name == "openai"
        assert result.client is provider

    def test_get_default_returns_configured_default(self) -> None:
        registry = ProviderRegistry()
        provider = FakeLLMProvider()
        registry.register("openai", LLMProvider(name="openai", client=provider))
        registry.set_default("openai")

        result = registry.get_default()
        assert result is not None
        assert result.name == "openai"

    def test_get_raises_for_unknown_provider(self) -> None:
        registry = ProviderRegistry()

        with pytest.raises(ProviderNotFoundError):
            registry.get("unknown")

    def test_list_providers_returns_all_names(self) -> None:
        registry = ProviderRegistry()
        registry.register("openai", LLMProvider(name="openai", client=FakeLLMProvider()))
        registry.register("anthropic", LLMProvider(name="anthropic", client=FakeLLMProvider()))

        names = registry.list_providers()
        assert set(names) == {"openai", "anthropic"}


class TestQuestionValidator:
    def test_validate_single_choice_accepts_valid_question(self) -> None:
        validator = QuestionValidator()
        question = GeneratedQuestion(
            question_type=QuestionType.SINGLE_CHOICE,
            prompt="What is 2 + 2?",
            options=[
                {"option_key": "A", "content": "3", "is_correct": False},
                {"option_key": "B", "content": "4", "is_correct": True},
                {"option_key": "C", "content": "5", "is_correct": False},
                {"option_key": "D", "content": "6", "is_correct": False},
            ],
            explanation="2 + 2 = 4",
            difficulty=1,
        )

        result = validator.validate(question)
        assert result is True

    def test_validate_multiple_choice_accepts_multiple_correct(self) -> None:
        validator = QuestionValidator()
        question = GeneratedQuestion(
            question_type=QuestionType.MULTIPLE_CHOICE,
            prompt="Select all prime numbers",
            options=[
                {"option_key": "A", "content": "2", "is_correct": True},
                {"option_key": "B", "content": "3", "is_correct": True},
                {"option_key": "C", "content": "4", "is_correct": False},
                {"option_key": "D", "content": "5", "is_correct": True},
            ],
            explanation="2, 3, 5 are prime",
            difficulty=2,
        )

        result = validator.validate(question)
        assert result is True

    def test_validate_true_false_accepts_two_options(self) -> None:
        validator = QuestionValidator()
        question = GeneratedQuestion(
            question_type=QuestionType.TRUE_FALSE,
            prompt="The Earth is flat",
            options=[
                {"option_key": "A", "content": "True", "is_correct": False},
                {"option_key": "B", "content": "False", "is_correct": True},
            ],
            explanation="The Earth is spherical",
            difficulty=1,
        )

        result = validator.validate(question)
        assert result is True

    def test_validate_rejects_single_choice_with_multiple_correct(self) -> None:
        validator = QuestionValidator()
        question = GeneratedQuestion(
            question_type=QuestionType.SINGLE_CHOICE,
            prompt="What is 2 + 2?",
            options=[
                {"option_key": "A", "content": "4", "is_correct": True},
                {"option_key": "B", "content": "4.0", "is_correct": True},
                {"option_key": "C", "content": "5", "is_correct": False},
            ],
            explanation="Both are 4",
            difficulty=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(question)
        assert "exactly one correct option" in str(exc_info.value).lower()

    def test_validate_rejects_true_false_with_wrong_option_count(self) -> None:
        validator = QuestionValidator()
        question = GeneratedQuestion(
            question_type=QuestionType.TRUE_FALSE,
            prompt="Is Python a compiled language?",
            options=[
                {"option_key": "A", "content": "Yes", "is_correct": False},
                {"option_key": "B", "content": "No", "is_correct": True},
                {"option_key": "C", "content": "Maybe", "is_correct": False},
            ],
            explanation="Python is interpreted",
            difficulty=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(question)
        assert "exactly 2 options" in str(exc_info.value).lower()

    def test_validate_rejects_question_without_correct_option(self) -> None:
        validator = QuestionValidator()
        question = GeneratedQuestion(
            question_type=QuestionType.SINGLE_CHOICE,
            prompt="What is 2 + 2?",
            options=[
                {"option_key": "A", "content": "3", "is_correct": False},
                {"option_key": "B", "content": "4", "is_correct": False},
            ],
            explanation="One must be correct",
            difficulty=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(question)
        assert "exactly one correct" in str(exc_info.value).lower()

    def test_validate_rejects_empty_prompt(self) -> None:
        validator = QuestionValidator()
        question = GeneratedQuestion(
            question_type=QuestionType.SINGLE_CHOICE,
            prompt="",
            options=[
                {"option_key": "A", "content": "4", "is_correct": True},
                {"option_key": "B", "content": "5", "is_correct": False},
            ],
            explanation="Empty prompt",
            difficulty=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(question)
        assert "prompt cannot be empty" in str(exc_info.value).lower()

    def test_validate_rejects_too_few_options_for_choice(self) -> None:
        validator = QuestionValidator()
        question = GeneratedQuestion(
            question_type=QuestionType.SINGLE_CHOICE,
            prompt="What is 2 + 2?",
            options=[
                {"option_key": "A", "content": "4", "is_correct": True},
            ],
            explanation="Need more options",
            difficulty=1,
        )

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(question)
        assert "at least 2 options" in str(exc_info.value).lower()

    def test_validate_explanation_rejects_generic_text_without_excerpt_overlap(self) -> None:
        validator = QuestionValidator()

        with pytest.raises(ValidationError) as exc_info:
            validator.validate_explanation(
                "According to the text, this is correct.",
                "Python syntax and dynamic typing make it an interpreted language.",
                "Why is Python interpreted?",
            )

        assert (
            "supporting excerpt" in str(exc_info.value).lower()
            or "stay close" in str(exc_info.value).lower()
        )


class TestQuestionGenerator:
    def make_fake_provider(self, responses: list[dict[str, Any]]) -> FakeLLMProvider:
        return FakeLLMProvider(responses=responses)

    def build_structured_response(
        self,
        questions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {"structured_output": {"questions": questions}}

    @pytest.mark.asyncio
    async def test_generate_returns_validated_questions(self) -> None:
        questions_data = [
            {
                "question_type": "single_choice",
                "prompt": "What is 1 + 1?",
                "options": [
                    {"option_key": "A", "content": "1", "is_correct": False},
                    {"option_key": "B", "content": "2", "is_correct": True},
                    {"option_key": "C", "content": "3", "is_correct": False},
                    {"option_key": "D", "content": "4", "is_correct": False},
                ],
                "explanation": "The excerpt states that 1 + 1 = 2.",
                "source_locator": "Math Basics",
                "metadata": {"supporting_excerpt": "1 + 1 = 2"},
                "difficulty": 1,
            }
        ]
        provider = self.make_fake_provider([self.build_structured_response(questions_data)])
        generator = QuestionGenerator(llm_client=provider)

        result = await generator.generate(
            document_id=uuid4(),
            context="Math Basics: 1 + 1 = 2.",
            question_types=[QuestionType.SINGLE_CHOICE],
            count=1,
        )

        assert len(result) == 1
        assert result[0].prompt == "What is 1 + 1?"
        assert result[0].question_type == QuestionType.SINGLE_CHOICE

    @pytest.mark.asyncio
    async def test_generate_filters_invalid_questions(self) -> None:
        questions_data = [
            {
                "question_type": "single_choice",
                "prompt": "Valid question",
                "options": [
                    {"option_key": "A", "content": "1", "is_correct": True},
                    {"option_key": "B", "content": "2", "is_correct": False},
                ],
                "explanation": "The excerpt states that this is the valid question.",
                "source_locator": "Test context",
                "metadata": {"supporting_excerpt": "Valid question"},
                "difficulty": 1,
            },
            {
                "question_type": "single_choice",
                "prompt": "",
                "options": [
                    {"option_key": "A", "content": "1", "is_correct": True},
                ],
                "explanation": "Invalid - empty prompt",
                "difficulty": 1,
            },
        ]
        provider = self.make_fake_provider([self.build_structured_response(questions_data)])
        generator = QuestionGenerator(llm_client=provider)

        result = await generator.generate(
            document_id=uuid4(),
            context="Test context. Valid question",
            question_types=[QuestionType.SINGLE_CHOICE],
            count=2,
        )

        assert len(result) == 1
        assert result[0].prompt == "Valid question"

    @pytest.mark.asyncio
    async def test_generate_raises_on_llm_failure(self) -> None:
        class FailingProvider:
            async def generate(
                self,
                prompt: str,
                **kwargs: Any,
            ) -> dict[str, Any]:
                _ = prompt
                _ = kwargs
                raise RuntimeError("LLM service unavailable")

        generator = QuestionGenerator(llm_client=FailingProvider())

        with pytest.raises(QuestionGenerationError) as exc_info:
            await generator.generate(
                document_id=uuid4(),
                context="Test",
                question_types=[QuestionType.SINGLE_CHOICE],
                count=1,
            )
        assert "failed to generate" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_generate_includes_document_context_in_prompt(self) -> None:
        provider = self.make_fake_provider(
            [
                self.build_structured_response(
                    [
                        {
                            "question_type": "single_choice",
                            "prompt": "Test",
                            "options": [
                                {"option_key": "A", "content": "Yes", "is_correct": True},
                                {"option_key": "B", "content": "No", "is_correct": False},
                            ],
                            "explanation": "Test",
                            "source_locator": "Plant Notes",
                            "metadata": {"supporting_excerpt": "photosynthesis in plants"},
                            "difficulty": 1,
                        }
                    ]
                )
            ]
        )
        generator = QuestionGenerator(llm_client=provider)

        await generator.generate(
            document_id=uuid4(),
            context="This is about photosynthesis in plants",
            question_types=[QuestionType.SINGLE_CHOICE],
            count=1,
        )

        assert provider.last_prompt is not None
        assert "photosynthesis" in provider.last_prompt
        assert "ONLY use facts that are explicitly stated in the context" in provider.last_prompt
        assert "Do not use outside knowledge" in provider.last_prompt
        assert "source_locator" in provider.last_prompt
        assert '"supporting_excerpt"' in provider.last_prompt
        assert "Generate exactly 1 questions" in provider.last_prompt

    @pytest.mark.asyncio
    async def test_generate_supports_multiple_question_types(self) -> None:
        questions_data = [
            {
                "question_type": "single_choice",
                "prompt": "Single choice question",
                "options": [
                    {"option_key": "A", "content": "1", "is_correct": True},
                    {"option_key": "B", "content": "2", "is_correct": False},
                ],
                "explanation": "The supporting excerpt explicitly identifies this as the single choice question.",
                "source_locator": "Mixed types",
                "metadata": {"supporting_excerpt": "Single choice question"},
                "difficulty": 1,
            },
            {
                "question_type": "true_false",
                "prompt": "True false question",
                "options": [
                    {"option_key": "A", "content": "True", "is_correct": True},
                    {"option_key": "B", "content": "False", "is_correct": False},
                ],
                "explanation": "The supporting excerpt explicitly identifies this as the true false question.",
                "source_locator": "Mixed types",
                "metadata": {"supporting_excerpt": "True false question"},
                "difficulty": 1,
            },
        ]
        provider = self.make_fake_provider([self.build_structured_response(questions_data)])
        generator = QuestionGenerator(llm_client=provider)

        result = await generator.generate(
            document_id=uuid4(),
            context="Mixed types. Single choice question. True false question.",
            question_types=[QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE],
            count=2,
        )

        types = {q.question_type for q in result}
        assert QuestionType.SINGLE_CHOICE in types
        assert QuestionType.TRUE_FALSE in types

    @pytest.mark.asyncio
    async def test_generate_respects_count_parameter(self) -> None:
        questions_data = [
            {
                "question_type": "single_choice",
                "prompt": f"Question {i}",
                "options": [
                    {"option_key": "A", "content": "1", "is_correct": True},
                    {"option_key": "B", "content": "2", "is_correct": False},
                ],
                "explanation": f"The excerpt explicitly references Question {i} as the supported item.",
                "source_locator": "Count Test",
                "metadata": {"supporting_excerpt": f"Question {i}"},
                "difficulty": 1,
            }
            for i in range(5)
        ]
        provider = self.make_fake_provider([self.build_structured_response(questions_data)])
        generator = QuestionGenerator(llm_client=provider)

        result = await generator.generate(
            document_id=uuid4(),
            context="Question 0. Question 1. Question 2. Question 3. Question 4.",
            question_types=[QuestionType.SINGLE_CHOICE],
            count=3,
        )

        assert len(result) == 5
        assert all(q.question_type == QuestionType.SINGLE_CHOICE for q in result)

    @pytest.mark.asyncio
    async def test_generate_filters_questions_without_context_grounding(self) -> None:
        questions_data = [
            {
                "question_type": "single_choice",
                "prompt": "Which year was Python created?",
                "options": [
                    {"option_key": "A", "content": "1989", "is_correct": False},
                    {"option_key": "B", "content": "1991", "is_correct": True},
                ],
                "explanation": "External trivia",
                "source_locator": "Python History",
                "metadata": {"supporting_excerpt": "This quote is absent from the source"},
                "difficulty": 1,
            }
        ]
        provider = self.make_fake_provider([self.build_structured_response(questions_data)])
        generator = QuestionGenerator(llm_client=provider)

        result = await generator.generate(
            document_id=uuid4(),
            context="Python supports multiple programming paradigms.",
            question_types=[QuestionType.SINGLE_CHOICE],
            count=1,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_generate_filters_questions_with_low_quality_explanations(self) -> None:
        questions_data = [
            {
                "question_type": "single_choice",
                "prompt": "Why is Python interpreted?",
                "options": [
                    {"option_key": "A", "content": "Because it is dynamic", "is_correct": True},
                    {"option_key": "B", "content": "Because it is compiled", "is_correct": False},
                ],
                "explanation": "According to the text, this is correct.",
                "source_locator": "一、Python简介",
                "metadata": {"supporting_excerpt": "Python语法和动态类型，以及解释型语言的本质"},
                "difficulty": 1,
            }
        ]
        provider = self.make_fake_provider([self.build_structured_response(questions_data)])
        generator = QuestionGenerator(llm_client=provider)

        result = await generator.generate(
            document_id=uuid4(),
            context="一、Python简介：Python语法和动态类型，以及解释型语言的本质。",
            question_types=[QuestionType.SINGLE_CHOICE],
            count=1,
        )

        assert result == []
