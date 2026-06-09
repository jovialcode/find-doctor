# admin-api — Spec v0.0.1

## Overview

데이터 수집 파이프라인 운영 관리용 FastAPI 서비스 (port 8500). 사이트 등록, 크롤링 룰 관리, 잡 스케줄링, 시스템 모니터링 기능을 제공한다.

## Directory Structure

```
admin-api/src/admin_api/
├── app.py            # FastAPI 앱 생성, 라우터 등록, lifespan
├── routers/
│   ├── sites.py      # 사이트 CRUD
│   ├── rules.py      # YAML 룰 파일 관리
│   ├── jobs.py       # 크롤링 잡 스케줄링/모니터링
│   └── monitoring.py # 시스템 상태 및 통계
└── schemas/
    ├── site.py       # Site 요청/응답 스키마
    ├── rule.py       # Rule 요청/응답 스키마
    └── job.py        # Job 요청/응답 스키마
```

## Application

```python
def create_app() -> FastAPI:
    # CORS 미들웨어 등록
    # 라우터 등록 (/sites, /rules, /jobs, /monitoring)
    # GET /health 엔드포인트
```

## API Endpoints

### Sites — `/sites`

사이트 등록 및 활성화 관리. (현재 인메모리 저장소, DB 연동 예정)

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/sites` | 사이트 목록 조회 (pagination, enabled 필터) |
| `GET` | `/sites/{site_id}` | 단일 사이트 조회 |
| `POST` | `/sites` | 사이트 등록 |
| `PUT` | `/sites/{site_id}` | 사이트 수정 |
| `DELETE` | `/sites/{site_id}` | 사이트 삭제 |
| `POST` | `/sites/{site_id}/enable` | 사이트 활성화 |
| `POST` | `/sites/{site_id}/disable` | 사이트 비활성화 |

### Rules — `/rules`

`rules/hospitals/` 디렉토리의 YAML 파일 관리.

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/rules` | 룰 파일 목록 (메타데이터 포함) |
| `GET` | `/rules/{rule_id}` | 룰 파일 전체 내용 조회 |
| `POST` | `/rules/validate` | YAML 룰 유효성 검사 |
| `POST` | `/rules/{rule_id}` | 룰 파일 생성/수정 |
| `DELETE` | `/rules/{rule_id}` | 룰 파일 삭제 |

### Jobs — `/jobs`

Celery 태스크 enqueue 및 JobLog 관리.

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/jobs` | 잡 목록 (status, site_id 필터) |
| `GET` | `/jobs/{job_id}` | 잡 상세 조회 |
| `POST` | `/jobs` | 새 크롤링 잡 생성 및 enqueue |
| `POST` | `/jobs/{job_id}/cancel` | 잡 취소 |
| `POST` | `/jobs/{job_id}/retry` | 실패 잡 재시도 |
| `DELETE` | `/jobs/{job_id}` | 잡 로그 삭제 |

### Monitoring — `/monitoring`

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/monitoring/status` | 시스템 컴포넌트 헬스 상태 |
| `GET` | `/monitoring/stats` | 잡 통계 (total/completed/failed/running/pending) |
| `GET` | `/monitoring/crawl-history` | 최근 잡 이력 (site_id 필터) |
| `GET` | `/monitoring/errors` | 최근 실패 잡 목록 |
| `GET` | `/monitoring/sites/{site_id}/stats` | 사이트별 통계 |
| `GET` | `/monitoring/alerts` | 활성 알럿 (최근 실패 기반) |

## Schemas

### Job

```python
class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

@dataclass
class JobCreate:
    site_id: str
    target_name: str | None = None

@dataclass
class JobResponse:
    id: str
    celery_task_id: str
    site_id: str
    target_name: str | None
    status: JobStatus
    started_at: datetime | None
    completed_at: datetime | None
    urls_crawled: int
    urls_failed: int
    items_parsed: int
    error_message: str | None
    created_at: datetime
```

### Site

```python
@dataclass
class SiteCreate:
    id: str
    name: str
    base_url: str
    enabled: bool = True

@dataclass
class SiteResponse:
    id: str
    name: str
    base_url: str
    enabled: bool
```

### Rule

```python
@dataclass
class RuleResponse:
    id: str
    name: str
    base_url: str
    enabled: bool
    file_path: str
    targets_count: int

@dataclass
class RuleValidationResponse:
    valid: bool
    errors: list[str]
```

## Dependencies

```toml
core                        # 내부 패키지
collector                   # 내부 패키지 (task enqueue)
fastapi >= 0.109.0
uvicorn[standard] >= 0.27.0
python-multipart >= 0.0.9
pyyaml >= 6.0.0
```

## Package Dependencies

```
admin-api → collector → core
admin-api → core
```

## Known Limitations (v0.0.1)

- 사이트 데이터가 인메모리 저장소에만 보관됨 (재시작 시 초기화)
- 재시작 후 DB 연동 필요
