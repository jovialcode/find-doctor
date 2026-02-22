"""Google Cloud Storage backend."""

import json
from typing import Any

from collector.storage.writer import BaseStorage


class GCSStorage(BaseStorage):
    """Google Cloud Storage backend.

    Requires google-cloud-storage package.
    """

    def __init__(self, bucket_name: str, project_id: str | None = None) -> None:
        """Initialize GCS storage.

        Args:
            bucket_name: GCS bucket name
            project_id: Optional GCP project ID
        """
        from google.cloud import storage

        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)
        self.bucket_name = bucket_name

    def save(self, path: str, content: bytes) -> str:
        """Save bytes content to GCS.

        Args:
            path: GCS object path
            content: Content bytes

        Returns:
            GCS URI
        """
        blob = self.bucket.blob(path)
        blob.upload_from_string(content)
        return f"gs://{self.bucket_name}/{path}"

    def save_text(self, path: str, content: str) -> str:
        """Save text content to GCS.

        Args:
            path: GCS object path
            content: Text content

        Returns:
            GCS URI
        """
        blob = self.bucket.blob(path)
        blob.upload_from_string(content, content_type="text/plain; charset=utf-8")
        return f"gs://{self.bucket_name}/{path}"

    def save_json(self, path: str, data: dict[str, Any] | list[Any]) -> str:
        """Save JSON data to GCS.

        Args:
            path: GCS object path
            data: JSON-serializable data

        Returns:
            GCS URI
        """
        content = json.dumps(data, ensure_ascii=False, indent=2)
        blob = self.bucket.blob(path)
        blob.upload_from_string(content, content_type="application/json")
        return f"gs://{self.bucket_name}/{path}"

    def load(self, path: str) -> bytes:
        """Load bytes content from GCS.

        Args:
            path: GCS object path

        Returns:
            Content bytes
        """
        blob = self.bucket.blob(path)
        return blob.download_as_bytes()

    def load_text(self, path: str) -> str:
        """Load text content from GCS.

        Args:
            path: GCS object path

        Returns:
            Text content
        """
        blob = self.bucket.blob(path)
        return blob.download_as_text(encoding="utf-8")

    def load_json(self, path: str) -> dict[str, Any] | list[Any]:
        """Load JSON data from GCS.

        Args:
            path: GCS object path

        Returns:
            Parsed JSON data
        """
        content = self.load_text(path)
        return json.loads(content)

    def exists(self, path: str) -> bool:
        """Check if object exists in GCS.

        Args:
            path: GCS object path

        Returns:
            True if exists
        """
        blob = self.bucket.blob(path)
        return blob.exists()

    def list_files(self, prefix: str) -> list[str]:
        """List objects with given prefix.

        Args:
            prefix: Object prefix

        Returns:
            List of object paths
        """
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]

    def delete(self, path: str) -> bool:
        """Delete an object.

        Args:
            path: GCS object path

        Returns:
            True if deleted
        """
        blob = self.bucket.blob(path)
        if blob.exists():
            blob.delete()
            return True
        return False
