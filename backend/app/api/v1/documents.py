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
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Get document processing progress.
    Returns real progress based on document/job/tree/question_set status.
    """
    try:
        document = await service.get_document(document_id=document_id, owner_user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    repo = DocumentRepository(session)
    job = await repo.get_latest_job_for_document(document_id)
    tree = await repo.get_pageindex_tree(document_id)
    question_set = await repo.get_question_set_for_document(document_id)

    status_str = str(document.ingest_status).lower()

    if status_str == "failed":
        progress = 0
        stage = "Processing failed"
    elif status_str == "ready":
        progress = 100
        stage = "Complete"
    elif status_str == "pending":
        progress = 0
        stage = "Waiting to start"
    else:
        job_status = str(job.status).lower() if job else "unknown"
        tree_status = str(tree.status).lower() if tree else "none"
        qs_status = str(question_set.status).lower() if question_set else "none"

        if job_status == "failed":
            progress = 0
            stage = "Processing failed"
        elif qs_status == "ready":
            progress = 95
            stage = "Finalizing"
        elif tree_status == "indexed":
            progress = 80
            stage = "Generating questions"
        elif tree_status == "indexing":
            progress = 60
            stage = "Building search index"
        elif job_status == "processing":
            progress = 30
            stage = "Parsing document"
        else:
            progress = 15
            stage = "Queued for processing"

    return {
        "document_id": str(document.id),
        "status": status_str,
        "progress": progress,
        "stage": stage,
    }


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
                "file_name": d.file_name,
                "format": str(d.format),
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


@router.get("/diagnostics/queue")
async def get_queue_diagnostics(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Get queue diagnostics for document ingestion jobs."""
    from app.db.models.documents import JobStatus

    repo = DocumentRepository(session)
    stats = await repo.get_queue_stats(queue_name="default")

    pending = stats.get(str(JobStatus.PENDING), 0)
    processing = stats.get(str(JobStatus.PROCESSING), 0)
    completed = stats.get(str(JobStatus.COMPLETED), 0)
    failed = stats.get(str(JobStatus.FAILED), 0)

    return {
        "queue": "default",
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "total": pending + processing + completed + failed,
    }
