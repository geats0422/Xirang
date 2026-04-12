from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from app.db.models.documents import DocumentStatus
from app.workers.main import _process_document_failed_cleanup


@dataclass
class FakeDocument:
    id: UUID
    storage_path: str
    ingest_status: DocumentStatus


@dataclass
class FakeJob:
    id: UUID
    payload: dict[str, object]


class FakeStorage:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    async def delete(self, storage_key: str) -> None:
        self.deleted.append(storage_key)


class FakeRepository:
    def __init__(self, document: FakeDocument | None) -> None:
        self.document = document
        self.deleted_document_ids: list[UUID] = []
        self.commit_count = 0

    async def get_document_by_id(self, document_id: UUID) -> FakeDocument | None:
        if self.document is None:
            return None
        return self.document if self.document.id == document_id else None

    async def delete_document_by_id(self, document_id: UUID) -> None:
        self.deleted_document_ids.append(document_id)
        self.document = None

    async def commit(self) -> None:
        self.commit_count += 1


@pytest.mark.asyncio
async def test_failed_document_cleanup_deletes_failed_document() -> None:
    document = FakeDocument(
        id=uuid4(),
        storage_path="user/doc.pdf",
        ingest_status=DocumentStatus.FAILED,
    )
    repository = FakeRepository(document)
    storage = FakeStorage()
    job = FakeJob(id=uuid4(), payload={"document_id": str(document.id)})

    await _process_document_failed_cleanup(job, repository, storage)

    assert storage.deleted == ["user/doc.pdf"]
    assert repository.deleted_document_ids == [document.id]
    assert repository.commit_count == 1


@pytest.mark.asyncio
async def test_failed_document_cleanup_skips_non_failed_document() -> None:
    document = FakeDocument(
        id=uuid4(),
        storage_path="user/doc.pdf",
        ingest_status=DocumentStatus.READY,
    )
    repository = FakeRepository(document)
    storage = FakeStorage()
    job = FakeJob(id=uuid4(), payload={"document_id": str(document.id)})

    await _process_document_failed_cleanup(job, repository, storage)

    assert storage.deleted == []
    assert repository.deleted_document_ids == []
    assert repository.commit_count == 1


@pytest.mark.asyncio
async def test_failed_document_cleanup_noop_when_document_missing() -> None:
    repository = FakeRepository(document=None)
    storage = FakeStorage()
    job = FakeJob(id=uuid4(), payload={"document_id": str(uuid4())})

    await _process_document_failed_cleanup(job, repository, storage)

    assert storage.deleted == []
    assert repository.deleted_document_ids == []
    assert repository.commit_count == 1


@pytest.mark.asyncio
async def test_failed_document_cleanup_is_idempotent_on_second_run() -> None:
    document = FakeDocument(
        id=uuid4(),
        storage_path="user/doc.pdf",
        ingest_status=DocumentStatus.FAILED,
    )
    repository = FakeRepository(document)
    storage = FakeStorage()
    job = FakeJob(id=uuid4(), payload={"document_id": str(document.id)})

    await _process_document_failed_cleanup(job, repository, storage)
    await _process_document_failed_cleanup(job, repository, storage)

    assert storage.deleted == ["user/doc.pdf"]
    assert repository.deleted_document_ids == [document.id]
    assert repository.commit_count == 2
