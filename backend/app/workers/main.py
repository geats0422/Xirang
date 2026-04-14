from __future__ import annotations

import asyncio
import logging
import os
import re
import signal
import sys
import time
from collections.abc import Awaitable, Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime, timedelta
from inspect import isawaitable
from pathlib import Path
from typing import Any, Protocol, cast
from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.models.documents import (
    DocumentFormat,
    DocumentStatus,
    Job,
    QuestionSetStatus,
    TreeStatus,
)
from app.db.models.profile import UserSetting
from app.db.models.questions import QuestionType
from app.db.session import get_session_factory
from app.integrations.agents.client import AgentsClient, OpenAIClient
from app.integrations.mineru.client import MinerUClient
from app.integrations.pageindex.client import PageIndexClient
from app.repositories.document_repository import DocumentRepository
from app.services.documents.normalizer import normalize_markdown
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

logger = logging.getLogger(__name__)


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

    async def create_job(
        self,
        *,
        job_type: str,
        queue_name: str,
        payload: dict[str, object],
        max_attempts: int = 3,
        available_at: datetime | None = None,
    ) -> Any: ...

    async def delete_document_by_id(self, document_id: UUID) -> None: ...

    async def commit(self) -> None: ...


class IngestionIndexBackendProtocol(Protocol):
    async def index_document(self, *, document_id: str, content: str) -> IndexDocumentResult: ...
    async def ask(self, *, document_id: str, question: str, context_chunks: int = 3) -> Any: ...


class IngestionQuestionGeneratorProtocol(Protocol):
    async def generate(
        self,
        context: str,
        question_types: list[QuestionType],
        count: int,
        *,
        document_id: Any = None,
        model: str | None = None,
        language_code: str = "en",
    ) -> list[GeneratedQuestion]: ...


class MinerUClientProtocol(Protocol):
    async def parse_to_markdown(
        self,
        *,
        file_name: str,
        file_bytes: bytes,
        backend: str | None = None,
        lang_list: tuple[str, ...] | None = None,
    ) -> str: ...


class CleanupRepositoryProtocol(Protocol):
    async def get_document_by_id(self, document_id: UUID) -> Any | None: ...

    async def delete_document_by_id(self, document_id: UUID) -> None: ...

    async def commit(self) -> None: ...


