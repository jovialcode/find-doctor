# core — Spec v0.0.1

## Overview

모든 패키지가 공유하는 기반 라이브러리. 데이터 모델, DB 레포지토리, 환경 설정을 제공한다.

## Directory Structure

```
core/src/core/
├── models/
│   ├── doctor.py       # Doctor, ConsultationHours 모델
│   ├── hospital.py     # Hospital 모델
│   └── job_log.py      # JobLog 모델
├── config/
│   └── settings.py     # Pydantic Settings (환경변수 기반)
└── database/
    ├── repository.py         # Repository Protocol + BaseRepository (ABC)
    ├── job_log_repository.py # SQLAlchemy 기반 JobLog CRUD
    └── migrations/
        └── 001_create_job_logs.sql
```

## Data Models

모든 모델은 `@dataclass(frozen=True)` 기반의 불변 객체.

### Doctor

| 필드 | 타입 | 설명 |
|------|------|------|
| id | str | UUID |
| name | str | 의사 이름 |
| hospital_id | str | 소속 병원 ID |
| department | str | 진료과 |
| specialty | tuple[str, ...] | 전문 분야 목록 |
| photo_url | str \| None | 프로필 사진 URL |
| education | tuple[str, ...] | 학력 |
| career | tuple[str, ...] | 경력 |
| certifications | tuple[str, ...] | 자격증 |
| publications | tuple[str, ...] | 논문/저서 |
| awards | tuple[str, ...] | 수상 내역 |
| consultation_hours | tuple[ConsultationHours, ...] | 진료 시간 |
| is_accepting_new | bool | 신규 환자 수락 여부 |
| booking_url | str \| None | 예약 URL |
| phone | str \| None | 전화번호 |
| source_url | str | 크롤링 출처 URL |
| collected_at | datetime | 수집 시각 |

### Hospital

| 필드 | 타입 | 설명 |
|------|------|------|
| id | str | UUID |
| name | str | 병원 이름 |
| address | str | 주소 |
| phone | str \| None | 전화번호 |
| website | str \| None | 웹사이트 URL |
| departments | tuple[str, ...] | 진료과 목록 |
| type | str | 병원 유형 (상급종합, 종합, 의원 등) |
| region | str | 지역 |
| collected_at | datetime | 수집 시각 |

### JobLog

크롤링 작업 실행 이력 추적용 모델.

| 필드 | 타입 | 설명 |
|------|------|------|
| id | str | UUID |
| celery_task_id | str | Celery task ID |
| site_id | str | 대상 사이트 ID |
| target_name | str \| None | 대상 타겟명 |
| status | str | pending / running / completed / failed / cancelled |
| started_at | datetime \| None | 시작 시각 |
| completed_at | datetime \| None | 완료 시각 |
| urls_crawled | int | 크롤링한 URL 수 |
| urls_failed | int | 실패한 URL 수 |
| items_parsed | int | 파싱된 항목 수 |
| error_message | str \| None | 오류 메시지 |
| result_summary | dict \| None | 결과 요약 |
| created_at | datetime | 레코드 생성 시각 |

## Configuration

`Settings` 클래스는 `pydantic_settings.BaseSettings` 기반이며 `get_settings()`로 LRU 캐싱된 싱글톤을 반환한다.

| 섹션 | 주요 변수 | 설명 |
|------|----------|------|
| Database | `DATABASE_URL` | PostgreSQL 연결 문자열 |
| Redis | `REDIS_URL` | Redis 연결 문자열 |
| Celery | `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Celery 브로커/백엔드 |
| MinIO | `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | 오브젝트 스토리지 |
| GCP | `GCP_PROJECT`, `GCP_REGION` | GCP 프로젝트 설정 |
| AI Agent | `ANTHROPIC_API_KEY` | Claude API 키 |
| Crawler | `CRAWLER_RATE_LIMIT`, `CRAWLER_TIMEOUT` | 크롤러 기본값 |

## Repositories

### Repository (Protocol)

```python
class Repository(Protocol):
    def find_by_id(self, id: str) -> dict | None: ...
    def save(self, entity: dict) -> dict: ...
    def delete(self, id: str) -> bool: ...
```

### BaseRepository (ABC)

- `find_by_id()`, `find_all()`, `save()`, `save_many()`, `delete()` 제공
- 인메모리 기본 구현 (하위 클래스에서 DB 연동 가능)

### DoctorRepository

- `search(query)` — 이름/전문분야 검색
- `find_by_hospital(hospital_id)` — 병원별 조회
- `find_by_department(department)` — 진료과별 조회

### HospitalRepository

- `search(query)` — 이름 검색
- `find_by_region(region)` — 지역별 조회
- `find_by_type(type)` — 유형별 조회

### JobLogRepository

SQLAlchemy 기반. `job_logs` 테이블에 직접 읽기/쓰기.

- `create(job_log)` — 새 잡 로그 생성
- `update_status(id, status, ...)` — 상태 업데이트
- `find_by_id(id)` — ID 조회
- `find_by_celery_task_id(task_id)` — Celery task ID로 조회
- `find_by_site_id(site_id)` — 사이트별 조회
- `find_recent(limit)` — 최근 잡 목록
- `find_recent_errors(limit)` — 최근 실패 잡 목록
- `count_by_status()` — 상태별 카운트

## Dependencies

```toml
pydantic >= 2.5.0
pydantic-settings >= 2.1.0
pyyaml >= 6.0.0
sqlalchemy >= 2.0.0
psycopg2-binary >= 2.9.0
structlog >= 24.0.0
python-dotenv >= 1.0.0
google-cloud-bigquery >= 3.0.0
google-cloud-storage >= 2.0.0
google-cloud-firestore >= 2.0.0
```

## Package Dependencies

없음 (모든 패키지의 최하위 의존성)
