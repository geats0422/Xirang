from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.db.models.documents import (
    DocumentFormat,
    DocumentStatus,
    Job,
    JobStatus,
    QuestionSetStatus,
)
from app.db.models.questions import QuestionType
from app.workers.job_runner import JobRunner
from app.workers.registry import JobRegistry


@dataclass
class FakeDocument:
    id: UUID
    owner_user_id: UUID
    title: str
    file_name: str
    storage_path: str
    format: DocumentFormat
    file_size_bytes: int
    ingest_status: DocumentStatus = DocumentStatus.PROCESSING
    mime_type: str | None = None
    checksum_sha256: str | None = None
    source_uri: str | None = None
    page_count: int | None = None
    word_count: int | None = None
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeQuestionSet:
    id: UUID
    document_id: UUID
    generation_version: int = 1
    status: QuestionSetStatus = QuestionSetStatus.PENDING
    question_count: int = 0
    generated_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeQuestion:
    id: UUID
    question_set_id: UUID
    document_id: UUID
    question_type: QuestionType
    prompt: str
    explanation: str | None = None
    source_locator: dict[str, Any] | None = None
    difficulty: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeQuestionOption:
    id: UUID
    question_id: UUID
    option_key: str
    content: str
    is_correct: bool = False
    sort_order: int = 0


