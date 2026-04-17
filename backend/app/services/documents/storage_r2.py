from uuid import uuid4

import boto3
from botocore.config import Config

from app.services.documents.storage import DocumentStorage, StoredFile, sanitize_file_name


class R2DocumentStorage(DocumentStorage):
    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
    ) -> None:
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )

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
        self.client.put_object(
            Bucket=self.bucket,
            Key=storage_key,
            Body=content,
            ContentType=media_type,
        )
        return StoredFile(
            storage_key=storage_key,
            storage_path=storage_key,
            file_name=safe_name,
            file_size_bytes=len(content),
            media_type=media_type,
        )

    def delete(self, storage_key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=storage_key)

    def read_bytes(self, storage_key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=storage_key)
        body = response["Body"]
        content = body.read()
        if not isinstance(content, bytes):
            raise TypeError("R2 get_object body must be bytes")
        return content
