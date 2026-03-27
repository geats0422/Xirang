from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.v1 import documents as documents_router
from app.api.v1 import runs as runs_router
from app.db.models.documents import DocumentStatus, JobStatus, QuestionSetStatus
from app.db.models.runs import RunMode, RunStatus
from app.main import create_app
from app.services.runs.schemas import QuestionData


@dataclass
class FakeDocument:
    id: UUID
    owner_user_id: UUID
    title: str
    ingest_status: DocumentStatus


@dataclass
class FakeQuestionSet:
    status: QuestionSetStatus
    question_count: int


@dataclass
class FakeRun:
    id: UUID
    user_id: UUID
    document_id: UUID
    mode: RunMode
    status: RunStatus
    total_questions: int
    answered_questions: int
    correct_answers: int
    score: int
    mode_state: dict[str, object]


class FlowStore:
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        self.documents: dict[UUID, FakeDocument] = {}
        self.question_sets: dict[UUID, FakeQuestionSet] = {}


class FakeDocumentService:
    def __init__(self, store: FlowStore) -> None:
        self._store = store

    async def upload(self, **kwargs: object) -> SimpleNamespace:
        document_id = uuid4()
        title = str(kwargs.get("title") or "markdown.md")
        document = FakeDocument(
            id=document_id,
            owner_user_id=self._store.user_id,
            title=title,
            ingest_status=DocumentStatus.PROCESSING,
        )
        self._store.documents[document_id] = document
        self._store.question_sets[document_id] = FakeQuestionSet(
            status=QuestionSetStatus.GENERATING,
            question_count=0,
        )
        job = SimpleNamespace(id=uuid4(), status=JobStatus.PROCESSING)
        return SimpleNamespace(document=document, job=job)


class FakeDocumentRepository:
    def __init__(self, store: FlowStore) -> None:
        self._store = store

    async def get_document_by_id(self, document_id: UUID) -> FakeDocument | None:
        return self._store.documents.get(document_id)

    async def get_question_set_for_document(self, document_id: UUID) -> FakeQuestionSet | None:
        return self._store.question_sets.get(document_id)


class FakeLearningPathService:
    async def get_path_options(self, *, document_id: UUID, mode: str) -> dict[str, object]:
        return {
            "generation_status": "ready",
            "mode": mode,
            "path_version_id": str(uuid4()),
            "version_no": 1,
            "options": [
                {
                    "path_id": "F1",
                    "label": "F1",
                    "kind": "floor",
                    "description": "Warm-up",
                    "goal_total": 10,
                    "path_version_id": str(uuid4()),
                    "level_node_id": str(uuid4()),
                }
            ],
        }


class FakeRunService:
    async def create_run(
        self,
        *,
        user_id: UUID,
        document_id: UUID,
        mode: RunMode,
        question_count: int,
        path_id: str | None = None,
        path_version_id: UUID | None = None,
        level_node_id: UUID | None = None,
        is_legend_review: bool = False,
    ) -> tuple[FakeRun, list[QuestionData]]:
        run = FakeRun(
            id=uuid4(),
            user_id=user_id,
            document_id=document_id,
            mode=mode,
            status=RunStatus.RUNNING,
            total_questions=question_count,
            answered_questions=0,
            correct_answers=0,
            score=0,
            mode_state={},
        )
        option_a = uuid4()
        option_b = uuid4()
        questions = [
            QuestionData(
                id=uuid4(),
                document_id=document_id,
                question_text="Markdown question",
                question_type="single_choice",
                options=[
                    {"id": str(option_a), "text": "A"},
                    {"id": str(option_b), "text": "B"},
                ],
                correct_option_ids=[option_a],
                difficulty=1,
            )
        ]
        return run, questions


def create_test_client(user_id: UUID, store: FlowStore) -> TestClient:
    app = create_app()
    fake_document_service = FakeDocumentService(store)
    fake_document_repository = FakeDocumentRepository(store)
    fake_learning_path_service = FakeLearningPathService()
    fake_run_service = FakeRunService()

    app.dependency_overrides[documents_router.get_current_user_id] = lambda: user_id
    app.dependency_overrides[documents_router.get_document_service] = lambda: fake_document_service

    app.dependency_overrides[runs_router.get_current_user_id] = lambda: user_id
    app.dependency_overrides[runs_router.get_document_repository] = lambda: fake_document_repository
    app.dependency_overrides[runs_router.get_learning_path_service] = lambda: fake_learning_path_service
    app.dependency_overrides[runs_router.get_run_service] = lambda: fake_run_service
    return TestClient(app)


class TestMarkdownFlowApi:
    def test_markdown_upload_path_options_and_run_flow(self) -> None:
        user_id = uuid4()
        store = FlowStore(user_id)
        client = create_test_client(user_id, store)

        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("notes.md", b"# markdown", "text/markdown")},
            data={"title": "notes.md", "format": "md"},
        )
        assert upload_response.status_code == 201
        document_id = UUID(upload_response.json()["document"]["id"])
        assert upload_response.json()["document"]["ingest_status"] == "processing"

        pending_path_response = client.get(
            f"/api/v1/runs/path-options?mode=endless&document_id={document_id}"
        )
        assert pending_path_response.status_code == 409
        assert pending_path_response.json()["detail"] == "document_not_ready"

        store.documents[document_id].ingest_status = DocumentStatus.READY
        store.question_sets[document_id] = FakeQuestionSet(
            status=QuestionSetStatus.READY,
            question_count=12,
        )

        path_response = client.get(f"/api/v1/runs/path-options?mode=endless&document_id={document_id}")
        assert path_response.status_code == 200
        path_payload = path_response.json()
        assert path_payload["generation_status"] == "ready"
        option = path_payload["options"][0]

        create_run_response = client.post(
            "/api/v1/runs",
            json={
                "document_id": str(document_id),
                "mode": "endless",
                "question_count": 5,
                "path_id": option["path_id"],
                "path_version_id": option["path_version_id"],
                "level_node_id": option["level_node_id"],
            },
        )
        assert create_run_response.status_code == 201
        run_payload = create_run_response.json()
        assert run_payload["run_id"]
        assert run_payload["questions"][0]["text"] == "Markdown question"
