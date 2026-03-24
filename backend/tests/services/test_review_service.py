from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.services.review.facade import ReviewService
from app.services.review.schemas import (
    FeedbackCreate,
    FeedbackRecord,
    MistakeRecord,
)


@dataclass
class FakeFeedback:
    id: UUID
    user_id: UUID
    question_id: UUID
    document_id: UUID
    run_id: UUID | None
    feedback_type: str
    detail_text: str | None
    status: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeMistake:
    id: UUID
    user_id: UUID
    question_id: UUID
    document_id: UUID
    run_id: UUID
    explanation: str | None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeEmbeddingService:
    async def generate_embedding(self, text: str) -> list[float]:
        return [0.1] * 1536

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 1536 for _ in texts]

    async def store_mistake_embedding(
        self,
        mistake_id: UUID,
        embedding: list[float],
        model_name: str,
    ) -> None:
        pass

    async def get_mistake_embedding(self, mistake_id: UUID) -> list[float] | None:
        return None

    async def find_similar_mistakes(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
        threshold: float = 0.0,
    ) -> list[tuple[UUID, float]]:
        return []


@dataclass
class FakeVectorBackend:
    _mistakes: dict[UUID, list[float]] = field(default_factory=dict)

    async def find_similar_mistakes(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
        threshold: float = 0.8,
    ) -> list[tuple[UUID, float]]:
        results = []
        for mid, emb in self._mistakes.items():
            dot = sum(a * b for a, b in zip(embedding, emb, strict=False))
            norm_a = sum(a**2 for a in embedding) ** 0.5
            norm_b = sum(b**2 for b in emb) ** 0.5
            similarity = dot / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0
            if similarity >= threshold:
                results.append((mid, similarity))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def store(self, mistake_id: UUID, embedding: list[float]) -> None:
        self._mistakes[mistake_id] = embedding


@dataclass
class FakeExplainerService:
    async def explain_mistake(
        self,
        mistake: MistakeRecord,
        question: Any,
        document_context: str | None,
        similar_mistakes: list[MistakeRecord] | None,
    ) -> str:
        base = f"This is an explanation for mistake {mistake.id}. "
        if document_context:
            base += f" Context: {document_context[:100]}..."
        if similar_mistakes:
            base += f" Similar mistakes: {len(similar_mistakes)}."
        return base


@dataclass
class FakeFeedbackLearningService:
    _summaries: list[dict] = field(default_factory=list)

    async def summarize_feedback(
        self,
        feedback_list: list[dict],
    ) -> dict:
        summary = f"Found {len(feedback_list)} feedback items. "
        suggestions = [
            {"type": "quality_improvement", "description": "Review questions for clarity"},
            {"type": "content_update", "description": "Update incorrect answers"},
        ]
        self._summaries.append({"summary": summary, "suggestions": suggestions})
        return {"summary": summary, "suggestions": suggestions}