class FakeIngestionRepository:
    def __init__(self) -> None:
        self.documents: dict[UUID, FakeDocument] = {}
        self.question_sets: dict[UUID, FakeQuestionSet] = {}
        self.questions: dict[UUID, FakeQuestion] = {}
        self.options: dict[UUID, FakeQuestionOption] = {}

    async def get_document(self, document_id: UUID) -> FakeDocument | None:
        return self.documents.get(document_id)

    async def update_document_status(
        self,
        *,
        document_id: UUID,
        status: DocumentStatus,
    ) -> None:
        if document_id in self.documents:
            self.documents[document_id].ingest_status = status
            self.documents[document_id].updated_at = datetime.now(UTC)

    async def get_question_set_for_document(self, document_id: UUID) -> FakeQuestionSet | None:
        for qs in self.question_sets.values():
            if qs.document_id == document_id:
                return qs
        return None

    async def create_question_set(
        self,
        *,
        document_id: UUID,
    ) -> FakeQuestionSet:
        qs = FakeQuestionSet(
            id=uuid4(),
            document_id=document_id,
            status=QuestionSetStatus.GENERATING,
        )
        self.question_sets[qs.id] = qs
        return qs

    async def update_question_set_status(
        self,
        *,
        question_set_id: UUID,
        status: QuestionSetStatus,
        question_count: int | None = None,
    ) -> None:
        if question_set_id in self.question_sets:
            qs = self.question_sets[question_set_id]
            qs.status = status
            if question_count is not None:
                qs.question_count = question_count
            if status == QuestionSetStatus.READY:
                qs.generated_at = datetime.now(UTC)

    async def create_question(
        self,
        *,
        question_set_id: UUID,
        document_id: UUID,
        question_type: QuestionType,
        prompt: str,
        explanation: str | None = None,
        source_locator: dict[str, Any] | None = None,
        difficulty: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> FakeQuestion:
        q = FakeQuestion(
            id=uuid4(),
            question_set_id=question_set_id,
            document_id=document_id,
            question_type=question_type,
            prompt=prompt,
            explanation=explanation,
            source_locator=source_locator,
            difficulty=difficulty,
            metadata=metadata or {},
        )
        self.questions[q.id] = q
        return q

    async def create_question_option(
        self,
        *,
        question_id: UUID,
        option_key: str,
        content: str,
        is_correct: bool = False,
        sort_order: int = 0,
    ) -> FakeQuestionOption:
        opt = FakeQuestionOption(
            id=uuid4(),
            question_id=question_id,
            option_key=option_key,
            content=content,
            is_correct=is_correct,
            sort_order=sort_order,
        )
        self.options[opt.id] = opt
        return opt

    async def commit(self) -> None:
        pass


class FakeJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.claimed_ids: set[str] = set()

    def add_job(self, job: Job) -> None:
        self.jobs[str(job.id)] = job

    async def claim_pending_job(self, *, queue_name: str) -> Job | None:
        for job in self.jobs.values():
            if (
                job.status == JobStatus.PENDING
                and job.queue_name == queue_name
                and str(job.id) not in self.claimed_ids
            ):
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now(UTC)
                self.claimed_ids.add(str(job.id))
                return job
        return None

    async def mark_completed(self, *, job_id: str) -> None:
        job = self.jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.finished_at = datetime.now(UTC)

    async def mark_failed(
        self,
        *,
        job_id: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        job = self.jobs.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.finished_at = datetime.now(UTC)
            job.error_code = error_code
            job.error_message = error_message

    async def increment_attempt(self, *, job_id: str) -> None:
        job = self.jobs.get(job_id)
        if job:
            job.attempt_count += 1


def make_job(
    *,
    job_type: str = "question_generation",
    document_id: UUID | None = None,
    status: JobStatus = JobStatus.PENDING,
    payload: dict[str, Any] | None = None,
) -> Job:
    return Job(
        id=uuid4(),
        job_type=job_type,
        queue_name="default",
        status=status,
        attempt_count=0,
        max_attempts=3,
        payload=payload or {"document_id": str(document_id or uuid4())},
        available_at=datetime.now(UTC),
    )


class FakeQuestionGeneratorClient:
    def __init__(self, questions: list[dict[str, Any]] | None = None) -> None:
        self.questions = questions or []
        self.call_count = 0

    async def generate_questions(
        self,
        *,
        document_id: UUID,
        context: str,
        question_types: list[QuestionType],
        count: int,
    ) -> list[dict[str, Any]]:
        self.call_count += 1
        return self.questions


class TestIngestionPipeline:
    @pytest.mark.asyncio
    async def test_question_generation_job_creates_questions_and_updates_status(self) -> None:
        document_id = uuid4()
        job_repo = FakeJobRepository()
        ingestion_repo = FakeIngestionRepository()

        ingestion_repo.documents[document_id] = FakeDocument(
            id=document_id,
            owner_user_id=uuid4(),
            title="Test Doc",
            file_name="test.pdf",
            storage_path="/data/test.pdf",
            format=DocumentFormat.PDF,
            file_size_bytes=1000,
            ingest_status=DocumentStatus.PROCESSING,
        )

        sample_questions = [
            {
                "question_type": QuestionType.SINGLE_CHOICE,
                "prompt": "What is 2 + 2?",
                "options": [
                    {"option_key": "A", "content": "3", "is_correct": False},
                    {"option_key": "B", "content": "4", "is_correct": True},
                    {"option_key": "C", "content": "5", "is_correct": False},
                    {"option_key": "D", "content": "6", "is_correct": False},
                ],
                "explanation": "2 + 2 equals 4",
                "difficulty": 1,
            },
        ]

        generator_client = FakeQuestionGeneratorClient(questions=sample_questions)

        async def question_generation_handler(job: Job) -> None:
            doc_id = UUID(job.payload["document_id"])
            doc = await ingestion_repo.get_document(doc_id)
            if doc is None:
                raise ValueError("Document not found")

            qs = await ingestion_repo.get_question_set_for_document(doc_id)
            if qs is None:
                qs = await ingestion_repo.create_question_set(document_id=doc_id)

            questions_data = await generator_client.generate_questions(
                document_id=doc_id,
                context="Extracted content from document",
                question_types=[
                    QuestionType.SINGLE_CHOICE,
                    QuestionType.MULTIPLE_CHOICE,
                    QuestionType.TRUE_FALSE,
                ],
                count=10,
            )

            for q_data in questions_data:
                question = await ingestion_repo.create_question(
                    question_set_id=qs.id,
                    document_id=doc_id,
                    question_type=q_data["question_type"],
                    prompt=q_data["prompt"],
                    explanation=q_data.get("explanation"),
                    difficulty=q_data.get("difficulty", 1),
                )
                for idx, opt_data in enumerate(q_data.get("options", [])):
                    await ingestion_repo.create_question_option(
                        question_id=question.id,
                        option_key=opt_data["option_key"],
                        content=opt_data["content"],
                        is_correct=opt_data.get("is_correct", False),
                        sort_order=idx,
                    )

            await ingestion_repo.update_question_set_status(
                question_set_id=qs.id,
                status=QuestionSetStatus.READY,
                question_count=len(questions_data),
            )
            await ingestion_repo.update_document_status(
                document_id=doc_id,
                status=DocumentStatus.READY,
            )

        registry = JobRegistry()
        registry.register("question_generation", question_generation_handler)

        job = make_job(job_type="question_generation", document_id=document_id)
        job_repo.add_job(job)

        runner = JobRunner(repository=job_repo, registry=registry)
        await runner.run_one(queue_name="default")

        assert job.status == JobStatus.COMPLETED
        assert len(ingestion_repo.questions) == 1
        assert len(ingestion_repo.options) == 4
        qs = await ingestion_repo.get_question_set_for_document(document_id)
        assert qs is not None
        assert qs.status == QuestionSetStatus.READY
        assert qs.question_count == 1
        assert ingestion_repo.documents[document_id].ingest_status == DocumentStatus.READY

    @pytest.mark.asyncio
    async def test_question_generation_job_retries_on_failure(self) -> None:
        document_id = uuid4()
        job_repo = FakeJobRepository()
        ingestion_repo = FakeIngestionRepository()

        ingestion_repo.documents[document_id] = FakeDocument(
            id=document_id,
            owner_user_id=uuid4(),
            title="Test Doc",
            file_name="test.pdf",
            storage_path="/data/test.pdf",
            format=DocumentFormat.PDF,
            file_size_bytes=1000,
        )

        call_count = 0

        async def failing_handler(job: Job) -> None:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("Temporary failure")

        registry = JobRegistry()
        registry.register("question_generation", failing_handler)

        job = make_job(job_type="question_generation", document_id=document_id)
        job_repo.add_job(job)

        runner = JobRunner(repository=job_repo, registry=registry)

        for _ in range(3):
            if job.status == JobStatus.PENDING:
                await runner.run_one(queue_name="default")

        assert call_count == 1
        assert job.status == JobStatus.FAILED

    @pytest.mark.asyncio
    async def test_question_generation_skips_if_question_set_already_ready(self) -> None:
        document_id = uuid4()
        job_repo = FakeJobRepository()
        ingestion_repo = FakeIngestionRepository()

        ingestion_repo.documents[document_id] = FakeDocument(
            id=document_id,
            owner_user_id=uuid4(),
            title="Test Doc",
            file_name="test.pdf",
            storage_path="/data/test.pdf",
            format=DocumentFormat.PDF,
            file_size_bytes=1000,
            ingest_status=DocumentStatus.READY,
        )

        existing_qs = FakeQuestionSet(
            id=uuid4(),
            document_id=document_id,
            status=QuestionSetStatus.READY,
            question_count=5,
        )
        ingestion_repo.question_sets[existing_qs.id] = existing_qs

        generator_called = False

        async def idempotent_handler(job: Job) -> None:
            nonlocal generator_called
            doc_id = UUID(job.payload["document_id"])
            qs = await ingestion_repo.get_question_set_for_document(doc_id)
            if qs is not None and qs.status == QuestionSetStatus.READY:
                return
            generator_called = True

        registry = JobRegistry()
        registry.register("question_generation", idempotent_handler)

        job = make_job(job_type="question_generation", document_id=document_id)
        job_repo.add_job(job)

        runner = JobRunner(repository=job_repo, registry=registry)
        await runner.run_one(queue_name="default")

        assert job.status == JobStatus.COMPLETED
        assert not generator_called

    @pytest.mark.asyncio
    async def test_pipeline_generates_multiple_question_types(self) -> None:
        document_id = uuid4()
        job_repo = FakeJobRepository()
        ingestion_repo = FakeIngestionRepository()

        ingestion_repo.documents[document_id] = FakeDocument(
            id=document_id,
            owner_user_id=uuid4(),
            title="Mixed Questions Doc",
            file_name="test.pdf",
            storage_path="/data/test.pdf",
            format=DocumentFormat.PDF,
            file_size_bytes=1000,
        )

        sample_questions = [
            {
                "question_type": QuestionType.SINGLE_CHOICE,
                "prompt": "Single choice question?",
                "options": [
                    {"option_key": "A", "content": "Option A", "is_correct": True},
                    {"option_key": "B", "content": "Option B", "is_correct": False},
                ],
                "explanation": "Single choice explanation",
                "difficulty": 1,
            },
            {
                "question_type": QuestionType.TRUE_FALSE,
                "prompt": "True or false question?",
                "options": [
                    {"option_key": "A", "content": "True", "is_correct": True},
                    {"option_key": "B", "content": "False", "is_correct": False},
                ],
                "explanation": "True/false explanation",
                "difficulty": 1,
            },
            {
                "question_type": QuestionType.MULTIPLE_CHOICE,
                "prompt": "Select all correct answers:",
                "options": [
                    {"option_key": "A", "content": "A", "is_correct": True},
                    {"option_key": "B", "content": "B", "is_correct": True},
                    {"option_key": "C", "content": "C", "is_correct": False},
                    {"option_key": "D", "content": "D", "is_correct": False},
                ],
                "explanation": "Multiple choice explanation",
                "difficulty": 2,
            },
        ]

        generator_client = FakeQuestionGeneratorClient(questions=sample_questions)

        async def multi_type_handler(job: Job) -> None:
            doc_id = UUID(job.payload["document_id"])
            qs = await ingestion_repo.create_question_set(document_id=doc_id)

            questions_data = await generator_client.generate_questions(
                document_id=doc_id,
                context="Context",
                question_types=[
                    QuestionType.SINGLE_CHOICE,
                    QuestionType.MULTIPLE_CHOICE,
                    QuestionType.TRUE_FALSE,
                ],
                count=10,
            )

            for q_data in questions_data:
                question = await ingestion_repo.create_question(
                    question_set_id=qs.id,
                    document_id=doc_id,
                    question_type=q_data["question_type"],
                    prompt=q_data["prompt"],
                    explanation=q_data.get("explanation"),
                    difficulty=q_data.get("difficulty", 1),
                )
                for idx, opt_data in enumerate(q_data.get("options", [])):
                    await ingestion_repo.create_question_option(
                        question_id=question.id,
                        option_key=opt_data["option_key"],
                        content=opt_data["content"],
                        is_correct=opt_data.get("is_correct", False),
                        sort_order=idx,
                    )

            await ingestion_repo.update_question_set_status(
                question_set_id=qs.id,
                status=QuestionSetStatus.READY,
                question_count=len(questions_data),
            )
            await ingestion_repo.update_document_status(
                document_id=doc_id,
                status=DocumentStatus.READY,
            )

        registry = JobRegistry()
        registry.register("question_generation", multi_type_handler)

        job = make_job(job_type="question_generation", document_id=document_id)
        job_repo.add_job(job)

        runner = JobRunner(repository=job_repo, registry=registry)
        await runner.run_one(queue_name="default")

        assert job.status == JobStatus.COMPLETED
        assert len(ingestion_repo.questions) == 3
        types = {q.question_type for q in ingestion_repo.questions.values()}
        assert types == {
            QuestionType.SINGLE_CHOICE,
            QuestionType.TRUE_FALSE,
            QuestionType.MULTIPLE_CHOICE,
        }
