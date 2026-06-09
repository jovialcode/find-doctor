# client-api — Spec v0.0.1

## Overview

수집된 병원/의사 데이터를 조회하는 읽기 전용 FastAPI 서비스 (port 8501). 검색, 필터링, 집계 엔드포인트를 제공한다.

## Directory Structure

```
client-api/src/client_api/
├── app.py            # FastAPI 앱 생성, 라우터 등록, lifespan
├── routers/
│   ├── doctors.py    # 의사 조회 엔드포인트
│   ├── hospitals.py  # 병원 조회 엔드포인트
│   └── search.py     # 통합 검색 엔드포인트
├── schemas/
│   ├── doctor.py     # Doctor 응답 스키마
│   ├── hospital.py   # Hospital 응답 스키마
│   └── search.py     # Search 요청/응답 스키마
└── services/
    └── __init__.py   # (예정) 비즈니스 로직 서비스 레이어
```

## Application

```python
def create_app() -> FastAPI:
    # CORS 미들웨어 (읽기 전용 메서드만 허용)
    # 라우터 등록 (/doctors, /hospitals, /search)
    # GET /health 엔드포인트
```

lifespan에서 Redis 연결 초기화 (캐싱용, 현재 스텁).

## API Endpoints

### Doctors — `/doctors`

| Method | Path | 쿼리 파라미터 | 설명 |
|--------|------|-------------|------|
| `GET` | `/doctors` | `hospital_id`, `department`, `specialty`, `region`, `is_accepting_new`, `skip`, `limit` | 의사 목록 조회 |
| `GET` | `/doctors/{doctor_id}` | — | 의사 상세 조회 |
| `GET` | `/doctors/hospital/{hospital_id}` | `department`, `skip`, `limit` | 병원별 의사 목록 |
| `GET` | `/doctors/department/{department}` | `skip`, `limit` | 진료과별 의사 목록 |

### Hospitals — `/hospitals`

| Method | Path | 쿼리 파라미터 | 설명 |
|--------|------|-------------|------|
| `GET` | `/hospitals` | `type`, `region`, `department`, `skip`, `limit` | 병원 목록 조회 |
| `GET` | `/hospitals/{hospital_id}` | — | 병원 상세 조회 |
| `GET` | `/hospitals/region/{region}` | `type`, `skip`, `limit` | 지역별 병원 목록 |
| `GET` | `/hospitals/{hospital_id}/departments` | — | 병원 진료과 목록 |

### Search — `/search`

| Method | Path | 쿼리 파라미터 | 설명 |
|--------|------|-------------|------|
| `GET` | `/search` | `q`, `type` (all/doctor/hospital), `skip`, `limit` | 의사+병원 통합 검색 |
| `GET` | `/search/suggest` | `q`, `limit` | 검색어 자동완성 |

**검색 스코어링 기준:**
- 이름 prefix 일치: 높은 점수
- 이름 포함 일치: 중간 점수
- 전문분야/진료과 일치: 추가 점수
- 지역 일치: 추가 점수

## Schemas

### DoctorResponse

```python
@dataclass
class ConsultationHoursSchema:
    day: str
    start_time: str
    end_time: str
    note: str | None

@dataclass
class DoctorResponse:
    id: str
    name: str
    hospital_id: str
    department: str
    specialty: list[str]
    photo_url: str | None
    education: list[str]
    career: list[str]
    certifications: list[str]
    publications: list[str]
    awards: list[str]
    consultation_hours: list[ConsultationHoursSchema]
    is_accepting_new: bool
    booking_url: str | None
    phone: str | None
    source_url: str
    collected_at: datetime

@dataclass
class DoctorListResponse:
    items: list[DoctorResponse]
    total: int
    skip: int
    limit: int
```

### HospitalResponse

```python
@dataclass
class HospitalResponse:
    id: str
    name: str
    address: str
    phone: str | None
    website: str | None
    departments: list[str]
    type: str
    region: str
    collected_at: datetime

@dataclass
class HospitalListResponse:
    items: list[HospitalResponse]
    total: int
    skip: int
    limit: int
```

### SearchResponse

```python
@dataclass
class SearchResult:
    type: str          # "doctor" | "hospital"
    id: str
    name: str
    description: str
    score: float
    data: DoctorResponse | HospitalResponse

@dataclass
class SearchResponse:
    query: str
    items: list[SearchResult]
    total: int
    skip: int
    limit: int
```

## Dependencies

```toml
core                        # 내부 패키지
fastapi >= 0.109.0
uvicorn[standard] >= 0.27.0
redis >= 5.0.0
```

## Package Dependencies

```
client-api → core
```

## Known Limitations (v0.0.1)

- 의사/병원 데이터가 인메모리 저장소에만 보관됨 (collector 파싱 결과 DB 연동 미완성)
- Redis 캐싱 미구현 (lifespan 스텁만 존재)
- 검색이 단순 in-memory 스캔 방식 (Elasticsearch 등 도입 예정)
