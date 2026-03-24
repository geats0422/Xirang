from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.documents import DocumentFormat, DocumentStatus, JobStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    file_name: str
    format: DocumentFormat
    file_size_bytes: int
    ingest_status: DocumentStatus
    created_at: datetime
    updated_at: datetime | None = None


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    limit: int
    offset: int


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_type: str
    status: JobStatus
    attempt_count: int
    max_attempts: int
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime


class UploadResponse(BaseModel):
    document: DocumentResponse
    job: JobResponse


class RetryResponse(BaseModel):
    document: DocumentResponse
    job: JobResponse
    ingest_version: int


class DocumentStatusResponse(BaseModel):
    document_id: UUID
    ingest_status: DocumentStatus
    job_id: UUID | None = None
    job_status: JobStatus | None = None
    error_message: str | None = None