@dataclass
class FakeReviewRepository:
    feedbacks: dict[UUID, FakeFeedback] = field(default_factory=dict)
    mistakes: dict[UUID, FakeMistake] = field(default_factory=dict)
    embeddings: dict[UUID, list[float]] = field(default_factory=dict)
    rule_candidates: dict[UUID, dict] = field(default_factory=dict)

    async def create_feedback(
        self,
        *,
        user_id: UUID,
        feedback: FeedbackCreate,
    ) -> FeedbackRecord:
        fb = FakeFeedback(
            id=uuid4(),
            user_id=user_id,
            question_id=feedback.question_id,
            document_id=feedback.document_id,
            run_id=feedback.run_id,
            feedback_type=feedback.feedback_type,
            detail_text=feedback.detail_text,
            status="open",
        )
        self.feedbacks[fb.id] = fb
        return FeedbackRecord(
            id=fb.id,
            user_id=fb.user_id,
            question_id=fb.question_id,
            document_id=fb.document_id,
            run_id=fb.run_id,
            feedback_type=fb.feedback_type,
            detail_text=fb.detail_text,
            status=fb.status,
            created_at=fb.created_at,
        )

    async def get_feedback(self, feedback_id: UUID) -> FeedbackRecord | None:
        fb = self.feedbacks.get(feedback_id)
        if not fb:
            return None
        return FeedbackRecord(
            id=fb.id,
            user_id=fb.user_id,
            question_id=fb.question_id,
            document_id=fb.document_id,
            run_id=fb.run_id,
            feedback_type=fb.feedback_type,
            detail_text=fb.detail_text,
            status=fb.status,
            created_at=fb.created_at,
        )

    async def list_feedback_by_user(
        self,
        user_id: UUID,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FeedbackRecord]:
        results = []
        for fb in self.feedbacks.values():
            if fb.user_id != user_id:
                continue
            if status and fb.status != status:
                continue
            results.append(
                FeedbackRecord(
                    id=fb.id,
                    user_id=fb.user_id,
                    question_id=fb.question_id,
                    document_id=fb.document_id,
                    run_id=fb.run_id,
                    feedback_type=fb.feedback_type,
                    detail_text=fb.detail_text,
                    status=fb.status,
                    created_at=fb.created_at,
                )
            )
        return results[offset : offset + limit]

    async def create_mistake(
        self,
        *,
        user_id: UUID,
        question_id: UUID,
        document_id: UUID,
        run_id: UUID,
        explanation: str | None = None,
    ) -> MistakeRecord:
        mistake = FakeMistake(
            id=uuid4(),
            user_id=user_id,
            question_id=question_id,
            document_id=document_id,
            run_id=run_id,
            explanation=explanation,
        )
        self.mistakes[mistake.id] = mistake
        return MistakeRecord(
            id=mistake.id,
            user_id=mistake.user_id,
            question_id=mistake.question_id,
            document_id=mistake.document_id,
            run_id=mistake.run_id,
            explanation=mistake.explanation,
            created_at=mistake.created_at,
        )

    async def get_mistake(self, mistake_id: UUID) -> MistakeRecord | None:
        m = self.mistakes.get(mistake_id)
        if not m:
            return None
        return MistakeRecord(
            id=m.id,
            user_id=m.user_id,
            question_id=m.question_id,
            document_id=m.document_id,
            run_id=m.run_id,
            explanation=m.explanation,
            created_at=m.created_at,
        )

    async def list_mistakes_by_user(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MistakeRecord]:
        results = []
        for m in self.mistakes.values():
            if m.user_id == user_id:
                results.append(
                    MistakeRecord(
                        id=m.id,
                        user_id=m.user_id,
                        question_id=m.question_id,
                        document_id=m.document_id,
                        run_id=m.run_id,
                        explanation=m.explanation,
                        created_at=m.created_at,
                    )
                )
        return results[offset : offset + limit]

    async def store_mistake_embedding(
        self,
        mistake_id: UUID,
        embedding: list[float],
        model_name: str,
    ) -> None:
        self.embeddings[mistake_id] = embedding

    async def get_mistake_embedding(self, mistake_id: UUID) -> list[float] | None:
        return self.embeddings.get(mistake_id)

    async def find_similar_mistakes(
        self,
        embedding: list[float],
        *,
        limit: int = 5,
        threshold: float = 0.0,
    ) -> list[tuple[UUID, float]]:
        results = []
        for mid, emb in self.embeddings.items():
            similarity = sum(a * b for a, b in zip(embedding, emb, strict=False)) / (
                (sum(a**1 for a in embedding) ** 1) * (sum(b**2 for b in emb) ** 1)
            )
            if similarity >= threshold:
                results.append((mid, similarity))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def create_rule_candidate(
        self,
        *,
        source_job_id: UUID,
        rule_type: str,
        title: str,
        content: str,
    ) -> dict:
        candidate_id = uuid4()
        candidate = {
            "id": str(candidate_id),
            "source_job_id": str(source_job_id),
            "rule_type": rule_type,
            "title": title,
            "content": content,
            "status": "pending_review",
        }
        self.rule_candidates[candidate_id] = candidate
        return candidate

    async def list_rule_candidates(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        results = []
        for c in self.rule_candidates.values():
            if status and c["status"] != status:
                continue
            results.append(c)
        return results[:limit]

    async def update_feedback_status(
        self,
        feedback_id: UUID,
        status: str,
    ) -> None:
        fb = self.feedbacks.get(feedback_id)
        if fb:
            fb.status = status


def build_review_service() -> ReviewService:
    repo = FakeReviewRepository()
    embedding = FakeEmbeddingService()
    vector_backend = FakeVectorBackend()
    explainer = FakeExplainerService()
    learning = FakeFeedbackLearningService()
    return ReviewService(
        repository=repo,
        embedding_service=embedding,
        vector_backend=vector_backend,
        explainer_service=explainer,
        feedback_learning_service=learning,
    )


class TestReviewService:
    @pytest.mark.asyncio
    async def test_submit_feedback_creates_record(self) -> None:
        service = build_review_service()
        user_id = uuid4()
        feedback = FeedbackCreate(
            question_id=uuid4(),
            document_id=uuid4(),
            run_id=uuid4(),
            feedback_type="question_incorrect",
            detail_text="The answer is wrong",
        )
        result = await service.submit_feedback(user_id=user_id, feedback=feedback)
        assert result.id is not None
        assert result.user_id == user_id
        assert result.feedback_type == "question_incorrect"
        assert result.status == "open"

    @pytest.mark.asyncio
    async def test_list_user_feedback_filters_by_user(self) -> None:
        service = build_review_service()
        user_id = uuid4()
        other_user_id = uuid4()
        await service.submit_feedback(
            user_id=user_id,
            feedback=FeedbackCreate(
                question_id=uuid4(),
                document_id=uuid4(),
                run_id=uuid4(),
                feedback_type="question_incorrect",
                detail_text=None,
            ),
        )
        await service.submit_feedback(
            user_id=other_user_id,
            feedback=FeedbackCreate(
                question_id=uuid4(),
                document_id=uuid4(),
                run_id=None,
                feedback_type="question_unclear",
                detail_text="Confusing",
            ),
        )
        results = await service.list_user_feedback(user_id)
        assert len(results) == 1
        assert results[0].user_id == user_id

    @pytest.mark.asyncio
    async def test_create_mistake_creates_record(self) -> None:
        service = build_review_service()
        user_id = uuid4()
        mistake = await service.create_mistake(
            user_id=user_id,
            question_id=uuid4(),
            document_id=uuid4(),
            run_id=uuid4(),
        )
        assert mistake.id is not None
        assert mistake.user_id == user_id

    @pytest.mark.asyncio
    async def test_explain_mistake_returns_explanation(self) -> None:
        service = build_review_service()
        user_id = uuid4()
        mistake = await service.create_mistake(
            user_id=user_id,
            question_id=uuid4(),
            document_id=uuid4(),
            run_id=uuid4(),
        )
        explanation = await service.explain_mistake(
            mistake_id=mistake.id,
            question_text="What is 2 + 2?",
            document_context="Chapter 1: Basic Math",
        )
        assert explanation is not None
        assert "explanation" in explanation.lower()

    @pytest.mark.asyncio
    async def test_summarize_feedback_returns_summary(self) -> None:
        service = build_review_service()
        user_id = uuid4()
        fb1 = await service.submit_feedback(
            user_id=user_id,
            feedback=FeedbackCreate(
                question_id=uuid4(),
                document_id=uuid4(),
                run_id=uuid4(),
                feedback_type="question_incorrect",
                detail_text="Wrong answer",
            ),
        )
        fb2 = await service.submit_feedback(
            user_id=user_id,
            feedback=FeedbackCreate(
                question_id=uuid4(),
                document_id=uuid4(),
                run_id=uuid4(),
                feedback_type="question_unclear",
                detail_text="Too confusing",
            ),
        )
        result = await service.summarize_feedback([fb1.id, fb2.id])
        assert "summary" in result
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_summarize_feedback_updates_status(self) -> None:
        service = build_review_service()
        user_id = uuid4()
        fb = await service.submit_feedback(
            user_id=user_id,
            feedback=FeedbackCreate(
                question_id=uuid4(),
                document_id=uuid4(),
                run_id=uuid4(),
                feedback_type="question_incorrect",
                detail_text=None,
            ),
        )
        assert fb.status == "open"
        await service.summarize_feedback([fb.id])
        updated = await service.get_feedback(fb.id)
        assert updated is not None
        assert updated.status == "summarized"

    @pytest.mark.asyncio
    async def test_get_feedback_returns_none_for_nonexistent(self) -> None:
        service = build_review_service()
        result = await service.get_feedback(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_mistake_returns_none_for_nonexistent(self) -> None:
        service = build_review_service()
        repo = service._repository
        result = await repo.get_mistake(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_mistakes_by_user_filters_by_user(self) -> None:
        service = build_review_service()
        user_id = uuid4()
        other_user_id = uuid4()
        await service.create_mistake(
            user_id=user_id,
            question_id=uuid4(),
            document_id=uuid4(),
            run_id=uuid4(),
        )
        await service.create_mistake(
            user_id=other_user_id,
            question_id=uuid4(),
            document_id=uuid4(),
            run_id=uuid4(),
        )
        repo = service._repository
        results = await repo.list_mistakes_by_user(user_id)
        assert len(results) == 1
        assert results[0].user_id == user_id
