from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from inspect import isawaitable
from pathlib import Path
from typing import Any, Protocol, cast
from uuid import UUID, uuid4

from app.db.models.documents import DocumentStatus, JobStatus


class DocumentServiceError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class DocumentNotFoundError(DocumentServiceError):
    status_code = 404


class StorageError(DocumentServiceError):
    status_code = 500


@dataclass(slots=True)
class UploadResult:
    document: Any
    job: Any


@dataclass(slots=True)
class RetryResult:
    document: Any
    job: Any
    ingest_version: int


@dataclass(slots=True)
class JobStatusResult:
    id: UUID
    status: JobStatus


class DocumentRepositoryProtocol(Protocol):
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
        content_text: str | None = None,
    ) -> Any: ...

    async def get_document_by_id(self, document_id: UUID) -> Any | None: ...

    async def delete_document_for_owner(
        self,
        *,
        document_id: UUID,
        owner_user_id: UUID,
    ) -> Any | None: ...

    async def get_documents_for_owner(
        self,
        *,
        document_ids: list[UUID],
        owner_user_id: UUID,
    ) -> list[Any]: ...

    async def list_documents_by_owner(
        self,
        owner_user_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Any]: ...

    async def list_document_titles_by_owner(self, owner_user_id: UUID) -> list[str]: ...

    async def create_job(
        self,
        *,
        job_type: str,
        queue_name: str,
        payload: dict[str, object],
    ) -> Any: ...

    async def create_ingestion_job(
        self,
        *,
        job_id: UUID,
        document_id: UUID,
        ingest_version: int,
    ) -> Any: ...

    async def update_document_status(
        self,
        *,
        document_id: UUID,
        ingest_status: DocumentStatus,
    ) -> None: ...

    async def get_job_by_id(self, job_id: UUID) -> Any | None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class StorageProtocol(Protocol):
    def save_bytes(
        self,
        *,
        owner_id: str,
        file_name: str,
        content: bytes,
        media_type: str,
    ) -> Any: ...

    def delete(self, storage_key: str) -> Any: ...


