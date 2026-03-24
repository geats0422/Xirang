from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.db.models.documents import (
    DocumentFormat,
    DocumentStatus,
    JobStatus,
    QuestionSetStatus,
    TreeStatus,
)
from app.db.models.questions import QuestionType
from app.services.questions.generator import GeneratedQuestion
from app.workers.main import _process_document_ingestion


@dataclass
class FakeDocument:
    id: UUID
    storage_path: str
    ingest_status: DocumentStatus
    format: DocumentFormat


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


class FakeIndexBackend:
    async def index_document(self, *, document_id: str, content: str) -> Any:
        class Result:
            def __init__(self, document_id: str) -> None:
                self.document_id = f"tree:{document_id}"
                self.status = "indexed"

        return Result(document_id)


class FailingIndexBackend:
    async def index_document(self, *, document_id: str, content: str) -> Any:
        raise RuntimeError("index backend unavailable")


class FakeQuestionGenerator:
    async def generate(
        self,
        context: str,
        question_types: list[QuestionType],
        count: int,
        *,
        document_id: Any = None,
    ) -> list[GeneratedQuestion]:
        return [
            GeneratedQuestion(
                question_type=QuestionType.SINGLE_CHOICE,
                prompt="What is the key topic?",
                options=[
                    {"option_key": "A", "content": "Topic A", "is_correct": True},
                    {"option_key": "B", "content": "Topic B", "is_correct": False},
                ],
                explanation="From source text",
                source_locator="p1",
                difficulty=1,
                metadata={"source": "test"},
            )
        ]


class FakeRepository:
    def __init__(self, document: FakeDocument) -> None:
        self.document = document
        self.question_set: FakeQuestionSet | None = None
        self.question_count = 0
        self.tree_status: TreeStatus | None = None
        self.ingestion_job_status: JobStatus | None = None
        self.ingestion_error: str | None = None
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

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.asyncio
async def test_process_document_ingestion_marks_ready_on_success(tmp_path: Path) -> None:
    owner_id = uuid4()
    storage_key = f"{owner_id}/sample.txt"
    file_path = tmp_path / storage_key
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("Document line one.\nDocument line two.", encoding="utf-8")

    document = FakeDocument(
        id=uuid4(),
        storage_path=storage_key,
        ingest_status=DocumentStatus.PROCESSING,
        format=DocumentFormat.TXT,
    )
    repository = FakeRepository(document)
    job = FakeJob(id=uuid4(), payload={"document_id": str(document.id)})

    await _process_document_ingestion(
        job,
        repository,
        FakeStorage(tmp_path),
        index_backend=FakeIndexBackend(),
        question_generator=FakeQuestionGenerator(),
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
        storage_path=storage_key,
        ingest_status=DocumentStatus.PROCESSING,
        format=DocumentFormat.TXT,
    )
    repository = FakeRepository(document)
    job = FakeJob(id=uuid4(), payload={"document_id": str(document.id)})

    with pytest.raises(RuntimeError):
        await _process_document_ingestion(
            job,
            repository,
            FakeStorage(tmp_path),
            index_backend=FailingIndexBackend(),
            question_generator=FakeQuestionGenerator(),
        )

    assert document.ingest_status == DocumentStatus.FAILED
    assert repository.tree_status == TreeStatus.FAILED
    assert repository.ingestion_job_status == JobStatus.FAILED
    assert repository.ingestion_error is not None
    assert repository.commits == 1
