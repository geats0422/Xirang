from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.v1.documents import get_current_user_id, get_document_service
from app.db.models.documents import DocumentFormat, DocumentStatus
from app.main import create_app


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
    ingest_status: DocumentStatus
    created_at: datetime


@dataclass
class FakeJob:
    id: UUID
    job_type: str
    status: str
    payload: dict[str, object]
    attempt_count: int = 0
    max_attempts: int = 3
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class UploadResult:
    document: FakeDocument
    job: FakeJob


@dataclass
class RetryResult:
    document: FakeDocument
    job: FakeJob
    ingest_version: int


class FakeApiDocumentService:
    def __init__(self) -> None:
        self.documents: dict[UUID, FakeDocument] = {}
        self.jobs: dict[UUID, FakeJob] = {}

    async def upload(
        self,
        *,
        owner_user_id: UUID,
        title: str,
        file_name: str,
        file_content: bytes,
        format: DocumentFormat,
        mime_type: str,
    ) -> UploadResult:
        doc_id = uuid4()
        job_id = uuid4()
        doc = FakeDocument(
            id=doc_id,
            owner_user_id=owner_user_id,
            title=title,
            file_name=file_name,
            storage_path=f"/uploads/{owner_user_id}/{file_name}",
            format=format,
            file_size_bytes=len(file_content),
            mime_type=mime_type,
            ingest_status=DocumentStatus.PROCESSING,
            created_at=datetime.now(UTC),
        )
        job = FakeJob(
            id=job_id,
            job_type="document_ingestion",
            status="pending",
            payload={"document_id": str(doc_id)},
        )
        self.documents[doc_id] = doc
        self.jobs[job_id] = job
        return UploadResult(document=doc, job=job)

    async def get_document(self, *, document_id: UUID, owner_user_id: UUID) -> FakeDocument:
        doc = self.documents.get(document_id)
        if not doc or doc.owner_user_id != owner_user_id:
            raise ValueError("Document not found")
        return doc

    async def list_documents(
        self,
        *,
        owner_user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FakeDocument]:
        return [d for d in self.documents.values() if d.owner_user_id == owner_user_id]

    async def get_job_status(self, *, job_id: UUID) -> FakeJob:
        job = self.jobs.get(job_id)
        if not job:
            raise ValueError("Job not found")
        return job

    async def retry(self, *, document_id: UUID, owner_user_id: UUID) -> RetryResult:
        doc = self.documents.get(document_id)
        if not doc or doc.owner_user_id != owner_user_id:
            raise ValueError("Document not found")
        if doc.ingest_status != DocumentStatus.FAILED:
            raise ValueError("Can only retry failed documents")
        doc.ingest_status = DocumentStatus.PROCESSING
        job = FakeJob(
            id=uuid4(),
            job_type="document_ingestion",
            status="pending",
            payload={"document_id": str(document_id)},
        )
        self.jobs[job.id] = job
        return RetryResult(
            document=doc,
            job=job,
            ingest_version=2,
        )

    async def delete_document(self, *, document_id: UUID, owner_user_id: UUID) -> FakeDocument:
        doc = self.documents.get(document_id)
        if not doc or doc.owner_user_id != owner_user_id:
            raise ValueError("Document not found")
        del self.documents[document_id]
        return doc

    async def delete_documents(
        self, *, document_ids: list[UUID], owner_user_id: UUID
    ) -> list[FakeDocument]:
        docs: list[FakeDocument] = []
        for document_id in document_ids:
            doc = self.documents.get(document_id)
            if not doc or doc.owner_user_id != owner_user_id:
                raise ValueError("One or more documents were not found")
            docs.append(doc)
        for doc in docs:
            del self.documents[doc.id]
        return docs


def create_test_client() -> TestClient:
    app = create_app()
    fake_service = FakeApiDocumentService()
    user_id = uuid4()
    app.dependency_overrides[get_document_service] = lambda: fake_service
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    return TestClient(app)


def test_upload_endpoint_creates_document_with_processing_status() -> None:
    client = create_test_client()
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Test Document"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["document"]["ingest_status"] == "processing"
    assert body["job"]["status"] == "pending"


@pytest.mark.parametrize(
    ("file_name", "mime_type"),
    [
        ("test.pdf", "application/pdf"),
        ("test.md", "text/markdown"),
        ("test.doc", "application/msword"),
        (
            "test.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        ("test.ppt", "application/vnd.ms-powerpoint"),
        (
            "test.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ),
    ],
)
def test_upload_endpoint_accepts_required_file_types(file_name: str, mime_type: str) -> None:
    client = create_test_client()
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": (file_name, b"dummy-content", mime_type)},
        data={"title": f"Upload {file_name}"},
    )
    assert response.status_code == 201


def test_upload_endpoint_validates_file_type() -> None:
    client = create_test_client()
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.exe", b"MZ", "application/octet-stream")},
        data={"title": "Bad File"},
    )
    assert response.status_code == 400


def test_upload_endpoint_requires_authorization_header() -> None:
    app = create_app()
    app.dependency_overrides[get_document_service] = lambda: FakeApiDocumentService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Test Document"},
    )

    assert response.status_code == 401


def test_upload_endpoint_rejects_invalid_user_id_header() -> None:
    app = create_app()
    app.dependency_overrides[get_document_service] = lambda: FakeApiDocumentService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/documents/upload",
        headers={
            "Authorization": "Bearer token-value",
            "X-User-Id": "not-a-uuid",
        },
        files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Test Document"},
    )

    assert response.status_code == 401


def test_delete_endpoint_removes_document_for_owner() -> None:
    client = create_test_client()
    upload = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Delete Me"},
    )
    assert upload.status_code == 201
    document_id = upload.json()["document"]["id"]

    delete_response = client.delete(f"/api/v1/documents/{document_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"id": document_id, "deleted": True}

    list_response = client.get("/api/v1/documents/")
    assert list_response.status_code == 200
    assert list_response.json()["items"] == []


def test_batch_delete_endpoint_removes_multiple_documents() -> None:
    client = create_test_client()
    upload_one = client.post(
        "/api/v1/documents/upload",
        files={"file": ("one.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "One"},
    )
    upload_two = client.post(
        "/api/v1/documents/upload",
        files={"file": ("two.pdf", b"%PDF-1.4", "application/pdf")},
        data={"title": "Two"},
    )
    first_id = upload_one.json()["document"]["id"]
    second_id = upload_two.json()["document"]["id"]

    response = client.post(
        "/api/v1/documents/batch-delete",
        json={"document_ids": [first_id, second_id]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["deleted_count"] == 2
    assert set(body["deleted_ids"]) == {first_id, second_id}

    list_response = client.get("/api/v1/documents/")
    assert list_response.status_code == 200
    assert list_response.json()["items"] == []
