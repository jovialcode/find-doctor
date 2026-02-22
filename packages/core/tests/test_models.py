"""Tests for data models."""

import pytest
from datetime import datetime

from core.models.doctor import Doctor, ConsultationHours
from core.models.hospital import Hospital


class TestDoctor:
    """Tests for Doctor model."""

    def test_create_doctor(self) -> None:
        """Test creating a doctor instance."""
        doctor = Doctor(
            id="doc-001",
            name="김철수",
            hospital_id="hosp-001",
            department="내과",
            specialty=("소화기내과", "간담도내과"),
        )

        assert doctor.id == "doc-001"
        assert doctor.name == "김철수"
        assert doctor.hospital_id == "hosp-001"
        assert doctor.department == "내과"
        assert doctor.specialty == ("소화기내과", "간담도내과")
        assert doctor.is_accepting_new is True

    def test_doctor_immutability(self) -> None:
        """Test that doctor is immutable."""
        doctor = Doctor(
            id="doc-001",
            name="김철수",
            hospital_id="hosp-001",
            department="내과",
        )

        with pytest.raises(AttributeError):
            doctor.name = "박영희"  # type: ignore

    def test_doctor_to_dict(self) -> None:
        """Test converting doctor to dictionary."""
        doctor = Doctor(
            id="doc-001",
            name="김철수",
            hospital_id="hosp-001",
            department="내과",
            specialty=("소화기내과",),
            education=("서울대학교 의과대학",),
        )

        data = doctor.to_dict()

        assert data["id"] == "doc-001"
        assert data["name"] == "김철수"
        assert data["specialty"] == ["소화기내과"]
        assert data["education"] == ["서울대학교 의과대학"]

    def test_doctor_from_dict(self) -> None:
        """Test creating doctor from dictionary."""
        data = {
            "id": "doc-001",
            "name": "김철수",
            "hospital_id": "hosp-001",
            "department": "내과",
            "specialty": ["소화기내과"],
            "education": ["서울대학교 의과대학"],
            "consultation_hours": [
                {"day": "월요일", "start_time": "09:00", "end_time": "17:00"}
            ],
        }

        doctor = Doctor.from_dict(data)

        assert doctor.id == "doc-001"
        assert doctor.name == "김철수"
        assert doctor.specialty == ("소화기내과",)
        assert len(doctor.consultation_hours) == 1
        assert doctor.consultation_hours[0].day == "월요일"

    def test_doctor_roundtrip(self) -> None:
        """Test that to_dict and from_dict are reversible."""
        original = Doctor(
            id="doc-001",
            name="김철수",
            hospital_id="hosp-001",
            department="내과",
            specialty=("소화기내과", "간담도내과"),
            education=("서울대학교 의과대학", "서울대학교병원 전공의"),
            career=("서울대학교병원 교수",),
            consultation_hours=(
                ConsultationHours(
                    day="월요일", start_time="09:00", end_time="17:00"
                ),
            ),
        )

        data = original.to_dict()
        restored = Doctor.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.specialty == original.specialty
        assert restored.education == original.education


class TestHospital:
    """Tests for Hospital model."""

    def test_create_hospital(self) -> None:
        """Test creating a hospital instance."""
        hospital = Hospital(
            id="hosp-001",
            name="서울대학교병원",
            address="서울특별시 종로구 대학로 101",
            phone="02-2072-2114",
            website="https://www.snuh.org",
            departments=("내과", "외과", "소아과"),
            type="university",
            region="서울",
        )

        assert hospital.id == "hosp-001"
        assert hospital.name == "서울대학교병원"
        assert hospital.type == "university"
        assert "내과" in hospital.departments

    def test_hospital_immutability(self) -> None:
        """Test that hospital is immutable."""
        hospital = Hospital(
            id="hosp-001",
            name="서울대학교병원",
            address="서울특별시 종로구 대학로 101",
        )

        with pytest.raises(AttributeError):
            hospital.name = "연세세브란스병원"  # type: ignore

    def test_hospital_to_dict(self) -> None:
        """Test converting hospital to dictionary."""
        hospital = Hospital(
            id="hosp-001",
            name="서울대학교병원",
            address="서울특별시 종로구 대학로 101",
            departments=("내과", "외과"),
        )

        data = hospital.to_dict()

        assert data["id"] == "hosp-001"
        assert data["name"] == "서울대학교병원"
        assert data["departments"] == ["내과", "외과"]

    def test_hospital_from_dict(self) -> None:
        """Test creating hospital from dictionary."""
        data = {
            "id": "hosp-001",
            "name": "서울대학교병원",
            "address": "서울특별시 종로구 대학로 101",
            "departments": ["내과", "외과"],
            "type": "university",
        }

        hospital = Hospital.from_dict(data)

        assert hospital.id == "hosp-001"
        assert hospital.name == "서울대학교병원"
        assert hospital.departments == ("내과", "외과")
        assert hospital.type == "university"

    def test_hospital_roundtrip(self) -> None:
        """Test that to_dict and from_dict are reversible."""
        original = Hospital(
            id="hosp-001",
            name="서울대학교병원",
            address="서울특별시 종로구 대학로 101",
            phone="02-2072-2114",
            departments=("내과", "외과", "소아과"),
            type="university",
            region="서울",
        )

        data = original.to_dict()
        restored = Hospital.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.departments == original.departments
