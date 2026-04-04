from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import pytest

import app.workers.main as worker_main
from app.db.models.documents import (
    DocumentFormat,
    DocumentStatus,
    JobStatus,
    QuestionSetStatus,
    TreeStatus,
)
from app.workers.main import _process_document_ingestion

if TYPE_CHECKING:
    from app.db.models.questions import QuestionType


@dataclass
class FakeDocument:
    id: UUID
    owner_user_id: UUID
    storage_path: str
    ingest_status: DocumentStatus
    format: DocumentFormat
    file_name: str


@dataclass
class FakeQuestionSet:
    id: UUID
    status: QuestionSetStatus


@dataclass
class FakeJob:
    id: UUID
    payload: dict[str, object]


class FakeStorage:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    async def delete(self, storage_key: str) -> None:
        target = self.root_dir / storage_key
        if target.exists():
            target.unlink()


class FakeIndexBackend:
    async def index_document(self, *, document_id: str, content: str) -> Any:
        class Result:
            def __init__(self, document_id: str) -> None:
                self.document_id = f"tree:{document_id}"
                self.status = "indexed"

        return Result(document_id)

    async def ask(self, *, document_id: str, question: str, context_chunks: int = 3) -> Any:
        _ = document_id
        _ = question
        _ = context_chunks

        class Result:
            def __init__(self) -> None:
                self.answer = (
                    "This is enriched study context with enough detail to be used for question "
                    "generation in tests."
                )

        return Result()


class FailingIndexBackend:
    async def index_document(self, *, document_id: str, content: str) -> Any:
        raise RuntimeError("index backend unavailable")

    async def ask(self, *, document_id: str, question: str, context_chunks: int = 3) -> Any:
        _ = document_id
        _ = question
        _ = context_chunks
        raise RuntimeError("index backend unavailable")


class FakeLLMClient:
    async def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = prompt
        _ = kwargs
        return {
            "structured_output": {
                "questions": [
                    {
                        "question_type": "fill_in_blank",
                        "prompt": "Document line ____.",
                        "options": [],
                        "correct_answer": "one",
                        "hints": ["3 letters"],
                        "explanation": "From source text",
                        "difficulty": 1,
                    },
                    {
                        "question_type": "single_choice",
                        "prompt": "What is the key topic?",
                        "options": [
                            {"option_key": "A", "content": "Topic A", "is_correct": True},
                            {"option_key": "B", "content": "Topic B", "is_correct": False},
                        ],
                        "explanation": "From source text",
                        "source_locator": "p1",
                        "difficulty": 1,
                        "metadata": {"source": "test"},
                    },
                ]
            }
        }


class FakeSession:
    async def execute(self, stmt: Any) -> Any:
        _ = stmt

        class Result:
            def one_or_none(self) -> tuple[None, str]:
                return (None, "en")

        return Result()


class FakeMinerUClient:
    async def parse_to_markdown(
        self,
        *,
        file_name: str,
        file_bytes: bytes,
        backend: str | None = None,
        lang_list: tuple[str, ...] | None = None,
    ) -> str:
        _ = file_name
        _ = file_bytes
        _ = backend
        _ = lang_list
        return "# Parsed\n\nMinerU markdown content"


