from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from uuid import UUID

    from app.services.review.schemas import FeedbackCreate, FeedbackRecord, MistakeRecord


class ReviewRepositoryProtocol(Protocol):
    async def create_feedback(
        self,
        *,
        user_id: UUID,
        feedback: FeedbackCreate,
    ) -> FeedbackRecord: ...

    async def get_feedback(self, feedback_id: UUID) -> FeedbackRecord | None: ...

    async def list_feedback_by_user(
        self,
        user_id: UUID,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FeedbackRecord]: ...

    async def create_mistake(
        self,
        *,
        user_id: UUID,
        question_id: UUID,
        document_id: UUID,
        run_id: UUID,
        explanation: str | None = None,
    ) -> MistakeRecord: ...

    async def get_mistake(self, mistake_id: UUID) -> MistakeRecord | None: ...

    async def list_mistakes_by_user(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MistakeRecord]: ...

    async def update_feedback_status(self, feedback_id: UUID, status: str) -> None: ...

    async def create_rule_candidate(
        self,
        *,
        source_job_id: UUID,
        rule_type: str,
        title: str,
        content: str,
    ) -> dict[str, str]: ...

    async def list_rule_candidates(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, str]]: ...


class EmbeddingServiceProtocol(Protocol):
    async def generate_embedding(self, text: str) -> list[float]: ...


class VectorBackendProtocol(Protocol):
    async def find_similar_mistakes(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
        threshold: float = 0.8,
    ) -> list[tuple[UUID, float]]: ...

    async def store(self, mistake_id: UUID, embedding: list[float]) -> None: ...


class ExplainerServiceProtocol(Protocol):
    async def explain_mistake(
        self,
        mistake: MistakeRecord,
        question: Any,
        document_context: str | None,
        similar_mistakes: list[MistakeRecord] | None,
    ) -> str: ...


class FeedbackLearningServiceProtocol(Protocol):
    async def summarize_feedback(
        self,
        feedback_list: list[dict[str, str]],
    ) -> dict[str, Any]: ...


class ReviewServiceError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class MistakeNotFoundError(ReviewServiceError):
    status_code = 404


class FeedbackNotFoundError(ReviewServiceError):
    status_code = 404


@dataclass(slots=True)
class ReviewService:
    repository: ReviewRepositoryProtocol
    embedding_service: EmbeddingServiceProtocol
    vector_backend: VectorBackendProtocol
    explainer_service: ExplainerServiceProtocol
    feedback_learning_service: FeedbackLearningServiceProtocol

    @property
    def _repository(self) -> ReviewRepositoryProtocol:
        return self.repository

    async def submit_feedback(self, *, user_id: UUID, feedback: FeedbackCreate) -> FeedbackRecord:
        return await self.repository.create_feedback(user_id=user_id, feedback=feedback)

    async def get_feedback(self, feedback_id: UUID) -> FeedbackRecord | None:
        return await self.repository.get_feedback(feedback_id)

    async def list_user_feedback(
        self,
        user_id: UUID,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FeedbackRecord]:
        return await self.repository.list_feedback_by_user(
            user_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def create_mistake(
        self,
        *,
        user_id: UUID,
        question_id: UUID,
        document_id: UUID,
        run_id: UUID,
        explanation: str | None = None,
    ) -> MistakeRecord:
        return await self.repository.create_mistake(
            user_id=user_id,
            question_id=question_id,
            document_id=document_id,
            run_id=run_id,
            explanation=explanation,
        )

    async def get_mistake(self, mistake_id: UUID) -> MistakeRecord | None:
        return await self.repository.get_mistake(mistake_id)

    async def list_mistakes_by_user(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MistakeRecord]:
        return await self.repository.list_mistakes_by_user(user_id, limit=limit, offset=offset)

    async def create_rule_candidate(
        self,
        *,
        source_job_id: UUID,
        rule_type: str,
        title: str,
        content: str,
    ) -> dict[str, str]:
        return await self.repository.create_rule_candidate(
            source_job_id=source_job_id,
            rule_type=rule_type,
            title=title,
            content=content,
        )

    async def list_rule_candidates(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, str]]:
        return await self.repository.list_rule_candidates(status=status, limit=limit)

    async def explain_mistake(
        self,
        *,
        mistake_id: UUID,
        question_text: str,
        document_context: str | None = None,
    ) -> str:
        mistake = await self.repository.get_mistake(mistake_id)
        if not mistake:
            raise MistakeNotFoundError(f"Mistake not found: {mistake_id}")

        embedding = await self.embedding_service.generate_embedding(question_text)
        similar_ids = await self.vector_backend.find_similar_mistakes(
            embedding,
            limit=5,
            threshold=0.7,
        )
        similar_mistakes: list[MistakeRecord] = []
        for similar_id, _ in similar_ids:
            similar = await self.repository.get_mistake(similar_id)
            if similar:
                similar_mistakes.append(similar)

        explanation = await self.explainer_service.explain_mistake(
            mistake=mistake,
            question=question_text,
            document_context=document_context,
            similar_mistakes=similar_mistakes if similar_mistakes else None,
        )
        await self.vector_backend.store(mistake_id, embedding)
        return explanation

    async def summarize_feedback(self, feedback_ids: list[UUID]) -> dict[str, Any]:
        feedback_list: list[dict[str, str]] = []
        for feedback_id in feedback_ids:
            feedback = await self.repository.get_feedback(feedback_id)
            if feedback:
                feedback_list.append(
                    {
                        "id": str(feedback.id),
                        "feedback_type": feedback.feedback_type,
                        "detail_text": feedback.detail_text or "",
                        "status": feedback.status,
                    }
                )
        result = await self.feedback_learning_service.summarize_feedback(feedback_list)
        for feedback_id in feedback_ids:
            await self.repository.update_feedback_status(feedback_id, "summarized")
        return result
