# collector

## Overview

병원/의사 데이터를 웹에서 수집하는 크롤러 패키지.
HTTP, 브라우저, AI Agent 세 가지 전략을 지원하며, YAML 룰 파일로 사이트별 크롤링 동작을 정의한다. 
Celery를 통해 비동기 분산 처리한다.

**중요**
작업은 SYSTEM_DESIGN.md를 꼭 참조한다.
작업의 task는 specs/*.md를 보고 작업을 진행한다.

## Directory Structure

```
collector/src/collector/
├── crawler/
│   ├── base.py            # BaseCrawler (ABC), CrawlResult, CrawlRequest
│   ├── http_crawler.py    # httpx 기반 HTTP 크롤러
│   ├── browser_crawler.py # Playwright 기반 브라우저 크롤러
│   └── ai_agent_crawler.py# browser-use + Claude 기반 AI 크롤러
├── parser/
│   ├── base.py            # BaseParser (ABC), ParseResult, FieldRule, ParserRule
│   ├── selector_parser.py # CSS/XPath 셀렉터 파서 (parsel)
│   └── registry.py        # ParserRegistry
├── rules/
│   ├── models.py          # SiteRule, TargetRule, CrawlerConfig, PaginationConfig 등
│   ├── loader.py          # RuleLoader (YAML → SiteRule)
│   └── validator.py       # RuleValidator (JSON Schema)
├── tasks/
│   ├── crawl_task.py      # crawl_target(), crawl_site()
│   └── parse_task.py      # parse_crawled_data(), parse_all_targets()
└── worker/
    ├── celery_app.py       # Celery 앱 설정 및 큐 라우팅
    ├── tasks.py            # Celery task 래퍼 + JobLog 시그널 핸들러
    └── enqueue.py          # enqueue_all_sites(), wait_for_tasks()
```

## Crawler

### BaseCrawler (ABC)

모든 크롤러의 공통 인터페이스.

```python
class BaseCrawler:
    async def fetch(self, request: CrawlRequest) -> CrawlResult: ...
    async def fetch_many(self, requests: list[CrawlRequest]) -> list[CrawlResult]: ...
    async def close(self) -> None: ...
```

- Rate limiting, timeout, retry 설정 포함
- `async with` 컨텍스트 매니저 지원

### CrawlResult

```python
@dataclass(frozen=True)
class CrawlResult:
    url: str
    html: str | None
    status_code: int
    headers: dict
    crawled_at: datetime
    error: str | None

    @property
    def is_success(self) -> bool: ...
```

### HttpCrawler

- `httpx.AsyncClient` 사용
- 세마포어 기반 동시성 제어
- Exponential backoff 재시도

### BrowserCrawler

- `playwright` 사용 (Chromium)
- JavaScript 렌더링 필요 페이지 처리
- `wait_for_selector` 로딩 대기 지원

### AIAgentCrawler

- `browser-use` + `langchain-anthropic` (Claude) 사용
- 자연어 추출 프롬프트로 구조화 데이터 추출
- 페이지 네비게이션을 AI가 자율 수행

## Parser

### SelectorParser

CSS/XPath 셀렉터 기반 HTML 파서.

**지원 필드 타입:**

| type | 설명 |
|------|------|
| `text` | 텍스트 추출 |
| `text_list` | 텍스트 목록 추출 |
| `url` | href 속성 추출 |
| `attribute` | 지정 attribute 추출 |
| `html` | 내부 HTML 추출 |

**지원 transform:**

`strip`, `regex_extract`, `regex_replace`, `split`, `join`, `lowercase`, `uppercase`, `prefix`, `suffix`

### ParseResult

```python
@dataclass(frozen=True)
class ParseResult:
    source_url: str
    data: tuple[dict, ...]
    parsed_at: datetime
    errors: tuple[str, ...]

    @property
    def is_success(self) -> bool: ...

    @property
    def item_count(self) -> int: ...
```

## Rules (YAML)

사이트별 크롤링 규칙은 `rules/hospitals/*.yaml` 에 정의.

### SiteRule 구조

```yaml
site:
  id: "example-hospital"
  name: "예시 병원"
  base_url: "https://example.com"
  enabled: true
  crawler:
    type: http          # http | browser | ai_agent
    rate_limit: 1.0     # 초당 요청 수
    timeout: 30
    headers: {}
    ai_extraction_prompt: "..."  # ai_agent 전용
  targets:
    - name: "doctors"
      url_pattern: "/doctors"
      selectors:
        container: ".doctor-list"
        item: ".doctor-item"
        fields:
          - name: name
            selector: ".name"
            type: text
          - name: specialty
            selector: ".specialty"
            type: text_list
      pagination:
        type: page_param    # page_param | next_button | infinite_scroll
        param_name: "page"
        max_pages: 10
```

### RuleLoader

YAML 파일 → `SiteRule` 객체 변환. `rules_dir` 디렉토리에서 모든 `.yaml` 파일 로드.

### RuleValidator

JSON Schema 기반 유효성 검사 + 시맨틱 검사 (selector 형식, pagination 설정 등).


## Tasks

### crawl_task.py

- `crawl_target(rule, target, output_dir)` — 단일 타겟 크롤링
- `crawl_site(rule, output_dir)` — 사이트 전체 크롤링 (모든 타겟)

### parse_task.py

- `parse_crawled_data(rule, target, input_dir, output_dir)` — 크롤링된 HTML 파싱
- `parse_all_targets(rule, input_dir, output_dir)` — 사이트 전체 파싱

## Celery Worker

### 큐 구성

| 큐 이름 | 목적 | 워커 수 |
|---------|------|---------|
| `scraper.http` | HTTP 크롤러 태스크 | 4 |
| `scraper.browser` | 브라우저 크롤러 태스크 | 4 |
| `scraper.ai_agent` | AI Agent 크롤러 태스크 | 2 |

### Celery Tasks (worker/tasks.py)

| 태스크 | 큐 | 설명 |
|--------|-----|------|
| `crawl_site_task` | `scraper.http` | HTTP 크롤링 |
| `crawl_site_browser_task` | `scraper.browser` | 브라우저 크롤링 |
| `crawl_site_ai_task` | `scraper.ai_agent` | AI Agent 크롤링 |
| `parse_site_task` | `scraper.http` | 파싱 태스크 |

**Celery 시그널 핸들러:**
- `task_prerun` → `JobLog` status = `running`
- `task_postrun` → `JobLog` status = `completed`
- `task_failure` → `JobLog` status = `failed`, error_message 기록

### enqueue.py

```python
def enqueue_all_sites(rules_dir: str, output_dir: str) -> list[str]: ...
def enqueue_parse_all_sites(rules_dir: str, input_dir: str, output_dir: str) -> list[str]: ...
def wait_for_tasks(task_ids: list[str], timeout: int) -> list[dict]: ...
```

Airflow DAG에서 직접 호출하여 Celery 큐에 작업을 enqueue하고 완료를 대기한다.

## Dependencies

```toml
core                        # 내부 패키지
httpx >= 0.27.0
playwright >= 1.40.0
beautifulsoup4 >= 4.12.0
lxml >= 5.0.0
parsel >= 1.8.0
tenacity >= 8.0.0
anyio >= 4.0.0
pyyaml >= 6.0.0
jsonschema >= 4.20.0
celery[redis] >= 5.3.0
flower >= 2.0.0
browser-use >= 0.1.0
langchain-anthropic >= 0.3.0
```

## Package Dependencies

```
collector → core
```
