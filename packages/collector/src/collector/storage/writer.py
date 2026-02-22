"""Storage writer for saving crawled and parsed data."""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol


class Storage(Protocol):
    """Storage protocol for different backends."""

    def save(self, path: str, content: bytes) -> str:
        """Save content to storage.

        Args:
            path: Storage path
            content: Content bytes to save

        Returns:
            Full path/URL of saved content
        """
        ...

    def load(self, path: str) -> bytes:
        """Load content from storage.

        Args:
            path: Storage path

        Returns:
            Content bytes
        """
        ...

    def exists(self, path: str) -> bool:
        """Check if path exists.

        Args:
            path: Storage path

        Returns:
            True if exists
        """
        ...


class BaseStorage(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save(self, path: str, content: bytes) -> str:
        """Save content to storage."""
        ...

    @abstractmethod
    def save_text(self, path: str, content: str) -> str:
        """Save text content to storage."""
        ...

    @abstractmethod
    def save_json(self, path: str, data: dict[str, Any] | list[Any]) -> str:
        """Save JSON data to storage."""
        ...

    @abstractmethod
    def load(self, path: str) -> bytes:
        """Load content from storage."""
        ...

    @abstractmethod
    def load_text(self, path: str) -> str:
        """Load text content from storage."""
        ...

    @abstractmethod
    def load_json(self, path: str) -> dict[str, Any] | list[Any]:
        """Load JSON data from storage."""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        ...

    @abstractmethod
    def list_files(self, prefix: str) -> list[str]:
        """List files with given prefix."""
        ...


class StorageWriter:
    """High-level writer for saving crawl and parse results."""

    def __init__(self, storage: BaseStorage, base_path: str = "") -> None:
        """Initialize the storage writer.

        Args:
            storage: Storage backend to use
            base_path: Base path prefix for all writes
        """
        self.storage = storage
        self.base_path = base_path.rstrip("/")

    def _make_path(self, *parts: str) -> str:
        """Construct a storage path.

        Args:
            parts: Path components

        Returns:
            Full path
        """
        if self.base_path:
            return "/".join([self.base_path, *parts])
        return "/".join(parts)

    def _get_timestamp_path(self) -> str:
        """Get timestamp-based path component.

        Returns:
            Timestamp path like "2024/01/15"
        """
        now = datetime.now()
        return f"{now.year}/{now.month:02d}/{now.day:02d}"

    def save_raw_html(self, site_id: str, target_name: str, url: str, html: str) -> str:
        """Save raw HTML from crawl.

        Args:
            site_id: Site identifier
            target_name: Target name
            url: Source URL
            html: HTML content

        Returns:
            Storage path
        """
        # Create unique filename from URL
        url_hash = str(hash(url))[-8:]
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{url_hash}_{timestamp}.html"

        path = self._make_path(
            "raw",
            site_id,
            target_name,
            self._get_timestamp_path(),
            filename,
        )

        return self.storage.save_text(path, html)

    def save_parsed_data(
        self,
        site_id: str,
        target_name: str,
        data: list[dict[str, Any]],
    ) -> str:
        """Save parsed data.

        Args:
            site_id: Site identifier
            target_name: Target name
            data: Parsed data items

        Returns:
            Storage path
        """
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"parsed_{timestamp}.json"

        path = self._make_path(
            "parsed",
            site_id,
            target_name,
            self._get_timestamp_path(),
            filename,
        )

        return self.storage.save_json(path, data)

    def save_crawl_manifest(
        self,
        site_id: str,
        crawled_urls: list[str],
        errors: list[dict[str, Any]],
    ) -> str:
        """Save crawl manifest with summary.

        Args:
            site_id: Site identifier
            crawled_urls: List of crawled URLs
            errors: List of errors

        Returns:
            Storage path
        """
        manifest = {
            "site_id": site_id,
            "crawled_at": datetime.now().isoformat(),
            "total_urls": len(crawled_urls),
            "total_errors": len(errors),
            "urls": crawled_urls,
            "errors": errors,
        }

        path = self._make_path(
            "manifests",
            site_id,
            self._get_timestamp_path(),
            f"manifest_{datetime.now().strftime('%H%M%S')}.json",
        )

        return self.storage.save_json(path, manifest)
