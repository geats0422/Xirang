from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.feedback import get_current_user_id, get_review_service
from app.api.v1.feedback import router as feedback_router
from app.services.review.facade import ReviewService
from app.services.review.schemas import (
    FeedbackCreate,
    FeedbackRecord,
    MistakeRecord,
)


class FakeReviewRepositoryForAPI:
    def __init__(self) -> None:
        self.feedbacks: dict[UUID, dict] = {}
        self.mistakes: dict[UUID, dict] = {}
        self.rule_candidates: dict[UUID, dict] = {}

    async def create_feedback(self, *, user_id: UUID, feedback: FeedbackCreate) -> FeedbackRecord:
        fb_id = uuid4()
        now = datetime.now(UTC)
        self.feedbacks[fb_id] = {
            "id": fb_id,
            "user_id": user_id,
            "question_id": feedback.question_id,
            "document_id": feedback.document_id,
            "run_id": feedback.run_id,
            "feedback_type": feedback.feedback_type,
            "detail_text": feedback.detail_text,
            "status": "open",
            "created_at": now,
        }
        return FeedbackRecord(
            id=fb_id,
            user_id=user_id,
            question_id=feedback.question_id,
            document_id=feedback.document_id,
            run_id=feedback.run_id,
            feedback_type=feedback.feedback_type,
            detail_text=feedback.detail_text,
            status="open",
            created_at=now,
        )

    async def get_feedback(self, feedback_id: UUID) -> FeedbackRecord | None:
        fb = self.feedbacks.get(feedback_id)
        if not fb:
            return None
        return FeedbackRecord(**fb)

    async def list_feedback_by_user(
        self, user_id: UUID, *, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[FeedbackRecord]:
        results = []
        for fb in self.feedbacks.values():
            if fb["user_id"] != user_id:
                continue
            if status and fb["status"] != status:
                continue
            results.append(FeedbackRecord(**fb))
        return results[offset : offset + limit]

    async def update_feedback_status(self, feedback_id: UUID, status: str) -> None:
        fb = self.feedbacks.get(feedback_id)
        if fb:
            fb["status"] = status

    async def get_mistake(self, mistake_id: UUID) -> MistakeRecord | None:
        m = self.mistakes.get(mistake_id)
        if not m:
            return None
        return MistakeRecord(**m)

    async def list_mistakes_by_user(
        self, user_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> list[MistakeRecord]:
        results = []
        for m in self.mistakes.values():
            if m["user_id"] == user_id:
                results.append(MistakeRecord(**m))
        return results[offset : offset + limit]

    async def create_rule_candidate(
        self, *, source_job_id: UUID, rule_type: str, title: str, content: str
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
        self, *, status: str | None = None, limit: int = 50
    ) -> list[dict]:
        results = []
        for c in self.rule_candidates.values():
            if status and c["status"] != status:
                continue
            results.append(c)
        return results[:limit]


class FakeEmbeddingServiceForAPI:
    async def generate_embedding(self, text: str) -> list[float]:
        return [0.1] * 1536


class FakeVectorBackendForAPI:
    async def find_similar_mistakes(
        self, embedding: list[float], *, limit: int = 5, threshold: float = 0.8
    ) -> list[tuple[UUID, float]]:
        return []


class FakeExplainerServiceForAPI:
    async def explain_mistake(
        self,
        mistake: MistakeRecord,
        question: object,
        document_context: str | None,
        similar_mistakes: list[MistakeRecord] | None,
    ) -> str:
        return f"Explanation for mistake {mistake.id}"


class FakeFeedbackLearningServiceForAPI:
    async def summarize_feedback(self, feedback_list: list[dict]) -> dict:
        return {
            "summary": f"Analyzed {len(feedback_list)} feedback items",
            "suggestions": [
                {"type": "quality", "description": "Review question clarity"},
            ],
        }


def build_test_service() -> ReviewService:
    repo = FakeReviewRepositoryForAPI()
    return ReviewService(
        repository=repo,
        embedding_service=FakeEmbeddingServiceForAPI(),
        vector_backend=FakeVectorBackendForAPI(),
        explainer_service=FakeExplainerServiceForAPI(),
        feedback_learning_service=FakeFeedbackLearningServiceForAPI(),
    )


@pytest.fixture
def test_user_id() -> UUID:
    return uuid4()


@pytest.fixture
def test_service() -> ReviewService:
    return build_test_service()


@pytest.fixture
def app(test_service: ReviewService, test_user_id: UUID) -> FastAPI:
    app = FastAPI()
    app.include_router(feedback_router, prefix="/api/v1")

    async def override_user_id() -> UUID:
        return test_user_id

    async def override_service() -> ReviewService:
        return test_service

    app.dependency_overrides[get_current_user_id] = override_user_id
    app.dependency_overrides[get_review_service] = override_service
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestFeedbackAPI:
    def test_submit_feedback_returns_201(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/feedback",
            json={
                "question_id": str(uuid4()),
                "document_id": str(uuid4()),
                "run_id": str(uuid4()),
                "feedback_type": "question_incorrect",
                "detail_text": "The answer is wrong",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["feedback_type"] == "question_incorrect"
        assert data["status"] == "open"

    def test_submit_feedback_without_detail(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/feedback",
            json={
                "question_id": str(uuid4()),
                "document_id": str(uuid4()),
                "run_id": None,
                "feedback_type": "question_unclear",
                "detail_text": None,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["feedback_type"] == "question_unclear"

    def test_get_feedback_by_id(self, client: TestClient) -> None:
        create_response = client.post(
            "/api/v1/feedback",
            json={
                "question_id": str(uuid4()),
                "document_id": str(uuid4()),
                "run_id": None,
                "feedback_type": "question_incorrect",
                "detail_text": "Test",
            },
        )
        feedback_id = create_response.json()["id"]

        response = client.get(f"/api/v1/feedback/{feedback_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == feedback_id

    def test_get_feedback_not_found_returns_404(self, client: TestClient) -> None:
        response = client.get(f"/api/v1/feedback/{uuid4()}")
        assert response.status_code == 404

    def test_list_user_feedback(self, client: TestClient) -> None:
        client.post(
            "/api/v1/feedback",
            json={
                "question_id": str(uuid4()),
                "document_id": str(uuid4()),
                "run_id": None,
                "feedback_type": "question_incorrect",
                "detail_text": "First",
            },
        )
        client.post(
            "/api/v1/feedback",
            json={
                "question_id": str(uuid4()),
                "document_id": str(uuid4()),
                "run_id": None,
                "feedback_type": "question_unclear",
                "detail_text": "Second",
            },
        )

        response = client.get("/api/v1/feedback")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_summarize_feedback(self, client: TestClient, test_service: ReviewService) -> None:
        create1 = client.post(
            "/api/v1/feedback",
            json={
                "question_id": str(uuid4()),
                "document_id": str(uuid4()),
                "run_id": None,
                "feedback_type": "question_incorrect",
                "detail_text": "First",
            },
        )
        create2 = client.post(
            "/api/v1/feedback",
            json={
                "question_id": str(uuid4()),
                "document_id": str(uuid4()),
                "run_id": None,
                "feedback_type": "question_unclear",
                "detail_text": "Second",
            },
        )
        id1 = create1.json()["id"]
        id2 = create2.json()["id"]

        response = client.post(
            "/api/v1/feedback/summarize",
            json={"feedback_ids": [id1, id2]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "suggestions" in data
