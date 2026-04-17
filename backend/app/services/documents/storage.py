import re
from dataclasses import dataclass
from enum import StrEnum
from io import BufferedIOBase
from pathlib import Path

"""Storage abstraction layer for file persistence."""


class FileValidationError(ValueError):
    pass


class StorageMode(StrEnum):
    LOCAL = "local"
    OBJECT = "object"
    R2 = "r2"


@dataclass(slots=True)
class StoredFile:
    storage_key: str
    storage_path: str
    file_name: str
    file_size_bytes: int
    media_type: str


ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt", ".md", ".markdown"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


def sanitize_file_name(file_name: str) -> str:
    base_name = Path(file_name).name.strip().lower()
    stem = re.sub(r"[^a-z0-9]+", "-", Path(base_name).stem).strip("-")
    suffix = Path(base_name).suffix.lower()
    if not stem:
        stem = "upload"
    return f"{stem}{suffix}"


def validate_upload(*, file_name: str, file_size_bytes: int) -> None:
    extension = Path(file_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise FileValidationError(f"Unsupported file type: {extension or 'unknown'}")
    if file_size_bytes > MAX_FILE_SIZE_BYTES:
        raise FileValidationError("File exceeds maximum size")


class DocumentStorage:
    def save_file(
        self,
        *,
        owner_id: str,
        file_name: str,
        file_stream: BufferedIOBase,
        media_type: str,
    ) -> StoredFile:
        content = file_stream.read()
        if not isinstance(content, bytes):
            raise TypeError("file_stream must return bytes")
        return self.save_bytes(
            owner_id=owner_id,
            file_name=file_name,
            content=content,
            media_type=media_type,
        )

    def save_bytes(
        self,
        *,
        owner_id: str,
        file_name: str,
        content: bytes,
        media_type: str,
    ) -> StoredFile:
        raise NotImplementedError

    def delete(self, storage_key: str) -> None:
        raise NotImplementedError

    def read_bytes(self, storage_key: str) -> bytes:
        raise NotImplementedError

    def read_text(self, storage_key: str) -> str:
        return self.read_bytes(storage_key).decode("utf-8", errors="ignore")


def build_storage(*, storage_mode: StorageMode, upload_dir: Path | None = None) -> DocumentStorage:
    if storage_mode == StorageMode.LOCAL:
        from app.services.documents.storage_local import LocalDocumentStorage

        return LocalDocumentStorage(root_dir=upload_dir or Path(".data/uploads"))

    if storage_mode == StorageMode.R2:
        from app.core.config import get_settings
        from app.services.documents.storage_r2 import R2DocumentStorage

        settings = get_settings()
        if not settings.r2_bucket_name:
            raise ValueError("R2_BUCKET_NAME is required when STORAGE_MODE=r2")
        if not settings.r2_endpoint_url:
            raise ValueError("R2_ACCOUNT_ID is required when STORAGE_MODE=r2")
        if not settings.r2_access_key_id:
            raise ValueError("R2_ACCESS_KEY_ID is required when STORAGE_MODE=r2")
        if not settings.r2_secret_access_key:
            raise ValueError("R2_SECRET_ACCESS_KEY is required when STORAGE_MODE=r2")

        return R2DocumentStorage(
            bucket=settings.r2_bucket_name,
            endpoint_url=settings.r2_endpoint_url,
            access_key=settings.r2_access_key_id,
            secret_key=settings.r2_secret_access_key,
        )

    if storage_mode == StorageMode.OBJECT:
        from app.services.documents.storage_object import ObjectStorageDocumentStorage

        return ObjectStorageDocumentStorage()

    raise ValueError(f"Unsupported storage mode: {storage_mode}")
