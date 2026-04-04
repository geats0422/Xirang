"""Documents API routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.core.config import get_settings
from app.db.models.documents import DocumentFormat
from app.db.session import get_db_session
from app.repositories.document_repository import DocumentRepository
from app.services.documents.service import DocumentService, DocumentServiceError
from app.services.documents.storage import StorageMode
from app.services.documents.storage import build_storage as build_document_storage

router = APIRouter(prefix="/documents", tags=["documents"])


async def get_document_service(session: AsyncSession = Depends(get_db_session)) -> DocumentService:
    settings = get_settings()
    try:
        storage_mode = StorageMode(settings.storage_mode)
    except ValueError:
        storage_mode = StorageMode.LOCAL
    storage = build_document_storage(storage_mode=storage_mode)
    return DocumentService(repository=DocumentRepository(session), storage=storage)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    format: str | None = Form(None),
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_document_service),
) -> dict[str, Any]:
    """Upload a document."""
    file_name = file.filename or "document"
    content_type = file.content_type or "application/octet-stream"
    extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    fmt_raw = (format or extension).lower()
    format_map = {
        "pdf": DocumentFormat.PDF,
        "doc": DocumentFormat.DOC,
        "txt": DocumentFormat.TXT,
        "md": DocumentFormat.MARKDOWN,
        "markdown": DocumentFormat.MARKDOWN,
        "docx": DocumentFormat.DOCX,
        "ppt": DocumentFormat.PPT,
        "pptx": DocumentFormat.PPTX,
    }
    if fmt_raw not in format_map:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    content = await file.read()
    result = await service.upload(
        owner_user_id=user_id,
        title=title,
        file_name=file_name,
        file_content=content,
        format=format_map[fmt_raw],
        mime_type=content_type,
    )
    return {
        "document": {
            "id": str(result.document.id),
            "title": result.document.title,
            "ingest_status": str(result.document.ingest_status),
        },
        "job": {
            "id": str(result.job.id),
            "status": str(result.job.status),
        },
    }


@router.get("/{document_id}/progress")
async def get_document_progress(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_document_service),
) -> dict[str, Any]:
    """Get document processing progress.
    Returns estimated percentage based on ingest status.
    """
    try:
        document = await service.get_document(document_id=document_id, owner_user_id=user_id)
        # Map status to estimated progress percentage
        status_progress = {
            "pending": {"progress": 0, "stage": "Waiting to start"},
            "processing": {"progress": 30, "stage": "Parsing document with MinerU"},
            "indexing": {"progress": 60, "stage": "Building search index"},
            "generating": {"progress": 80, "stage": "Generating questions"},
            "ready": {"progress": 100, "stage": "Complete"},
            "failed": {"progress": 0, "stage": "Processing failed"},
        }
        status_str = str(document.ingest_status).lower()
        progress_info = status_progress.get(status_str, {"progress": 0, "stage": "Unknown"})
        return {
            "document_id": str(document.id),
            "status": str(document.ingest_status),
            "progress": progress_info["progress"],
            "stage": progress_info["stage"],
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/batch-delete")
async def batch_delete_documents(
    payload: dict[str, list[str]],
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_document_service),
) -> dict[str, Any]:
    ids_raw = payload.get("document_ids", [])
    try:
        document_ids = [UUID(item) for item in ids_raw]
        deleted_docs = await service.delete_documents(
            document_ids=document_ids, owner_user_id=user_id
        )
        return {
            "deleted_ids": [str(doc.id) for doc in deleted_docs],
            "deleted_count": len(deleted_docs),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DocumentServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_document_service),
) -> dict[str, Any]:
    """Get a document."""
    try:
        document = await service.get_document(document_id=document_id, owner_user_id=user_id)
        return {
            "id": str(document.id),
            "title": document.title,
            "status": document.ingest_status,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/")
async def list_documents(
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_document_service),
) -> dict[str, Any]:
    """List user documents."""
    documents = await service.list_documents(owner_user_id=user_id)
    return {
        "items": [
            {
                "id": str(d.id),
                "title": d.title,
                "status": str(d.ingest_status),
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in documents
        ]
    }


@router.post("/{document_id}/retry")
async def retry_document(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_document_service),
) -> dict[str, Any]:
    """Retry a failed document."""
    try:
        result = await service.retry(document_id=document_id, owner_user_id=user_id)
        return {
            "id": str(result.document.id),
            "status": result.job.status,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: UUID,
    service: Any = Depends(get_document_service),
) -> dict[str, str]:
    """Get job status."""
    job = await service.get_job_status(job_id=job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {
        "id": str(job.id),
        "status": str(job.status),
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: Any = Depends(get_document_service),
) -> dict[str, Any]:
    try:
        deleted = await service.delete_document(document_id=document_id, owner_user_id=user_id)
        return {
            "id": str(deleted.id),
            "deleted": True,
        }
    except DocumentServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
