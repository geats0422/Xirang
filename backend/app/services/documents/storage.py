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


def build_storage(*, storage_mode: StorageMode, upload_dir: Path | None = None) -> DocumentStorage:
    if storage_mode == StorageMode.LOCAL:
        from app.services.documents.storage_local import LocalDocumentStorage

        return LocalDocumentStorage(root_dir=upload_dir or Path(".data/uploads"))

    from app.services.documents.storage_object import ObjectStorageDocumentStorage

    return ObjectStorageDocumentStorage()
