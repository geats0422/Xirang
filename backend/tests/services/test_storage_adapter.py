from io import BytesIO
from pathlib import Path

import pytest

from app.services.documents.storage import (
    DocumentStorage,
    FileValidationError,
    StorageMode,
    StoredFile,
    build_storage,
    sanitize_file_name,
    validate_upload,
)
from app.services.documents.storage_local import LocalDocumentStorage
from app.services.documents.storage_object import ObjectStorageDocumentStorage


class StubObjectStorage(ObjectStorageDocumentStorage):
    def save_bytes(
        self, *, owner_id: str, file_name: str, content: bytes, media_type: str
    ) -> StoredFile:
        return StoredFile(
            storage_key=f"objects/{owner_id}/{file_name}",
            storage_path=f"objects://bucket/{owner_id}/{file_name}",
            file_name=file_name,
            file_size_bytes=len(content),
            media_type=media_type,
        )

    def delete(self, storage_key: str) -> None:
        return None


def test_validate_upload_accepts_phase1_formats_within_size_limit() -> None:
    validate_upload(file_name="chapter-1.pdf", file_size_bytes=1024)
    validate_upload(file_name="legacy.doc", file_size_bytes=1536)
    validate_upload(file_name="notes.docx", file_size_bytes=2048)
    validate_upload(file_name="deck.ppt", file_size_bytes=3072)
    validate_upload(file_name="deck.pptx", file_size_bytes=3584)
    validate_upload(file_name="summary.txt", file_size_bytes=4096)
    validate_upload(file_name="outline.md", file_size_bytes=8192)


def test_validate_upload_rejects_unsupported_extension() -> None:
    with pytest.raises(FileValidationError, match="Unsupported file type"):
        validate_upload(file_name="archive.zip", file_size_bytes=1024)


def test_validate_upload_rejects_file_above_hard_limit() -> None:
    with pytest.raises(FileValidationError, match="File exceeds maximum size"):
        validate_upload(file_name="large.pdf", file_size_bytes=51 * 1024 * 1024)


def test_sanitize_file_name_removes_path_segments_and_keeps_ascii_safe_chars() -> None:
    assert sanitize_file_name("../My Notes (final).md") == "my-notes-final.md"
    assert sanitize_file_name(" spaced   name .PDF ") == "spaced-name.pdf"


def test_local_storage_persists_bytes_under_owner_prefix(tmp_path: Path) -> None:
    storage = LocalDocumentStorage(root_dir=tmp_path)

    stored = storage.save_bytes(
        owner_id="user-123",
        file_name="chapter-1.pdf",
        content=b"pdf-content",
        media_type="application/pdf",
    )

    saved_path = Path(stored.storage_path)
    assert saved_path.exists()
    assert saved_path.read_bytes() == b"pdf-content"
    assert stored.storage_key.startswith("user-123/")
    assert stored.file_size_bytes == 11


def test_local_storage_delete_removes_persisted_file(tmp_path: Path) -> None:
    storage = LocalDocumentStorage(root_dir=tmp_path)
    stored = storage.save_bytes(
        owner_id="user-123",
        file_name="draft.txt",
        content=b"hello",
        media_type="text/plain",
    )

    storage.delete(stored.storage_key)

    assert not Path(stored.storage_path).exists()


def test_object_storage_base_contract_can_be_extended_without_local_filesystem() -> None:
    storage = StubObjectStorage()

    stored = storage.save_file(
        owner_id="user-456",
        file_name="doc.md",
        file_stream=BytesIO(b"markdown"),
        media_type="text/markdown",
    )

    assert stored.storage_key == "objects/user-456/doc.md"
    assert stored.file_size_bytes == 8


def test_build_storage_returns_local_adapter_for_local_mode(tmp_path: Path) -> None:
    storage = build_storage(storage_mode=StorageMode.LOCAL, upload_dir=tmp_path)

    assert isinstance(storage, LocalDocumentStorage)


def test_build_storage_returns_object_adapter_for_object_mode() -> None:
    storage = build_storage(storage_mode=StorageMode.OBJECT)

    assert isinstance(storage, ObjectStorageDocumentStorage)


def test_document_storage_save_file_reads_stream_once(tmp_path: Path) -> None:
    storage: DocumentStorage = LocalDocumentStorage(root_dir=tmp_path)

    stored = storage.save_file(
        owner_id="user-789",
        file_name="unit.txt",
        file_stream=BytesIO(b"unit-test"),
        media_type="text/plain",
    )

    assert Path(stored.storage_path).read_text() == "unit-test"
