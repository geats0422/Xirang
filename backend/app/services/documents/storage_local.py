from pathlib import Path
from uuid import uuid4

from app.services.documents.storage import DocumentStorage, StoredFile, sanitize_file_name


class LocalDocumentStorage(DocumentStorage):
    def __init__(self, *, root_dir: Path) -> None:
        self.root_dir = root_dir

    def save_bytes(
        self,
        *,
        owner_id: str,
        file_name: str,
        content: bytes,
        media_type: str,
    ) -> StoredFile:
        safe_name = sanitize_file_name(file_name)
        storage_key = f"{owner_id}/{uuid4().hex}-{safe_name}"
        storage_path = self.root_dir / storage_key
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_bytes(content)
        return StoredFile(
            storage_key=storage_key,
            storage_path=str(storage_path),
            file_name=safe_name,
            file_size_bytes=len(content),
            media_type=media_type,
        )

    def delete(self, storage_key: str) -> None:
        target = self.root_dir / storage_key
        if target.exists():
            target.unlink()

    def read_bytes(self, storage_key: str) -> bytes:
        target = self.root_dir / storage_key
        return target.read_bytes()
