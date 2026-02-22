"""Storage module for saving crawled data."""

from collector.storage.writer import StorageWriter
from collector.storage.gcs import GCSStorage
from collector.storage.local import LocalStorage

__all__ = ["StorageWriter", "GCSStorage", "LocalStorage"]
