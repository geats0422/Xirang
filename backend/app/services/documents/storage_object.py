from app.services.documents.storage import DocumentStorage, StoredFile


class ObjectStorageDocumentStorage(DocumentStorage):
    def save_bytes(
        self,
        *,
        owner_id: str,
        file_name: str,
        content: bytes,
        media_type: str,
    ) -> StoredFile:
        raise NotImplementedError("Object storage adapter is not configured yet")

    def delete(self, storage_key: str) -> None:
        raise NotImplementedError("Object storage adapter is not configured yet")
