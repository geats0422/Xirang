from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.v1 import runs as runs_router
from app.db.models.documents import DocumentStatus, QuestionSetStatus
from app.main import create_app
from app.services.learning_paths.service import (
    PathGenerationFailedError,
    PathGenerationInProgressError,
    RegenerationLimitExceededError,
)


class FakeDocument:
    def __init__(self, *, owner_user_id: UUID, ingest_status: DocumentStatus) -> None:
        self.id = uuid4()
        self.owner_user_id = owner_user_id
        self.ingest_status = ingest_status


class FakeQuestionSet:
    def __init__(self, *, status: QuestionSetStatus, question_count: int) -> None:
        self.status = status
        self.question_count = question_count


class FakeDocumentRepository:
    def __init__(
        self,
        *,
        owner_user_id: UUID,
        ingest_status: DocumentStatus = DocumentStatus.READY,
        question_set_status: QuestionSetStatus = QuestionSetStatus.READY,
        question_count: int = 10,
    ) -> None:
        self._owner_user_id = owner_user_id
        self._ingest_status = ingest_status
        self._question_set_status = question_set_status
        self._question_count = question_count

    async def get_document_by_id(self, document_id: UUID) -> FakeDocument | None:
        return FakeDocument(owner_user_id=self._owner_user_id, ingest_status=self._ingest_status)

    async def get_question_set_for_document(self, document_id: UUID) -> FakeQuestionSet | None:
        return FakeQuestionSet(status=self._question_set_status, question_count=self._question_count)


class FakeLearningPathService:
    def __init__(self) -> None:
        self.path_options_payload: dict[str, object] = {
            "generation_status": "ready",
            "mode": "endless",
            "path_version_id": str(uuid4()),
            "version_no": 1,
            "options": [],
        }
        self.raise_on_get: Exception | None = None
        self.raise_on_regenerate: Exception | None = None

    async def get_path_options(self, *, document_id: UUID, mode: str) -> dict[str, object]:
        if self.raise_on_get is not None:
            raise self.raise_on_get
        return self.path_options_payload

    async def regenerate_path(self, *, document_id: UUID, mode: str, user_id: UUID) -> dict[str, object]:
        if self.raise_on_regenerate is not None:
            raise self.raise_on_regenerate
        return {
            "generation_status": "generating",
            "mode": mode,
            "path_version_id": str(uuid4()),
            "next_version_no": 2,
            "job_id": None,
        }


def create_test_client(
    user_id: UUID,
    fake_service: FakeLearningPathService,
    *,
    fake_document_repository: FakeDocumentRepository | None = None,
) -> TestClient:
    app = create_app()
    document_repository = fake_document_repository or FakeDocumentRepository(owner_user_id=user_id)
    app.dependency_overrides[runs_router.get_current_user_id] = lambda: user_id
    app.dependency_overrides[runs_router.get_learning_path_service] = lambda: fake_service
    app.dependency_overrides[runs_router.get_document_repository] = lambda: document_repository
    return TestClient(app)


class TestLearningPathApi:
    def test_path_options_returns_accepted_when_generating(self) -> None:
        user_id = uuid4()
        fake_service = FakeLearningPathService()
        fake_service.path_options_payload = {
            "generation_status": "generating",
            "mode": "endless",
            "path_version_id": str(uuid4()),
            "version_no": 3,
            "job_id": None,
            "options": [],
        }
        client = create_test_client(user_id, fake_service)

        response = client.get(f"/api/v1/runs/path-options?mode=endless&document_id={uuid4()}")

        assert response.status_code == 202
        assert response.json()["generation_status"] == "generating"

    def test_path_options_returns_conflict_when_generation_failed(self) -> None:
        user_id = uuid4()
        fake_service = FakeLearningPathService()
        fake_service.raise_on_get = PathGenerationFailedError("Path generation failed")
        client = create_test_client(user_id, fake_service)

        response = client.get(f"/api/v1/runs/path-options?mode=endless&document_id={uuid4()}")

        assert response.status_code == 409
        assert response.json()["detail"] == "Path generation failed"

    def test_path_options_rejects_when_document_not_ready(self) -> None:
        user_id = uuid4()
        fake_service = FakeLearningPathService()
        client = create_test_client(
            user_id,
            fake_service,
            fake_document_repository=FakeDocumentRepository(
                owner_user_id=user_id,
                ingest_status=DocumentStatus.PROCESSING,
            ),
        )

        response = client.get(f"/api/v1/runs/path-options?mode=endless&document_id={uuid4()}")

        assert response.status_code == 409
        assert response.json()["detail"] == "document_not_ready"

    def test_path_regeneration_conflict_when_in_progress(self) -> None:
        user_id = uuid4()
        fake_service = FakeLearningPathService()
        fake_service.raise_on_regenerate = PathGenerationInProgressError("Path generation already in progress")
        client = create_test_client(user_id, fake_service)

        response = client.post(
            "/api/v1/runs/path-regenerations",
            json={"document_id": str(uuid4()), "mode": "endless"},
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Path generation already in progress"

    def test_path_regeneration_rate_limit(self) -> None:
        user_id = uuid4()
        fake_service = FakeLearningPathService()
        fake_service.raise_on_regenerate = RegenerationLimitExceededError("Path regeneration limit reached")
        client = create_test_client(user_id, fake_service)

        response = client.post(
            "/api/v1/runs/path-regenerations",
            json={"document_id": str(uuid4()), "mode": "endless"},
        )

        assert response.status_code == 429
        assert response.json()["detail"] == "Path regeneration limit reached"
