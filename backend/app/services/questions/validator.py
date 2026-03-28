"""Question validator."""

from __future__ import annotations

import re
from typing import Any


class ValidationError(Exception):
    """Validation error for questions."""

    pass


class QuestionValidator:
    """Validator for questions."""

    def validate(self, question: Any) -> bool:
        """Validate a question (accepts dict or GeneratedQuestion)."""
        # Handle both dict and dataclass
        if hasattr(question, "__dict__"):
            prompt = getattr(question, "prompt", "") or ""
            options = getattr(question, "options", []) or []
            qtype = getattr(question, "question_type", None)
        else:
            prompt = question.get("prompt", "") or ""
            options = question.get("options", []) or []
            qtype = question.get("question_type", None)

        if not prompt:
            raise ValidationError("prompt cannot be empty")

        if not options or len(options) < 2:
            raise ValidationError("at least 2 options required")

        # Check for correct options
        correct = []
        for o in options:
            if isinstance(o, dict):
                if o.get("is_correct"):
                    correct.append(o)
            elif hasattr(o, "is_correct") and o.is_correct:
                correct.append(o)

        if not correct:
            raise ValidationError("exactly one correct option must be marked")

        # Type-specific validation
        if qtype:
            from app.db.models.questions import QuestionType

            if qtype == QuestionType.SINGLE_CHOICE:
                if len(correct) != 1:
                    raise ValidationError("exactly one correct option allowed")
            elif qtype == QuestionType.TRUE_FALSE and len(options) != 2:
                raise ValidationError("exactly 2 options required")

        return True

    def validate_question(
        self,
        question_type: Any,
        prompt: str,
        options: list[dict[str, Any]],
    ) -> bool:
        if not prompt:
            raise ValidationError("prompt cannot be empty")
        if not options or len(options) < 2:
            raise ValidationError("at least 2 options required")
        correct = [o for o in options if isinstance(o, dict) and o.get("is_correct")]
        if not correct:
            raise ValidationError("exactly one correct option must be marked")
        return True

    def validate_explanation(
        self,
        explanation: str | None,
        supporting_excerpt: str | None,
        prompt: str,
    ) -> bool:
        normalized_explanation = (explanation or "").strip()
        normalized_excerpt = (supporting_excerpt or "").strip()

        if len(normalized_explanation) < 12:
            raise ValidationError("explanation is too short")

        if normalized_explanation.lower() == prompt.strip().lower():
            raise ValidationError("explanation must add reasoning beyond the prompt")

        if not normalized_excerpt:
            raise ValidationError("supporting excerpt is required for explanation validation")

        if not self._has_meaningful_overlap(normalized_explanation, normalized_excerpt):
            raise ValidationError("explanation must stay close to supporting excerpt")

        return True

    @staticmethod
    def _has_meaningful_overlap(explanation: str, excerpt: str) -> bool:
        compact_explanation = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]", "", explanation).lower()
        compact_excerpt = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]", "", excerpt).lower()
        if compact_explanation and compact_excerpt:
            if compact_excerpt in compact_explanation or compact_explanation in compact_excerpt:
                return True

        def tokenize(text: str) -> set[str]:
            latin_tokens = {token.lower() for token in re.findall(r"[A-Za-z0-9_]{3,}", text)}
            cjk_tokens: set[str] = set()
            for token in re.findall(r"[\u4e00-\u9fff]{2,}", text):
                if len(token) == 2:
                    cjk_tokens.add(token)
                    continue
                cjk_tokens.update(token[index : index + 2] for index in range(len(token) - 1))
            return latin_tokens | cjk_tokens

        explanation_tokens = tokenize(explanation)
        excerpt_tokens = tokenize(excerpt)
        if explanation_tokens and excerpt_tokens:
            return bool(explanation_tokens & excerpt_tokens)

        return excerpt in explanation or explanation in excerpt

    def validate_single_choice(self, question: Any) -> bool:
        self.validate(question)
        return True

    def validate_true_false(self, question: Any) -> bool:
        self.validate(question)
        return True

    def validate_multiple_choice(self, question: Any) -> bool:
        self.validate(question)
        return True
