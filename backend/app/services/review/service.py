from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.agents.client import AgentsClient
from app.services.review.embeddings import OpenAIEmbeddingService
from app.services.review.facade import ReviewService
from app.services.review.repository import ReviewRepository
from app.services.review.vector_backend import PgvectorBackend

logger = logging.getLogger(__name__)


class LLMExplainerService:
    """LLM-based explainer service that generates explanations for mistakes."""

    def __init__(self, llm_client: AgentsClient | None = None) -> None:
        self._llm_client = llm_client

    async def explain_mistake(
        self,
        mistake: Any,
        question: Any,
        document_context: Any,
        similar_mistakes: Any,
    ) -> str:
        """Generate an explanation for a mistake using LLM or fallback to stored explanation."""
        # First, try to use the stored explanation from the question
        if hasattr(mistake, "explanation") and mistake.explanation:
            stored_explanation: str = mistake.explanation
            return stored_explanation

        # If no stored explanation and LLM is available, generate one
        if self._llm_client is None:
            return "Explanation not available."

        try:
            prompt = self._build_explanation_prompt(
                question=question,
                document_context=document_context,
                similar_mistakes=similar_mistakes,
            )
            response = await self._llm_client.generate(prompt)
            content = response.get("content")
            if isinstance(content, str):
                return content
            return "Explanation generation failed."
        except Exception as e:
            logger.warning("Failed to generate explanation via LLM: %s", e)
            return "Explanation not available."

    def _build_explanation_prompt(
        self,
        question: Any,
        document_context: Any,
        similar_mistakes: Any,
    ) -> str:
        """Build a prompt for LLM to generate an explanation."""
        prompt_parts = [
            "You are a helpful tutor explaining why an answer was incorrect.",
            "",
            f"Question: {question}",
        ]

        if document_context:
            prompt_parts.extend(
                [
                    "",
                    f"Document Context: {document_context[:2000]}",
                ]
            )

        if similar_mistakes:
            prompt_parts.extend(
                [
                    "",
                    "Similar mistakes from other learners:",
                ]
            )
            for i, m in enumerate(similar_mistakes[:3], 1):
                if hasattr(m, "explanation") and m.explanation:
                    prompt_parts.append(f"{i}. {m.explanation[:200]}")

        prompt_parts.extend(
            [
                "",
                "Please provide a clear, concise explanation of why the answer was incorrect",
                "and what the correct answer should be. Keep it under 200 words.",
            ]
        )

        return "\n".join(prompt_parts)


class LLMFeedbackLearningService:
    """LLM-based feedback learning service that analyzes user feedback patterns."""

    def __init__(self, llm_client: AgentsClient | None = None) -> None:
        self._llm_client = llm_client

    async def summarize_feedback(self, feedback_list: list[dict[str, str]]) -> dict[str, Any]:
        """Analyze feedback patterns and generate a summary with improvement suggestions."""
        if not feedback_list:
            return {"summary": "", "feedback_count": 0, "patterns": [], "suggestions": []}

        # If no LLM, return basic summary
        if self._llm_client is None:
            return {
                "summary": f"Collected {len(feedback_list)} feedback items",
                "feedback_count": len(feedback_list),
                "patterns": [],
                "suggestions": [],
            }

        try:
            prompt = self._build_feedback_prompt(feedback_list)
            response = await self._llm_client.generate(
                prompt,
                response_format={"type": "json_object"},
            )
            content = response.get("content")
            if isinstance(content, str):
                import json

                try:
                    result = json.loads(content)
                    if isinstance(result, dict):
                        result["feedback_count"] = len(feedback_list)
                        return result
                except json.JSONDecodeError:
                    pass

            # Fallback if JSON parsing fails
            return {
                "summary": f"Analyzed {len(feedback_list)} feedback items",
                "feedback_count": len(feedback_list),
                "patterns": [],
                "suggestions": [],
            }
        except Exception as e:
            logger.warning("Failed to summarize feedback via LLM: %s", e)
            return {
                "summary": f"Collected {len(feedback_list)} feedback items",
                "feedback_count": len(feedback_list),
                "patterns": [],
                "suggestions": [],
            }

    def _build_feedback_prompt(self, feedback_list: list[dict[str, str]]) -> str:
        """Build a prompt for LLM to analyze feedback patterns."""
        feedback_text = "\n".join(
            [
                f"- Type: {f['feedback_type']}, Detail: {f.get('detail_text', 'N/A')}"
                for f in feedback_list
            ]
        )

        return f"""Analyze the following user feedback and provide insights.

Feedback Items:
{feedback_text}

Provide a JSON response with:
- summary: A brief summary of the feedback themes
- patterns: List of common patterns found in the feedback
- suggestions: List of actionable improvement suggestions

Keep response under 500 words."""


class StubFeedbackLearningService:
    async def summarize_feedback(self, feedback_list: list[dict[str, str]]) -> dict[str, Any]:
        return {"summary": "", "feedback_count": len(feedback_list)}


def create_review_service(session: AsyncSession) -> ReviewService:
    repository = ReviewRepository(session)
    embedding_service = OpenAIEmbeddingService()
    vector_backend = PgvectorBackend()

    # Create LLM client for explainer and feedback services
    settings = get_settings()
    llm_client = None
    if settings.llm_api_key:
        llm_client = AgentsClient()

    explainer_service = LLMExplainerService(llm_client=llm_client)
    feedback_learning_service = LLMFeedbackLearningService(llm_client=llm_client)

    return ReviewService(
        repository=repository,
        embedding_service=embedding_service,
        vector_backend=vector_backend,
        explainer_service=explainer_service,
        feedback_learning_service=feedback_learning_service,
    )
