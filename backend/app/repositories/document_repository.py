from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import select

from app.db.models.documents import (
    Document,
    DocumentIngestionJob,
    DocumentPageIndexTree,
    DocumentQuestionSet,
    DocumentStatus,
    Job,
    JobStatus,
    QuestionSetStatus,
    TreeStatus,
)
from app.db.models.questions import Question, QuestionOption, QuestionType

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_document(
        self,
        *,
        owner_user_id: UUID,
        title: str,
        file_name: str,
        storage_path: str,
        format: Any,
        file_size_bytes: int,
        mime_type: str | None,
        checksum_sha256: str | None,
    ) -> Document:
        document = Document(
            owner_user_id=owner_user_id,
            title=title,
            file_name=file_name,
            storage_path=storage_path,
            format=format,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            checksum_sha256=checksum_sha256,
            ingest_status=DocumentStatus.PROCESSING,
        )
        self._session.add(document)
        await self._session.flush()
        return document

    async def get_document_by_id(self, document_id: UUID) -> Document | None:
        stmt = select(Document).where(Document.id == document_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_document_for_owner(
        self,
        *,
        document_id: UUID,
        owner_user_id: UUID,
    ) -> Document | None:
        stmt = (
            select(Document)
            .where(
                Document.id == document_id,
                Document.owner_user_id == owner_user_id,
                Document.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        document = result.scalar_one_or_none()
        if document is None:
            return None
        await self._session.delete(document)
        await self._session.flush()
        return document

    async def get_documents_for_owner(
        self,
        *,
        document_ids: list[UUID],
        owner_user_id: UUID,
    ) -> list[Document]:
        if not document_ids:
            return []
        stmt = (
            select(Document)
            .where(
                Document.id.in_(document_ids),
                Document.owner_user_id == owner_user_id,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_documents_by_owner(
        self,
        owner_user_id: UUID,
        *,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        stmt = select(Document).where(Document.owner_user_id == owner_user_id)
        if not include_deleted:
            stmt = stmt.where(Document.deleted_at.is_(None))
        stmt = stmt.order_by(Document.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_job(
        self,
        *,
        job_type: str,
        queue_name: str,
        payload: dict[str, object],
        max_attempts: int = 3,
    ) -> Job:
        job = Job(
            job_type=job_type,
            queue_name=queue_name,
            status=JobStatus.PENDING,
            attempt_count=0,
            max_attempts=max_attempts,
            payload=payload,
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def create_ingestion_job(
        self,
        *,
        job_id: UUID,
        document_id: UUID,
        ingest_version: int,
    ) -> DocumentIngestionJob:
        ingestion_job = DocumentIngestionJob(
            job_id=job_id,
            document_id=document_id,
            ingest_version=ingest_version,
            status=JobStatus.PROCESSING,
            started_at=datetime.now(UTC),
        )
        self._session.add(ingestion_job)
        await self._session.flush()
        return ingestion_job

    async def get_latest_ingestion_version(self, document_id: UUID) -> int:
        stmt = (
            select(DocumentIngestionJob)
            .where(DocumentIngestionJob.document_id == document_id)
            .order_by(DocumentIngestionJob.ingest_version.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return int(row.ingest_version) if row is not None else 0

    async def update_document_status(
        self,
        *,
        document_id: UUID,
        ingest_status: DocumentStatus,
        page_count: int | None = None,
        word_count: int | None = None,
    ) -> None:
        document = await self.get_document_by_id(document_id)
        if document is None:
            return
        document.ingest_status = ingest_status
        if page_count is not None:
            document.page_count = page_count
        if word_count is not None:
            document.word_count = word_count
        await self._session.flush()

    async def get_job_by_id(self, job_id: UUID) -> Job | None:
        stmt = select(Job).where(Job.id == job_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_ingestion_job_by_job_id(self, job_id: UUID) -> DocumentIngestionJob | None:
        stmt = select(DocumentIngestionJob).where(DocumentIngestionJob.job_id == job_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_ingestion_job_completed(
        self,
        *,
        job_id: UUID,
        page_count: int,
        word_count: int,
    ) -> None:
        ingestion_job = await self.get_ingestion_job_by_job_id(job_id)
        if ingestion_job is None:
            return
        ingestion_job.status = JobStatus.COMPLETED
        ingestion_job.page_count = page_count
        ingestion_job.word_count = word_count
        ingestion_job.finished_at = datetime.now(UTC)
        await self._session.flush()

    async def mark_ingestion_job_failed(
        self,
        *,
        job_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        ingestion_job = await self.get_ingestion_job_by_job_id(job_id)
        if ingestion_job is None:
            return
        ingestion_job.status = JobStatus.FAILED
        ingestion_job.error_code = error_code
        ingestion_job.error_message = error_message
        ingestion_job.finished_at = datetime.now(UTC)
        await self._session.flush()

    async def upsert_pageindex_tree(
        self,
        *,
        document_id: UUID,
        tree_key: str,
        status: TreeStatus,
        node_count: int | None,
    ) -> DocumentPageIndexTree:
        stmt = (
            select(DocumentPageIndexTree)
            .where(DocumentPageIndexTree.document_id == document_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        tree = result.scalar_one_or_none()
        if tree is None:
            tree = DocumentPageIndexTree(
                document_id=document_id,
                tree_key=tree_key,
                status=status,
                node_count=node_count,
                indexed_at=datetime.now(UTC) if status == TreeStatus.INDEXED else None,
            )
            self._session.add(tree)
        else:
            tree.tree_key = tree_key
            tree.status = status
            tree.node_count = node_count
            tree.indexed_at = datetime.now(UTC) if status == TreeStatus.INDEXED else None
        await self._session.flush()
        return tree

    async def get_question_set_for_document(self, document_id: UUID) -> DocumentQuestionSet | None:
        stmt = (
            select(DocumentQuestionSet)
            .where(DocumentQuestionSet.document_id == document_id)
            .order_by(DocumentQuestionSet.generation_version.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_question_set(
        self,
        *,
        document_id: UUID,
        generation_version: int,
    ) -> DocumentQuestionSet:
        question_set = DocumentQuestionSet(
            document_id=document_id,
            generation_version=generation_version,
            status=QuestionSetStatus.GENERATING,
            question_count=0,
        )
        self._session.add(question_set)
        await self._session.flush()
        return question_set

    async def update_question_set_status(
        self,
        *,
        question_set_id: UUID,
        status: QuestionSetStatus,
        question_count: int | None = None,
    ) -> None:
        stmt = select(DocumentQuestionSet).where(DocumentQuestionSet.id == question_set_id).limit(1)
        result = await self._session.execute(stmt)
        question_set = result.scalar_one_or_none()
        if question_set is None:
            return
        question_set.status = status
        if question_count is not None:
            question_set.question_count = question_count
        if status == QuestionSetStatus.READY:
            question_set.generated_at = datetime.now(UTC)
        await self._session.flush()

    async def clear_questions_for_set(self, question_set_id: UUID) -> None:
        stmt = select(Question).where(Question.question_set_id == question_set_id)
        result = await self._session.execute(stmt)
        for question in result.scalars().all():
            await self._session.delete(question)
        await self._session.flush()

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
    ) -> Question:
        question = Question(
            question_set_id=question_set_id,
            document_id=document_id,
            question_type=question_type,
            prompt=prompt,
            explanation=explanation,
            source_locator=source_locator,
            difficulty=difficulty,
            question_metadata=metadata,
        )
        self._session.add(question)
        await self._session.flush()
        return question

    async def create_question_option(
        self,
        *,
        question_id: UUID,
        option_key: str,
        content: str,
        is_correct: bool,
        sort_order: int,
    ) -> QuestionOption:
        option = QuestionOption(
            question_id=question_id,
            option_key=option_key,
            content=content,
            is_correct=is_correct,
            sort_order=sort_order,
        )
        self._session.add(option)
        await self._session.flush()
        return option

    async def claim_pending_job(self, *, queue_name: str) -> Job | None:
        stmt = (
            select(Job)
            .where(Job.queue_name == queue_name, Job.status == JobStatus.PENDING)
            .order_by(Job.created_at.asc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        job = result.scalar_one_or_none()
        if job is None:
            return None
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(UTC)
        await self._session.flush()
        return job

    async def mark_job_completed(self, *, job_id: str) -> None:
        job = await self.get_job_by_id(UUID(job_id))
        if job is None:
            return
        job.status = JobStatus.COMPLETED
        job.finished_at = datetime.now(UTC)
        await self._session.flush()

    async def mark_job_failed(
        self,
        *,
        job_id: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        job = await self.get_job_by_id(UUID(job_id))
        if job is None:
            return
        job.status = JobStatus.FAILED
        job.error_code = error_code
        job.error_message = error_message
        job.finished_at = datetime.now(UTC)
        await self._session.flush()

    async def increment_job_attempt(self, *, job_id: str) -> None:
        job = await self.get_job_by_id(UUID(job_id))
        if job is None:
            return
        job.attempt_count += 1
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