class HeuristicQuestionGenerator:
    async def generate(
        self,
        context: str,
        question_types: list[QuestionType],
        count: int,
        *,
        document_id: Any = None,
        game_mode: str | None = None,
        model: str | None = None,
        language_code: str = "en",
    ) -> list[GeneratedQuestion]:
        chunks = [
            line.strip() for line in context.splitlines() if line.strip() and len(line.strip()) > 20
        ]
        if not chunks:
            chunks = ["This document contains important study material that should be reviewed."]

        generated: list[GeneratedQuestion] = []
        use_zh = language_code.strip().lower().startswith("zh")

        # Determine question type based on game mode
        if game_mode == "endless-abyss":
            question_type = QuestionType.FILL_IN_BLANK
        elif game_mode == "speed-survival":
            question_type = QuestionType.TRUE_FALSE
        else:
            question_type = QuestionType.SINGLE_CHOICE

        for index in range(count):
            chunk = chunks[index % len(chunks)]
            # Extract key terms from the chunk (simple heuristic)
            words = chunk.split()
            key_term = words[len(words) // 2] if len(words) > 3 else "concept"

            if question_type == QuestionType.FILL_IN_BLANK:
                # Fill-in-blank for Endless Abyss
                prompt_text = chunk.replace(key_term, "____", 1)
                prompt_prefix = "补全句子: " if use_zh else "Complete the statement: "
                starts_with_label = "首字母" if use_zh else "Starts with"
                letters_label = "字符数" if use_zh else "letters"
                explanation_text = (
                    f"术语“{key_term}”与该语境匹配。"
                    if use_zh
                    else f"The term '{key_term}' fits this context."
                )
                generated.append(
                    GeneratedQuestion(
                        question_type=QuestionType.FILL_IN_BLANK,
                        prompt=f"{prompt_prefix}{prompt_text[:120]}",
                        options=[],
                        correct_answer=key_term,
                        hints=[
                            f"{starts_with_label} '{key_term[0].upper()}'",
                            f"{letters_label}: {len(key_term)}",
                        ],
                        explanation=explanation_text,
                        source_locator="local-heuristic",
                        difficulty=min(5, (index % 5) + 1),
                        metadata={"generator": "heuristic", "answer": key_term},
                    )
                )
            elif question_type == QuestionType.TRUE_FALSE:
                # True/False for Speed Survival
                is_true = index % 2 == 0
                explanation_text = "基于文档内容。" if use_zh else "Based on the document content."
                generated.append(
                    GeneratedQuestion(
                        question_type=QuestionType.TRUE_FALSE,
                        prompt=chunk[:150],
                        options=[
                            {
                                "option_key": "A",
                                "content": "正确" if use_zh else "True",
                                "is_correct": is_true,
                            },
                            {
                                "option_key": "B",
                                "content": "错误" if use_zh else "False",
                                "is_correct": not is_true,
                            },
                        ],
                        explanation=explanation_text,
                        source_locator="local-heuristic",
                        difficulty=min(5, (index % 5) + 1),
                        metadata={"generator": "heuristic"},
                    )
                )
            else:
                # Single/Multiple choice for Knowledge Draft (displayed as fill-in-blank)
                prompt_with_blank = chunk.replace(key_term, "____", 1)
                prompt_text = (
                    f"哪个术语最适合填空: {prompt_with_blank[:120]}?"
                    if use_zh
                    else f"Which term best completes: {prompt_with_blank[:120]}?"
                )
                explanation_text = (
                    f"术语“{key_term}”在该语境中正确。"
                    if use_zh
                    else f"The term '{key_term}' is correct in this context."
                )
                generated.append(
                    GeneratedQuestion(
                        question_type=QuestionType.SINGLE_CHOICE,
                        prompt=prompt_text,
                        options=[
                            {"option_key": "A", "content": key_term, "is_correct": True},
                            {
                                "option_key": "B",
                                "content": "替代概念" if use_zh else "alternative concept",
                                "is_correct": False,
                            },
                            {
                                "option_key": "C",
                                "content": "无关术语" if use_zh else "unrelated term",
                                "is_correct": False,
                            },
                            {
                                "option_key": "D",
                                "content": "另一个选项" if use_zh else "another option",
                                "is_correct": False,
                            },
                        ],
                        explanation=explanation_text,
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


async def _get_user_generation_preferences(session: Any, user_id: UUID) -> tuple[str | None, str]:
    stmt = select(UserSetting.selected_model, UserSetting.language_code).where(
        UserSetting.user_id == user_id
    )
    result = await session.execute(stmt)
    row = result.one_or_none()
    if row is None:
        return None, "en"
    selected_model, language_code = row
    normalized_language = str(language_code or "en").strip() or "en"
    return cast("str | None", selected_model), normalized_language


def _create_llm_client_for_model(model: str | None) -> OpenAIClient | None:
    settings = get_settings()
    if not settings.llm_api_key:
        return None
    return OpenAIClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=model or settings.llm_model,
    )


async def _get_enriched_context_from_pageindex(
    index_backend: IngestionIndexBackendProtocol,
    document_id: str,
    content: str,
) -> str:
    raw_context = content[:12000]
    study_queries = [
        "What are the main concepts, theories, or key points covered in this document?",
        "What are the important definitions, formulas, or technical terms explained?",
        "What examples, case studies, or practical applications are discussed?",
        "What conclusions, recommendations, or takeaways are presented?",
    ]

    enriched_parts: list[str] = []

    for query in study_queries:
        try:
            result = await index_backend.ask(
                document_id=document_id,
                question=query,
                context_chunks=5,
            )
            answer = getattr(result, "answer", None)
            if not isinstance(answer, str):
                continue

            answer_text = answer.strip()
            if not _is_trustworthy_pageindex_answer(answer_text, raw_context):
                logger.warning(
                    "Rejected untrusted PageIndex enrichment for document %s (query=%s)",
                    document_id,
                    query,
                )
                continue

            enriched_parts.append(f"Topic: {query}\nAnswer: {answer_text[:2000]}")
        except Exception as exc:
            logger.debug("PageIndex.ask failed for query '%s': %s", query, exc)

    if enriched_parts:
        enriched_context = "\n\n".join(enriched_parts)
        logger.info(
            "PageIndex enrichment appended: %d bytes from %d queries",
            len(enriched_context),
            len(enriched_parts),
        )
        return f"{raw_context}\n\n[Supplemental retrieval notes]\n{enriched_context}"

    logger.debug("PageIndex enrichment unavailable, using raw content")
    return raw_context


def _is_trustworthy_pageindex_answer(answer: str, raw_context: str) -> bool:
    if len(answer) <= 50:
        return False
    if _looks_like_schema_or_prompt(answer):
        return False

    answer_tokens = _tokenize_text(answer)
    if not answer_tokens:
        return False
    source_tokens = _tokenize_text(raw_context)
    overlap_count = len(answer_tokens & source_tokens)
    overlap_ratio = overlap_count / len(answer_tokens)
    return overlap_count >= 8 or overlap_ratio >= 0.08


def _looks_like_schema_or_prompt(text: str) -> bool:
    lower_text = text.lower()
    contamination_markers = (
        "system prompt",
        "you are an ai",
        "role:",
        "instruction:",
        "output format",
        "json schema",
        '"properties"',
        '"required"',
    )
    if any(marker in lower_text for marker in contamination_markers):
        return True

    normalized = lower_text.strip()
    return normalized.startswith("{") and ('"type"' in normalized or '"properties"' in normalized)


def _tokenize_text(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z\u4e00-\u9fff]{2,}", text.lower()))


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
    mineru_client = MinerUClient(
        base_url=settings.mineru_url,
        timeout_seconds=settings.mineru_timeout_seconds,
        backend=settings.mineru_backend,
        lang_list=tuple(settings.mineru_lang_list),
    )

    agents_client = AgentsClient()
    provider = agents_client.registry.get_default()
    default_llm_client = provider.client if provider is not None else None

    async def document_ingestion_handler(job: Job) -> None:
        async with session_factory() as session:
            repository = DocumentRepository(session)
            await _process_document_ingestion(
                job,
                repository,
                storage,
                session=session,
                index_backend=index_backend,
                default_llm_client=default_llm_client,
                mineru_client=mineru_client,
            )

    async def document_failed_cleanup_handler(job: Job) -> None:
        async with session_factory() as session:
            repository = DocumentRepository(session)
            await _process_document_failed_cleanup(job, repository, storage)

    registry.register("document_ingestion", document_ingestion_handler)
    registry.register("document_failed_cleanup", document_failed_cleanup_handler)
    return registry


async def _process_document_ingestion(
    job: Any,
    repository: IngestionRepositoryProtocol,
    storage: Any,
    *,
    session: Any,
    index_backend: IngestionIndexBackendProtocol,
    default_llm_client: Any,
    mineru_client: MinerUClientProtocol,
) -> None:
    payload = job.payload if isinstance(job.payload, dict) else {}
    raw_document_id = payload.get("document_id")
    if not isinstance(raw_document_id, str):
        raise ValueError("document_id missing in job payload")

    document_id = UUID(raw_document_id)
    document = await repository.get_document_by_id(document_id)
    if document is None:
        raise ValueError(f"Document not found: {document_id}")

    user_selected_model, user_language_code = await _get_user_generation_preferences(
        session, document.owner_user_id
    )
    llm_client = _create_llm_client_for_model(user_selected_model) or default_llm_client

    if llm_client is not None:
        question_generator: IngestionQuestionGeneratorProtocol = QuestionGenerator(llm_client)
        logger.info("Using LLM for question generation: model=%s", user_selected_model or "default")
    else:
        question_generator = HeuristicQuestionGenerator()
        logger.warning(
            "LLM not available for document %s (user=%s). "
            "Falling back to heuristic question generator (low quality). "
            "Configure NVIDIA_API_KEY to enable LLM-powered generation.",
            document_id,
            document.owner_user_id,
        )

    try:
        await repository.update_document_status(
            document_id=document_id,
            ingest_status=DocumentStatus.PROCESSING,
        )

        content = await _load_document_markdown(
            storage=storage,
            storage_key=document.storage_path,
            file_name=document.file_name,
            document_format=document.format,
            mineru_client=mineru_client,
            content_text=document.content_text,
        )
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

        enriched_context = await _get_enriched_context_from_pageindex(
            index_backend=index_backend,
            document_id=str(document_id),
            content=content,
        )

        questions = await question_generator.generate(
            context=enriched_context,
            question_types=[
                QuestionType.SINGLE_CHOICE,
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.TRUE_FALSE,
                QuestionType.FILL_IN_BLANK,
            ],
            count=15,
            document_id=document_id,
            model=user_selected_model,
            language_code=user_language_code,
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
        await repository.create_job(
            job_type="document_failed_cleanup",
            queue_name="default",
            payload={"document_id": str(document_id)},
            max_attempts=1,
            available_at=datetime.now(UTC) + timedelta(days=7),
        )
        await repository.commit()
        raise


async def _process_document_failed_cleanup(
    job: Any,
    repository: CleanupRepositoryProtocol,
    storage: Any,
) -> None:
    payload = job.payload if isinstance(job.payload, dict) else {}
    raw_document_id = payload.get("document_id")
    if not isinstance(raw_document_id, str):
        raise ValueError("document_id missing in cleanup job payload")

    document_id = UUID(raw_document_id)
    document = await repository.get_document_by_id(document_id)
    if document is None:
        await repository.commit()
        return

    if document.ingest_status != DocumentStatus.FAILED:
        await repository.commit()
        return

    delete_result = storage.delete(document.storage_path)
    if isawaitable(delete_result):
        await cast("Awaitable[None]", delete_result)

    await repository.delete_document_by_id(document_id)
    await repository.commit()


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


def _read_document_bytes(storage_key: str, storage: Any) -> bytes:
    root_dir = None
    storage_any = cast("Any", storage)
    if hasattr(storage_any, "root_dir"):
        root_dir = storage_any.root_dir
    if isinstance(root_dir, Path):
        target = root_dir / storage_key
        if target.exists():
            return target.read_bytes()

    fallback = Path(storage_key)
    if fallback.exists():
        return fallback.read_bytes()

    raise FileNotFoundError(f"Cannot locate source document at {storage_key}")


async def _load_document_markdown(
    *,
    storage: Any,
    storage_key: str,
    file_name: str,
    document_format: DocumentFormat,
    mineru_client: MinerUClientProtocol,
    content_text: str | None = None,
) -> str:
    if document_format in (DocumentFormat.MARKDOWN, DocumentFormat.TXT):
        if content_text is not None:
            return normalize_markdown(content_text)
        raw_content = _read_document_content(storage_key, storage)
        return normalize_markdown(raw_content)

    raw_bytes = _read_document_bytes(storage_key, storage)
    parsed_markdown = await mineru_client.parse_to_markdown(
        file_name=file_name,
        file_bytes=raw_bytes,
    )
    return normalize_markdown(parsed_markdown)


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


def _worker_lock_path(queue_name: str) -> Path:
    data_dir = Path(__file__).resolve().parent.parent.parent / ".data"
    return data_dir / f"worker-{queue_name}.lock"


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


@contextmanager
def _worker_single_instance(queue_name: str) -> Iterator[None]:
    lock_path = _worker_lock_path(queue_name)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = None
    max_retries = 3
    retry_delay = 0.5

    try:
        while True:
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                break
            except FileExistsError:
                existing_pid = 0
                with suppress(Exception):
                    existing_pid = int(lock_path.read_text(encoding="utf-8").strip() or "0")
                if _pid_is_running(existing_pid):
                    raise RuntimeError(
                        f"worker already running for queue {queue_name}: {existing_pid}"
                    ) from None
                for attempt in range(max_retries):
                    try:
                        lock_path.unlink()
                        break
                    except OSError:
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(retry_delay)
        os.write(fd, str(os.getpid()).encode("utf-8"))
        yield
    finally:
        if fd is not None:
            with suppress(OSError):
                os.close(fd)
        with suppress(OSError):
            lock_path.unlink()


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    try:
        with _worker_single_instance("default"):
            asyncio.run(
                run_worker(
                    queue_name="default",
                    poll_interval=1.0,
                )
            )
    except RuntimeError as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