class FakeRepository:
    def __init__(self, document: FakeDocument) -> None:
        self.document = document
        self.question_set: FakeQuestionSet | None = None
        self.question_count = 0
        self.tree_status: TreeStatus | None = None
        self.ingestion_job_status: JobStatus | None = None
        self.ingestion_error: str | None = None
        self.created_jobs: list[dict[str, object]] = []
        self.commits = 0

    async def get_document_by_id(self, document_id: UUID) -> FakeDocument | None:
        if self.document.id == document_id:
            return self.document
        return None

    async def update_document_status(
        self,
        *,
        document_id: UUID,
        ingest_status: DocumentStatus,
        page_count: int | None = None,
        word_count: int | None = None,
    ) -> None:
        self.document.ingest_status = ingest_status

    async def upsert_pageindex_tree(
        self,
        *,
        document_id: UUID,
        tree_key: str,
        status: TreeStatus,
        node_count: int | None,
    ) -> None:
        self.tree_status = status

    async def get_question_set_for_document(self, document_id: UUID) -> FakeQuestionSet | None:
        return self.question_set

    async def create_question_set(
        self,
        *,
        document_id: UUID,
        generation_version: int,
    ) -> FakeQuestionSet:
        self.question_set = FakeQuestionSet(id=uuid4(), status=QuestionSetStatus.GENERATING)
        return self.question_set

    async def update_question_set_status(
        self,
        *,
        question_set_id: UUID,
        status: QuestionSetStatus,
        question_count: int | None = None,
    ) -> None:
        if self.question_set is not None:
            self.question_set.status = status
        if question_count is not None:
            self.question_count = question_count

    async def clear_questions_for_set(self, question_set_id: UUID) -> None:
        self.question_count = 0

    async def create_question(
        self,
        *,
        question_set_id: UUID,
        document_id: UUID,
        question_type: QuestionType,
        prompt: str,
        explanation: str | None,
        source_locator: dict[str, object] | None,
        difficulty: int,
        metadata: dict[str, object],
    ) -> Any:
        class FakeQuestion:
            def __init__(self) -> None:
                self.id = uuid4()

        self.question_count += 1
        return FakeQuestion()

    async def create_question_option(
        self,
        *,
        question_id: UUID,
        option_key: str,
        content: str,
        is_correct: bool,
        sort_order: int,
    ) -> None:
        return

    async def mark_ingestion_job_completed(
        self,
        *,
        job_id: UUID,
        page_count: int,
        word_count: int,
    ) -> None:
        self.ingestion_job_status = JobStatus.COMPLETED

    async def mark_ingestion_job_failed(
        self,
        *,
        job_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        self.ingestion_job_status = JobStatus.FAILED
        self.ingestion_error = error_message

    async def create_job(
        self,
        *,
        job_type: str,
        queue_name: str,
        payload: dict[str, object],
        max_attempts: int = 3,
        available_at: datetime | None = None,
    ) -> Any:
        self.created_jobs.append(
            {
                "job_type": job_type,
                "queue_name": queue_name,
                "payload": payload,
                "max_attempts": max_attempts,
                "available_at": available_at,
            }
        )

        class FakeCreatedJob:
            def __init__(self) -> None:
                self.id = uuid4()

        return FakeCreatedJob()

    async def delete_document_by_id(self, document_id: UUID) -> None:
        _ = document_id

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.asyncio
async def test_process_document_ingestion_marks_ready_on_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(worker_main, "_create_llm_client_for_model", lambda model: None)
    owner_id = uuid4()
    storage_key = f"{owner_id}/sample.txt"
    file_path = tmp_path / storage_key
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("Document line one.\nDocument line two.", encoding="utf-8")

    document = FakeDocument(
        id=uuid4(),
        owner_user_id=owner_id,
        storage_path=storage_key,
        ingest_status=DocumentStatus.PROCESSING,
        format=DocumentFormat.TXT,
        file_name="sample.txt",
    )
    repository = FakeRepository(document)
    job = FakeJob(id=uuid4(), payload={"document_id": str(document.id)})

    await _process_document_ingestion(
        job,
        repository,
        FakeStorage(tmp_path),
        session=FakeSession(),
        index_backend=FakeIndexBackend(),
        default_llm_client=FakeLLMClient(),
        mineru_client=FakeMinerUClient(),
    )

    assert document.ingest_status == DocumentStatus.READY
    assert repository.tree_status == TreeStatus.INDEXED
    assert repository.question_set is not None
    assert repository.question_set.status == QuestionSetStatus.READY
    assert repository.question_count >= 1
    assert repository.ingestion_job_status == JobStatus.COMPLETED
    assert repository.commits == 1


@pytest.mark.asyncio
async def test_process_document_ingestion_marks_failed_on_index_error(tmp_path: Path) -> None:
    owner_id = uuid4()
    storage_key = f"{owner_id}/sample.txt"
    file_path = tmp_path / storage_key
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("Document line one.", encoding="utf-8")

    document = FakeDocument(
        id=uuid4(),
        owner_user_id=owner_id,
        storage_path=storage_key,
        ingest_status=DocumentStatus.PROCESSING,
        format=DocumentFormat.TXT,
        file_name="sample.txt",
    )
    repository = FakeRepository(document)
    job = FakeJob(id=uuid4(), payload={"document_id": str(document.id)})

    with pytest.raises(RuntimeError):
        await _process_document_ingestion(
            job,
            repository,
            FakeStorage(tmp_path),
            session=FakeSession(),
            index_backend=FailingIndexBackend(),
            default_llm_client=FakeLLMClient(),
            mineru_client=FakeMinerUClient(),
        )

    assert document.ingest_status == DocumentStatus.FAILED
    assert repository.tree_status == TreeStatus.FAILED
    assert repository.ingestion_job_status == JobStatus.FAILED
    assert repository.ingestion_error is not None
    assert len(repository.created_jobs) == 1
    created_job = repository.created_jobs[0]
    assert created_job["job_type"] == "document_failed_cleanup"
    assert created_job["max_attempts"] == 1
    cleanup_available_at = repository.created_jobs[0]["available_at"]
    assert isinstance(cleanup_available_at, datetime)
    assert abs(cleanup_available_at - (datetime.now(UTC) + timedelta(days=7))) < timedelta(
        seconds=10
    )
    assert repository.commits == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("doc_format", "file_name", "binary_content"),
    [
        (DocumentFormat.PDF, "document.pdf", b"PDF-BINARY"),
        (DocumentFormat.DOCX, "document.docx", b"DOCX-BINARY"),
        (DocumentFormat.PPTX, "document.pptx", b"PPTX-BINARY"),
    ],
)
async def test_process_document_ingestion_uses_mineru_for_non_text_formats(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    doc_format: DocumentFormat,
    file_name: str,
    binary_content: bytes,
) -> None:
    monkeypatch.setattr(worker_main, "_create_llm_client_for_model", lambda model: None)
    owner_id = uuid4()
    storage_key = f"{owner_id}/{file_name}"
    file_path = tmp_path / storage_key
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(binary_content)

    document = FakeDocument(
        id=uuid4(),
        owner_user_id=owner_id,
        storage_path=storage_key,
        ingest_status=DocumentStatus.PROCESSING,
        format=doc_format,
        file_name=file_name,
    )
    repository = FakeRepository(document)
    job = FakeJob(id=uuid4(), payload={"document_id": str(document.id)})

    await _process_document_ingestion(
        job,
        repository,
        FakeStorage(tmp_path),
        session=FakeSession(),
        index_backend=FakeIndexBackend(),
        default_llm_client=FakeLLMClient(),
        mineru_client=FakeMinerUClient(),
    )

    assert document.ingest_status == DocumentStatus.READY
    assert repository.ingestion_job_status == JobStatus.COMPLETED
