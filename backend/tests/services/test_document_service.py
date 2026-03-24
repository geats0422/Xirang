from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.db.models.documents import DocumentFormat, DocumentStatus, JobStatus
from app.services.documents.service import (
    DocumentNotFoundError,
    DocumentService,
    StorageError,
)
from app.services.documents.storage import StoredFile


@dataclass
class FakeDocument:
    id: UUID
    owner_user_id: UUID
    title: str
    file_name: str
    storage_path: str
    format: DocumentFormat
    file_size_bytes: int
    mime_type: str | None
    checksum_sha256: str | None
    source_uri: str | None
    ingest_status: DocumentStatus
    page_count: int | None
    word_count: int | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass
class FakeJob:
    id: UUID
    job_type: str
    queue_name: str
    status: JobStatus
    attempt_count: int
    max_attempts: int
    payload: dict[str, object]
    error_code: str | None
    error_message: str | None
    available_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass
class FakeIngestionJob:
    id: UUID
    job_id: UUID
    document_id: UUID
    ingest_version: int
    status: JobStatus
    page_count: int | None
    word_count: int | None
    error_code: str | None
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class FakeDocumentRepository:
    def __init__(self) -> None:
        self.documents: dict[UUID, FakeDocument] = {}
        self.jobs: dict[UUID, FakeJob] = {}
        self.ingestion_jobs: dict[UUID, FakeIngestionJob] = {}
        self.commit_count = 0

    async def create_document(
        self,
        *,
        owner_user_id: UUID,
        title: str,
        file_name: str,
        storage_path: str,
        format: DocumentFormat,
        file_size_bytes: int,
        mime_type: str | None,
        checksum_sha256: str | None,
    ) -> FakeDocument:
        now = datetime.now(UTC)
        doc = FakeDocument(
            id=uuid4(),
            owner_user_id=owner_user_id,
            title=title,
            file_name=file_name,
            storage_path=storage_path,
            format=format,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            checksum_sha256=checksum_sha256,
            source_uri=None,
            ingest_status=DocumentStatus.PROCESSING,
            page_count=None,
            word_count=None,
            created_at=now,
            updated_at=now,
        )
        self.documents[doc.id] = doc
        return doc

    async def get_document_by_id(self, document_id: UUID) -> FakeDocument | None:
        return self.documents.get(document_id)

    async def list_documents_by_owner(
        self,
        owner_user_id: UUID,
        *,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FakeDocument]:
        docs = [
            d
            for d in self.documents.values()
            if d.owner_user_id == owner_user_id and (include_deleted or d.deleted_at is None)
        ]
        return docs[offset : offset + limit]

    async def update_document_status(
        self,
        *,
        document_id: UUID,
        ingest_status: DocumentStatus,
        page_count: int | None = None,
        word_count: int | None = None,
    ) -> None:
        doc = self.documents[document_id]
        doc.ingest_status = ingest_status
        doc.page_count = page_count
        doc.word_count = word_count
        doc.updated_at = datetime.now(UTC)

    async def create_job(
        self,
        *,
        job_type: str,
        queue_name: str,
        payload: dict[str, object],
        max_attempts: int = 3,
    ) -> FakeJob:
        now = datetime.now(UTC)
        job = FakeJob(
            id=uuid4(),
            job_type=job_type,
            queue_name=queue_name,
            status=JobStatus.PENDING,
            attempt_count=0,
            max_attempts=max_attempts,
            payload=payload,
            error_code=None,
            error_message=None,
            available_at=now,
            started_at=None,
            finished_at=None,
            created_at=now,
            updated_at=now,
        )
        self.jobs[job.id] = job
        return job

    async def create_ingestion_job(
        self,
        *,
        job_id: UUID,
        document_id: UUID,
        ingest_version: int = 1,
    ) -> FakeIngestionJob:
        now = datetime.now(UTC)
        ingest = FakeIngestionJob(
            id=uuid4(),
            job_id=job_id,
            document_id=document_id,
            ingest_version=ingest_version,
            status=JobStatus.PROCESSING,
            page_count=None,
            word_count=None,
            error_code=None,
            error_message=None,
            started_at=now,
            finished_at=None,
        )
        self.ingestion_jobs[ingest.id] = ingest
        return ingest

    async def get_ingestion_job_by_document(
        self,
        document_id: UUID,
    ) -> FakeIngestionJob | None:
        return next(
            (ij for ij in self.ingestion_jobs.values() if ij.document_id == document_id),
            None,
        )

    async def get_job_by_id(self, job_id: UUID) -> FakeJob | None:
        return self.jobs.get(job_id)

    async def get_latest_ingestion_version(self, document_id: UUID) -> int:
        versions = [
            ij.ingest_version
            for ij in self.ingestion_jobs.values()
            if ij.document_id == document_id
        ]
        return max(versions) if versions else 0

    async def commit(self) -> None:
        self.commit_count += 1


class FakeStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def save_bytes(
        self,
        *,
        owner_id: str,
        file_name: str,
        content: bytes,
        media_type: str,
    ) -> StoredFile:
        storage_key = f"{owner_id}/{file_name}"
        self.files[storage_key] = content
        return StoredFile(
            storage_key=storage_key,
            storage_path=f"/uploads/{storage_key}",
            file_name=file_name,
            file_size_bytes=len(content),
            media_type=media_type,
        )

    async def delete(self, storage_key: str) -> None:
        self.files.pop(storage_key, None)


def build_document_service() -> tuple[DocumentService, FakeDocumentRepository, FakeStorage]:
    repository = FakeDocumentRepository()
    storage = FakeStorage()
    service = DocumentService(repository=repository, storage=storage)
    return service, repository, storage


