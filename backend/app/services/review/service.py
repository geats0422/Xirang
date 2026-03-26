from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.review.embeddings import OpenAIEmbeddingService
from app.services.review.facade import ReviewService
from app.services.review.repository import ReviewRepository
from app.services.review.vector_backend import PgvectorBackend


class StubExplainerService:
    async def explain_mistake(
        self,
        mistake: Any,
        question: Any,
        document_context: Any,
        similar_mistakes: Any,
    ) -> str:
        return "Explanation not available."


class StubFeedbackLearningService:
    async def summarize_feedback(self, feedback_list: list[dict[str, str]]) -> dict[str, Any]:
        return {"summary": "", "feedback_count": len(feedback_list)}


def create_review_service(session: AsyncSession) -> ReviewService:
    repository = ReviewRepository(session)
    embedding_service = OpenAIEmbeddingService()
    vector_backend = PgvectorBackend()
    explainer_service = StubExplainerService()
    feedback_learning_service = StubFeedbackLearningService()

    return ReviewService(
        repository=repository,
        embedding_service=embedding_service,
        vector_backend=vector_backend,
        explainer_service=explainer_service,
        feedback_learning_service=feedback_learning_service,
    )
