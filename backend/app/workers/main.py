from __future__ import annotations

import asyncio
import signal
from pathlib import Path
from typing import Any, Protocol, cast
from uuid import UUID

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.models.documents import DocumentStatus, Job, QuestionSetStatus, TreeStatus
from app.db.models.questions import QuestionType
from app.db.session import get_session_factory
from app.integrations.agents.client import AgentsClient
from app.integrations.pageindex.client import PageIndexClient
from app.repositories.document_repository import DocumentRepository
from app.services.documents.storage import StorageMode
from app.services.documents.storage import build_storage as build_document_storage
from app.services.questions.generator import GeneratedQuestion, QuestionGenerator
from app.services.retrieval.pageindex_backend import (
    IndexDocumentResult,
    PageIndexBackend,
    PageIndexConfig,
)
from app.workers.job_runner import JobRunner
from app.workers.registry import JobRegistry


class IngestionRepositoryProtocol(Protocol):
    async def get_document_by_id(self, document_id: UUID) -> Any | None: ...

    async def update_document_status(
        self,
        *,
        document_id: UUID,
        ingest_status: DocumentStatus,
        page_count: int | None = None,
        word_count: int | None = None,
    ) -> None: ...

    async def upsert_pageindex_tree(
        self,
        *,
        document_id: UUID,
        tree_key: str,
        status: TreeStatus,
        node_count: int | None,
    ) -> Any: ...

    async def get_question_set_for_document(self, document_id: UUID) -> Any | None: ...

    async def create_question_set(
        self,
        *,
        document_id: UUID,
        generation_version: int,
    ) -> Any: ...

    async def update_question_set_status(
        self,
        *,
        question_set_id: UUID,
        status: QuestionSetStatus,
        question_count: int | None = None,
    ) -> None: ...

    async def clear_questions_for_set(self, question_set_id: UUID) -> None: ...

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
    ) -> Any: ...

    async def create_question_option(
        self,
        *,
        question_id: UUID,
        option_key: str,
        content: str,
        is_correct: bool,
        sort_order: int,
    ) -> Any: ...

    async def mark_ingestion_job_completed(
        self,
        *,
        job_id: UUID,
        page_count: int,
        word_count: int,
    ) -> None: ...

    async def mark_ingestion_job_failed(
        self,
        *,
        job_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None: ...

    async def commit(self) -> None: ...


class IngestionIndexBackendProtocol(Protocol):
    async def index_document(self, *, document_id: str, content: str) -> IndexDocumentResult: ...


class IngestionQuestionGeneratorProtocol(Protocol):
    async def generate(
        self,
        context: str,
        question_types: list[QuestionType],
        count: int,
        *,
        document_id: Any = None,
    ) -> list[GeneratedQuestion]: ...


class HeuristicQuestionGenerator:
    async def generate(
        self,
        context: str,
        question_types: list[QuestionType],
        count: int,
        *,
        document_id: Any = None,
    ) -> list[GeneratedQuestion]:
        chunks = [line.strip() for line in context.splitlines() if line.strip()]
        if not chunks:
            chunks = ["This document contains study material."]

        generated: list[GeneratedQuestion] = []
        types = question_types or [QuestionType.SINGLE_CHOICE]
        for index in range(count):
            chunk = chunks[index % len(chunks)]
            question_type = types[index % len(types)]
            generated.append(
                GeneratedQuestion(
                    question_type=question_type,
                    prompt=f"Which statement best matches: {chunk[:80]}?",
                    options=[
                        {
                            "option_key": "A",
                            "content": "It is explicitly stated.",
                            "is_correct": True,
                        },
                        {
                            "option_key": "B",
                            "content": "It is contradicted by the text.",
                            "is_correct": False,
                        },
                        {
                            "option_key": "C",
                            "content": "The text does not mention this.",
                            "is_correct": False,
                        },
                    ],
                    explanation="Answer based on available document context.",
                    source_locator="local-heuristic",
                    difficulty=min(5, (index % 5) + 1),
                    metadata={"generator": "heuristic"},
                )
            )
        return generated


class WorkerJobRepository:
    def __init__(self, document_repository: DocumentRepository) -> None:
        self._repo = document_repository

    async def claim_pending_job(self, *, queue_name: str) -> Job | None:
        job = await self._repo.claim_pending_job(queue_name=queue_name)
        if job is not None:
            await self._repo.commit()
        return job

    async def mark_completed(self, *, job_id: str) -> None:
        await self._repo.mark_job_completed(job_id=job_id)
        await self._repo.commit()

    async def mark_failed(
        self,
        *,
        job_id: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        await self._repo.mark_job_failed(
            job_id=job_id,
            error_code=error_code,
            error_message=error_message,
        )
        await self._repo.commit()

    async def increment_attempt(self, *, job_id: str) -> None:
        await self._repo.increment_job_attempt(job_id=job_id)
        await self._repo.commit()


def build_job_registry() -> JobRegistry:
    registry = JobRegistry()
    settings = get_settings()
    session_factory = get_session_factory()

    try:
        storage_mode = StorageMode(settings.storage_mode)
    except ValueError:
        storage_mode = StorageMode.LOCAL

    storage = build_document_storage(
        storage_mode=storage_mode, upload_dir=Path(settings.upload_dir)
    )
    index_backend = PageIndexBackend(
        client=PageIndexClient(base_url=settings.pageindex_url),
        config=PageIndexConfig(base_url=settings.pageindex_url),
    )

    if settings.openai_api_key:
        agents_client = AgentsClient(api_key=settings.openai_api_key)
        provider = agents_client.registry.get_default()
        question_generator: IngestionQuestionGeneratorProtocol
        if provider is None:
            question_generator = HeuristicQuestionGenerator()
        else:
            question_generator = QuestionGenerator(provider.client)
    else:
        question_generator = HeuristicQuestionGenerator()

    async def document_ingestion_handler(job: Job) -> None:
        async with session_factory() as session:
            repository = DocumentRepository(session)
            await _process_document_ingestion(
                job,
                repository,
                storage,
                index_backend=index_backend,
                question_generator=question_generator,
            )

    registry.register("document_ingestion", document_ingestion_handler)
    return registry


async def _process_document_ingestion(
    job: Any,
    repository: IngestionRepositoryProtocol,
    storage: Any,
    *,
    index_backend: IngestionIndexBackendProtocol,
    question_generator: IngestionQuestionGeneratorProtocol,
) -> None:
    payload = job.payload if isinstance(job.payload, dict) else {}
    raw_document_id = payload.get("document_id")
    if not isinstance(raw_document_id, str):
        raise ValueError("document_id missing in job payload")

    document_id = UUID(raw_document_id)
    document = await repository.get_document_by_id(document_id)
    if document is None:
        raise ValueError(f"Document not found: {document_id}")

    try:
        await repository.update_document_status(
            document_id=document_id,
            ingest_status=DocumentStatus.PROCESSING,
        )

        content = _read_document_content(document.storage_path, storage)
        if not content.strip():
            raise ValueError("Document content is empty")

        page_count = _estimate_page_count(content)
        word_count = _estimate_word_count(content)

        index_result = await index_backend.index_document(
            document_id=str(document_id), content=content
        )
        await repository.upsert_pageindex_tree(
            document_id=document_id,
            tree_key=index_result.document_id,
            status=TreeStatus.INDEXED,
            node_count=page_count,
        )

        question_set = await repository.get_question_set_for_document(document_id)
        if question_set is not None and question_set.status == QuestionSetStatus.READY:
            await repository.mark_ingestion_job_completed(
                job_id=job.id,
                page_count=page_count,
                word_count=word_count,
            )
            await repository.update_document_status(
                document_id=document_id,
                ingest_status=DocumentStatus.READY,
                page_count=page_count,
                word_count=word_count,
            )
            await repository.commit()
            return

        if question_set is None:
            question_set = await repository.create_question_set(
                document_id=document_id, generation_version=1
            )
        else:
            await repository.update_question_set_status(
                question_set_id=question_set.id,
                status=QuestionSetStatus.GENERATING,
            )
            await repository.clear_questions_for_set(question_set.id)

        questions = await question_generator.generate(
            context=content[:12000],
            question_types=[
                QuestionType.SINGLE_CHOICE,
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.TRUE_FALSE,
            ],
            count=10,
            document_id=document_id,
        )

        if not questions:
            raise ValueError("Question generation returned no questions")

        for generated in questions:
            source_locator: dict[str, object] | None = (
                {"source": generated.source_locator}
                if generated.source_locator is not None
                else None
            )
            question = await repository.create_question(
                question_set_id=question_set.id,
                document_id=document_id,
                question_type=generated.question_type,
                prompt=generated.prompt,
                explanation=generated.explanation,
                source_locator=source_locator,
                difficulty=generated.difficulty,
                metadata=generated.metadata,
            )

            for index, option in enumerate(generated.options):
                option_key_raw = option.get("option_key")
                option_key = (
                    str(option_key_raw) if isinstance(option_key_raw, str) else chr(65 + index)
                )
                option_content = str(option.get("content", ""))
                is_correct = bool(option.get("is_correct", False))
                await repository.create_question_option(
                    question_id=question.id,
                    option_key=option_key,
                    content=option_content,
                    is_correct=is_correct,
                    sort_order=index,
                )

        await repository.update_question_set_status(
            question_set_id=question_set.id,
            status=QuestionSetStatus.READY,
            question_count=len(questions),
        )
        await repository.update_document_status(
            document_id=document_id,
            ingest_status=DocumentStatus.READY,
            page_count=page_count,
            word_count=word_count,
        )
        await repository.mark_ingestion_job_completed(
            job_id=job.id,
            page_count=page_count,
            word_count=word_count,
        )
        await repository.commit()
    except Exception as e:
        await repository.upsert_pageindex_tree(
            document_id=document_id,
            tree_key=str(document_id),
            status=TreeStatus.FAILED,
            node_count=None,
        )
        await repository.update_document_status(
            document_id=document_id,
            ingest_status=DocumentStatus.FAILED,
        )
        await repository.mark_ingestion_job_failed(
            job_id=job.id,
            error_code="INGESTION_FAILED",
            error_message=str(e),
        )
        await repository.commit()
        raise


def _read_document_content(storage_key: str, storage: Any) -> str:
    root_dir = None
    storage_any = cast("Any", storage)
    if hasattr(storage_any, "root_dir"):
        root_dir = storage_any.root_dir
    if isinstance(root_dir, Path):
        target = root_dir / storage_key
        if target.exists():
            return target.read_text(encoding="utf-8", errors="ignore")

    fallback = Path(storage_key)
    if fallback.exists():
        return fallback.read_text(encoding="utf-8", errors="ignore")

    raise FileNotFoundError(f"Cannot locate source document at {storage_key}")


def _estimate_page_count(content: str) -> int:
    paragraph_count = sum(1 for line in content.splitlines() if line.strip())
    return max(1, (paragraph_count // 30) + 1)


def _estimate_word_count(content: str) -> int:
    return len([word for word in content.split() if word.strip()])


async def run_worker(*, queue_name: str = "default", poll_interval: float = 1.0) -> None:
    registry = build_job_registry()
    session_factory = get_session_factory()

    async with session_factory() as session:
        document_repo = DocumentRepository(session)
        repository = WorkerJobRepository(document_repo)
        runner = JobRunner(repository=repository, registry=registry)

        shutdown = False

        def handle_signal(signum: int, frame: object) -> None:
            nonlocal shutdown
            shutdown = True

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        while not shutdown:
            processed = await runner.run_one(queue_name=queue_name)
            if not processed:
                await asyncio.sleep(poll_interval)


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    asyncio.run(
        run_worker(
            queue_name="default",
            poll_interval=1.0,
        )
    )


if __name__ == "__main__":
    main()