@pytest.mark.asyncio
async def test_upload_creates_document_with_processing_status() -> None:
    service, repository, _ = build_document_service()
    user_id = uuid4()

    result = await service.upload(
        owner_user_id=user_id,
        title="Test Document",
        file_name="test.pdf",
        file_content=b"%PDF-1.4",
        format=DocumentFormat.PDF,
        mime_type="application/pdf",
    )

    assert result.document.ingest_status == DocumentStatus.PROCESSING
    assert result.document.title == "Test Document"
    assert result.job.status == JobStatus.PENDING
    assert result.job.job_type == "document_ingestion"
    assert result.job.queue_name == "default"
    assert repository.commit_count == 1


@pytest.mark.asyncio
async def test_upload_stores_file_via_storage_adapter() -> None:
    service, _, storage = build_document_service()
    user_id = uuid4()

    result = await service.upload(
        owner_user_id=user_id,
        title="Test",
        file_name="doc.txt",
        file_content=b"hello world",
        format=DocumentFormat.TXT,
        mime_type="text/plain",
    )

    assert result.document.storage_path.endswith("doc.txt")
    assert str(user_id) in result.document.storage_path
    assert storage.files


@pytest.mark.asyncio
async def test_upload_creates_ingestion_job_linked_to_document() -> None:
    service, repository, _ = build_document_service()
    user_id = uuid4()

    result = await service.upload(
        owner_user_id=user_id,
        title="Test",
        file_name="doc.md",
        file_content=b"# Hello",
        format=DocumentFormat.MARKDOWN,
        mime_type="text/markdown",
    )

    ingestion_job = await repository.get_ingestion_job_by_document(result.document.id)
    assert ingestion_job is not None
    assert ingestion_job.job_id == result.job.id


@pytest.mark.asyncio
async def test_get_document_returns_document_for_owner() -> None:
    service, _repository, _ = build_document_service()
    user_id = uuid4()
    uploaded = await service.upload(
        owner_user_id=user_id,
        title="My Doc",
        file_name="my.txt",
        file_content=b"content",
        format=DocumentFormat.TXT,
        mime_type="text/plain",
    )

    result = await service.get_document(document_id=uploaded.document.id, owner_user_id=user_id)

    assert result.id == uploaded.document.id
    assert result.title == "My Doc"


@pytest.mark.asyncio
async def test_get_document_raises_for_non_owner() -> None:
    service, _, _ = build_document_service()
    user_id = uuid4()
    other_user_id = uuid4()
    uploaded = await service.upload(
        owner_user_id=user_id,
        title="My Doc",
        file_name="my.txt",
        file_content=b"content",
        format=DocumentFormat.TXT,
        mime_type="text/plain",
    )

    with pytest.raises(DocumentNotFoundError):
        await service.get_document(document_id=uploaded.document.id, owner_user_id=other_user_id)


@pytest.mark.asyncio
async def test_list_documents_returns_only_owner_documents() -> None:
    service, _, _ = build_document_service()
    user_id = uuid4()
    other_user_id = uuid4()

    await service.upload(
        owner_user_id=user_id,
        title="User Doc",
        file_name="u.txt",
        file_content=b"c",
        format=DocumentFormat.TXT,
        mime_type="text/plain",
    )
    await service.upload(
        owner_user_id=other_user_id,
        title="Other Doc",
        file_name="o.txt",
        file_content=b"c",
        format=DocumentFormat.TXT,
        mime_type="text/plain",
    )

    result = await service.list_documents(owner_user_id=user_id)

    assert len(result) == 1
    assert result[0].title == "User Doc"


@pytest.mark.asyncio
async def test_retry_failed_document_creates_new_job_and_resets_status() -> None:
    service, repository, _ = build_document_service()
    user_id = uuid4()
    uploaded = await service.upload(
        owner_user_id=user_id,
        title="Failed Doc",
        file_name="fail.txt",
        file_content=b"content",
        format=DocumentFormat.TXT,
        mime_type="text/plain",
    )

    await repository.update_document_status(
        document_id=uploaded.document.id,
        ingest_status=DocumentStatus.FAILED,
    )

    result = await service.retry(document_id=uploaded.document.id, owner_user_id=user_id)

    assert result.document.ingest_status == DocumentStatus.PROCESSING
    assert result.job.status == JobStatus.PENDING
    assert result.ingest_version == 2
    versions = sorted(
        ij.ingest_version
        for ij in repository.ingestion_jobs.values()
        if ij.document_id == uploaded.document.id
    )
    assert versions == [1, 2]


@pytest.mark.asyncio
async def test_retry_raises_for_non_failed_document() -> None:
    service, _, _ = build_document_service()
    user_id = uuid4()
    uploaded = await service.upload(
        owner_user_id=user_id,
        title="Processing Doc",
        file_name="proc.txt",
        file_content=b"c",
        format=DocumentFormat.TXT,
        mime_type="text/plain",
    )

    with pytest.raises(StorageError):
        await service.retry(document_id=uploaded.document.id, owner_user_id=user_id)


@pytest.mark.asyncio
async def test_get_job_status_returns_current_job_state() -> None:
    service, _repository, _ = build_document_service()
    user_id = uuid4()
    uploaded = await service.upload(
        owner_user_id=user_id,
        title="Test",
        file_name="t.txt",
        file_content=b"c",
        format=DocumentFormat.TXT,
        mime_type="text/plain",
    )

    result = await service.get_job_status(job_id=uploaded.job.id)

    assert result.id == uploaded.job.id
    assert result.status == JobStatus.PENDING
