"""Core package for gungil - shared data models, database, and config."""

from core.models.doctor import Doctor
from core.models.hospital import Hospital

__all__ = ["Doctor", "Hospital"]
