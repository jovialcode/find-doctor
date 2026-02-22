"""Local filesystem storage backend."""

import json
from pathlib import Path
from typing import Any

from collector.storage.writer import BaseStorage


class LocalStorage(BaseStorage):
    """Local filesystem storage backend.

    Useful for local development and testing.
    """

    def __init__(self, base_dir: str | Path) -> None:
        """Initialize local storage.

        Args:
            base_dir: Base directory for storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, path: str) -> Path:
        """Get full filesystem path.

        Args:
            path: Relative path

        Returns:
            Full Path object
        """
        return self.base_dir / path

    def save(self, path: str, content: bytes) -> str:
        """Save bytes content to filesystem.

        Args:
            path: Relative path
            content: Content bytes

        Returns:
            Full path string
        """
        full_path = self._get_full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return str(full_path)

    def save_text(self, path: str, content: str) -> str:
        """Save text content to filesystem.

        Args:
            path: Relative path
            content: Text content

        Returns:
            Full path string
        """
        full_path = self._get_full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return str(full_path)

    def save_json(self, path: str, data: dict[str, Any] | list[Any]) -> str:
        """Save JSON data to filesystem.

        Args:
            path: Relative path
            data: JSON-serializable data

        Returns:
            Full path string
        """
        content = json.dumps(data, ensure_ascii=False, indent=2)
        return self.save_text(path, content)

    def load(self, path: str) -> bytes:
        """Load bytes content from filesystem.

        Args:
            path: Relative path

        Returns:
            Content bytes
        """
        return self._get_full_path(path).read_bytes()

    def load_text(self, path: str) -> str:
        """Load text content from filesystem.

        Args:
            path: Relative path

        Returns:
            Text content
        """
        return self._get_full_path(path).read_text(encoding="utf-8")

    def load_json(self, path: str) -> dict[str, Any] | list[Any]:
        """Load JSON data from filesystem.

        Args:
            path: Relative path

        Returns:
            Parsed JSON data
        """
        content = self.load_text(path)
        return json.loads(content)

    def exists(self, path: str) -> bool:
        """Check if path exists.

        Args:
            path: Relative path

        Returns:
            True if exists
        """
        return self._get_full_path(path).exists()

    def list_files(self, prefix: str) -> list[str]:
        """List files with given prefix.

        Args:
            prefix: Path prefix

        Returns:
            List of relative paths
        """
        prefix_path = self._get_full_path(prefix)
        if not prefix_path.exists():
            return []

        if prefix_path.is_file():
            return [prefix]

        files: list[str] = []
        for file_path in prefix_path.rglob("*"):
            if file_path.is_file():
                relative = file_path.relative_to(self.base_dir)
                files.append(str(relative))

        return sorted(files)

    def delete(self, path: str) -> bool:
        """Delete a file.

        Args:
            path: Relative path

        Returns:
            True if deleted
        """
        full_path = self._get_full_path(path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False
