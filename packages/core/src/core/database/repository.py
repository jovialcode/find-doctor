"""Repository implementations for Doctor and Hospital."""

from abc import ABC, abstractmethod
from typing import Protocol

from core.models.doctor import Doctor
from core.models.hospital import Hospital


class Repository(Protocol):
    """Base repository protocol."""

    def find_by_id(self, id: str) -> dict | None:
        """Find entity by ID."""
        ...

    def save(self, entity: dict) -> dict:
        """Save entity."""
        ...

    def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        ...


class BaseRepository(ABC):
    """Abstract base repository with common operations."""

    @abstractmethod
    def find_by_id(self, id: str) -> dict | None:
        """Find entity by ID."""
        ...

    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Find all entities with pagination."""
        ...

    @abstractmethod
    def save(self, entity: dict) -> dict:
        """Save entity."""
        ...

    @abstractmethod
    def save_many(self, entities: list[dict]) -> list[dict]:
        """Save multiple entities."""
        ...

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        ...


class DoctorRepository(BaseRepository):
    """Repository for Doctor entities.

    This is a base implementation that can be extended for different backends
    (PostgreSQL, BigQuery, Firestore, etc.)
    """

    def __init__(self) -> None:
        self._storage: dict[str, dict] = {}

    def find_by_id(self, id: str) -> dict | None:
        """Find doctor by ID."""
        return self._storage.get(id)

    def find_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Find all doctors with pagination."""
        all_doctors = list(self._storage.values())
        return all_doctors[offset : offset + limit]

    def find_by_hospital(self, hospital_id: str) -> list[dict]:
        """Find all doctors in a hospital."""
        return [d for d in self._storage.values() if d.get("hospital_id") == hospital_id]

    def find_by_department(self, department: str) -> list[dict]:
        """Find all doctors in a department."""
        return [d for d in self._storage.values() if d.get("department") == department]

    def save(self, entity: dict) -> dict:
        """Save doctor."""
        doctor_id = entity.get("id")
        if not doctor_id:
            raise ValueError("Doctor must have an ID")
        self._storage[doctor_id] = entity
        return entity

    def save_many(self, entities: list[dict]) -> list[dict]:
        """Save multiple doctors."""
        for entity in entities:
            self.save(entity)
        return entities

    def delete(self, id: str) -> bool:
        """Delete doctor by ID."""
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    def search(self, query: str) -> list[dict]:
        """Search doctors by name or specialty."""
        query_lower = query.lower()
        results = []
        for doctor in self._storage.values():
            if query_lower in doctor.get("name", "").lower():
                results.append(doctor)
            elif any(query_lower in s.lower() for s in doctor.get("specialty", [])):
                results.append(doctor)
        return results


class HospitalRepository(BaseRepository):
    """Repository for Hospital entities.

    This is a base implementation that can be extended for different backends.
    """

    def __init__(self) -> None:
        self._storage: dict[str, dict] = {}

    def find_by_id(self, id: str) -> dict | None:
        """Find hospital by ID."""
        return self._storage.get(id)

    def find_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Find all hospitals with pagination."""
        all_hospitals = list(self._storage.values())
        return all_hospitals[offset : offset + limit]

    def find_by_region(self, region: str) -> list[dict]:
        """Find all hospitals in a region."""
        return [h for h in self._storage.values() if h.get("region") == region]

    def find_by_type(self, hospital_type: str) -> list[dict]:
        """Find all hospitals of a specific type."""
        return [h for h in self._storage.values() if h.get("type") == hospital_type]

    def save(self, entity: dict) -> dict:
        """Save hospital."""
        hospital_id = entity.get("id")
        if not hospital_id:
            raise ValueError("Hospital must have an ID")
        self._storage[hospital_id] = entity
        return entity

    def save_many(self, entities: list[dict]) -> list[dict]:
        """Save multiple hospitals."""
        for entity in entities:
            self.save(entity)
        return entities

    def delete(self, id: str) -> bool:
        """Delete hospital by ID."""
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    def search(self, query: str) -> list[dict]:
        """Search hospitals by name or region."""
        query_lower = query.lower()
        results = []
        for hospital in self._storage.values():
            if query_lower in hospital.get("name", "").lower():
                results.append(hospital)
            elif query_lower in hospital.get("region", "").lower():
                results.append(hospital)
        return results
