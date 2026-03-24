"""Question validator."""

from __future__ import annotations

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

    def validate_single_choice(self, question: Any) -> bool:
        self.validate(question)
        return True

    def validate_true_false(self, question: Any) -> bool:
        self.validate(question)
        return True

    def validate_multiple_choice(self, question: Any) -> bool:
        self.validate(question)
        return True