@dataclass(slots=True)
class DocumentService:
    repository: DocumentRepositoryProtocol
    storage: StorageProtocol

    async def _resolve_unique_title(self, *, owner_user_id: UUID, desired_title: str) -> str:
        normalized_title = desired_title.strip() or "Untitled"
        existing_titles = set(await self.repository.list_document_titles_by_owner(owner_user_id))
        if normalized_title not in existing_titles:
            return normalized_title

        path = Path(normalized_title)
        suffix = path.suffix
        stem = path.stem if suffix else normalized_title
        base_stem = stem or "Untitled"

        counter = 1
        while True:
            candidate = f"{base_stem} ({counter}){suffix}"
            if candidate not in existing_titles:
                return candidate
            counter += 1

    async def upload(
        self,
        *,
        owner_user_id: UUID,
        title: str,
        file_name: str,
        file_content: bytes,
        format: Any,
        mime_type: str,
    ) -> UploadResult:
        from app.db.models.documents import DocumentFormat

        checksum = hashlib.sha256(file_content).hexdigest()

        storage_key = f"{owner_user_id}/{uuid4()}/{file_name}"
        try:
            stored = self.storage.save_bytes(
                owner_id=str(owner_user_id),
                file_name=file_name,
                content=file_content,
                media_type=mime_type,
            )
            storage_key = str(stored.storage_key)
        except Exception as e:
            raise StorageError(f"Failed to store file: {e}") from e

        resolved_title = await self._resolve_unique_title(
            owner_user_id=owner_user_id,
            desired_title=title,
        )

        content_text = None
        if format in (DocumentFormat.MARKDOWN, DocumentFormat.TXT):
            content_text = file_content.decode("utf-8", errors="ignore")

        document = await self.repository.create_document(
            owner_user_id=owner_user_id,
            title=resolved_title,
            file_name=file_name,
            storage_path=storage_key,
            format=format,
            file_size_bytes=len(file_content),
            mime_type=mime_type,
            checksum_sha256=checksum,
            content_text=content_text,
        )

        job = await self.repository.create_job(
            job_type="document_ingestion",
            queue_name="default",
            payload={"document_id": str(document.id)},
        )

        await self.repository.create_ingestion_job(
            job_id=job.id,
            document_id=document.id,
            ingest_version=1,
        )

        await self.repository.commit()
        return UploadResult(document=document, job=job)

    async def get_document(self, document_id: UUID, owner_user_id: UUID) -> Any:
        document = await self.repository.get_document_by_id(document_id)
        if document is None or document.owner_user_id != owner_user_id:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        return document

    async def delete_document(self, document_id: UUID, owner_user_id: UUID) -> Any:
        document = await self.repository.get_document_by_id(document_id)
        if document is None or document.owner_user_id != owner_user_id:
            raise DocumentNotFoundError(f"Document not found: {document_id}")

        try:
            delete_result = self.storage.delete(document.storage_path)
            if isawaitable(delete_result):
                await cast("Awaitable[None]", delete_result)
        except Exception as e:
            raise StorageError(f"Failed to delete file from storage: {e}") from e

        deleted_document = await self.repository.delete_document_for_owner(
            document_id=document_id,
            owner_user_id=owner_user_id,
        )
        if deleted_document is None:
            await self.repository.rollback()
            raise DocumentNotFoundError(f"Document not found: {document_id}")

        await self.repository.commit()
        return deleted_document

    async def delete_documents(self, document_ids: list[UUID], owner_user_id: UUID) -> list[Any]:
        unique_ids = list(dict.fromkeys(document_ids))
        if not unique_ids:
            return []

        documents = await self.repository.get_documents_for_owner(
            document_ids=unique_ids,
            owner_user_id=owner_user_id,
        )
        if len(documents) != len(unique_ids):
            await self.repository.rollback()
            raise DocumentNotFoundError("One or more documents were not found")

        try:
            for document in documents:
                delete_result = self.storage.delete(document.storage_path)
                if isawaitable(delete_result):
                    await cast("Awaitable[None]", delete_result)
                await self.repository.delete_document_for_owner(
                    document_id=document.id,
                    owner_user_id=owner_user_id,
                )
        except Exception as e:
            await self.repository.rollback()
            raise StorageError(f"Failed to delete files from storage: {e}") from e

        await self.repository.commit()
        return documents

    async def list_documents(
        self,
        owner_user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Any]:
        return await self.repository.list_documents_by_owner(
            owner_user_id,
            limit=limit,
            offset=offset,
        )

    async def retry(self, document_id: UUID, owner_user_id: UUID) -> RetryResult:
        document = await self.repository.get_document_by_id(document_id)
        if document is None or document.owner_user_id != owner_user_id:
            raise DocumentNotFoundError(f"Document not found: {document_id}")

        if document.ingest_status != DocumentStatus.FAILED:
            raise StorageError("Document is not in failed state")

        await self.repository.update_document_status(
            document_id=document_id,
            ingest_status=DocumentStatus.PROCESSING,
        )

        next_ingest_version = 2
        get_latest_ingestion_version = getattr(
            self.repository, "get_latest_ingestion_version", None
        )
        if callable(get_latest_ingestion_version):
            latest_version_fetcher = cast(
                "Callable[[UUID], Awaitable[int]]",
                get_latest_ingestion_version,
            )
            latest_ingest_version = await latest_version_fetcher(document.id)
            next_ingest_version = max(1, int(latest_ingest_version) + 1)

        job = await self.repository.create_job(
            job_type="document_ingestion",
            queue_name="default",
            payload={"document_id": str(document.id)},
        )

        await self.repository.create_ingestion_job(
            job_id=job.id,
            document_id=document.id,
            ingest_version=next_ingest_version,
        )

        await self.repository.commit()
        updated_document = await self.repository.get_document_by_id(document_id)
        if updated_document is None:
            raise DocumentNotFoundError(f"Document not found: {document_id}")

        return RetryResult(document=updated_document, job=job, ingest_version=next_ingest_version)

    async def get_job_status(self, job_id: UUID) -> JobStatusResult:
        job = await self.repository.get_job_by_id(job_id)
        if job is None:
            raise DocumentNotFoundError(f"Job not found: {job_id}")
        return JobStatusResult(id=job.id, status=job.status)
