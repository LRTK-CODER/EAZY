# EAZY 백엔드 로직 분석 보고서

> **분석 일자:** 2026-01-10
> **분석 방법:** Sequential-Thinking MCP 기반 다중 전문가 토론
> **참여 전문가:** 시스템 아키텍트, 데이터베이스 아키텍트, API 설계 전문가, 도메인 전문가, 인프라 엔지니어, 보안 전문가
> **분석 대상:** `backend/app/` 전체 소스 코드

---

## 1. 백엔드 아키텍처 개요

### 1.1 전체 구조

```
backend/
├── app/
│   ├── api/v1/endpoints/     # API 엔드포인트
│   │   ├── project.py        # 프로젝트 + 타겟 API
│   │   └── task.py           # 스캔/태스크 API
│   ├── core/                 # 인프라 설정
│   │   ├── config.py         # 환경 설정
│   │   ├── db.py             # 데이터베이스 연결
│   │   ├── queue.py          # TaskManager (Redis)
│   │   └── redis.py          # Redis 클라이언트
│   ├── models/               # 데이터 모델
│   │   ├── project.py        # Project 모델
│   │   ├── target.py         # Target 모델
│   │   ├── task.py           # Task 모델
│   │   └── asset.py          # Asset + Discovery 모델
│   ├── services/             # 비즈니스 로직
│   │   ├── project_service.py
│   │   ├── target_service.py
│   │   ├── task_service.py
│   │   ├── asset_service.py
│   │   └── crawler_service.py
│   ├── utils/
│   │   └── url_parser.py     # URL 파싱 유틸
│   ├── main.py               # FastAPI 앱 진입점
│   └── worker.py             # 비동기 워커 (307 lines)
├── alembic/                  # DB 마이그레이션
└── tests/                    # 테스트 코드
```

### 1.2 아키텍처 레이어

```
┌─────────────────────────────────────────────────────┐
│                   API Layer                         │
│         (FastAPI Endpoints + CORS)                  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 Service Layer                       │
│  (ProjectService, TaskService, AssetService, etc.)  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  Data Layer                         │
│         (SQLModel + AsyncPG + PostgreSQL)           │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Infrastructure Layer                   │
│       (Redis Queue + Worker + Playwright)           │
└─────────────────────────────────────────────────────┘
```

### 1.3 데이터 흐름

```
Client Request
      │
      ▼
┌─────────────┐      ┌─────────────┐
│  FastAPI    │ ────→│   Service   │
│  Endpoint   │      │   Layer     │
└─────────────┘      └──────┬──────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │PostgreSQL│  │  Redis   │  │  Worker  │
        │   (DB)   │  │ (Queue)  │  │(Crawler) │
        └──────────┘  └──────────┘  └──────────┘
```

---

## 2. 전문가별 상세 분석

### 2.1 시스템 아키텍트 분석

**핵심 컴포넌트:**

| 컴포넌트 | 기술 | 역할 |
|----------|------|------|
| FastAPI App | FastAPI + Uvicorn | HTTP 서버, 라우팅 |
| 비동기 DB | SQLModel + AsyncPG | PostgreSQL 비동기 ORM |
| Redis Queue | redis.asyncio | 작업 큐 관리 |
| Worker | asyncio | 크롤링 작업 실행 |
| Crawler | Playwright | 웹 페이지 크롤링 |

**강점:**
- 완전 비동기 설계 (asyncio 기반)
- 작업-워커 분리로 장시간 작업 처리 가능
- Task 취소 기능 구현 (Redis flag 기반)

---

### 2.2 데이터베이스 아키텍트 분석

**ERD (Entity Relationship Diagram):**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Project    │ 1:N │   Target    │ 1:N │    Task     │
│─────────────│────→│─────────────│────→│─────────────│
│ id (PK)     │     │ id (PK)     │     │ id (PK)     │
│ name        │     │ project_id  │     │ project_id  │
│ description │     │ name        │     │ target_id   │
│ is_archived │     │ url         │     │ type        │
│ archived_at │     │ scope       │     │ status      │
│ created_at  │     │ description │     │ result      │
│ updated_at  │     │ created_at  │     │ started_at  │
└─────────────┘     │ updated_at  │     │ completed_at│
                    └─────────────┘     └─────────────┘
                          │ 1:N              │ 1:N
                          ↓                  ↓
                    ┌─────────────┐     ┌─────────────────┐
                    │   Asset     │←────│ AssetDiscovery  │
                    │─────────────│     │─────────────────│
                    │ id (PK)     │     │ id (PK)         │
                    │ target_id   │     │ task_id (FK)    │
                    │ content_hash│     │ asset_id (FK)   │
                    │ type        │     │ parent_asset_id │
                    │ source      │     │ discovered_at   │
                    │ method      │     └─────────────────┘
                    │ url/path    │
                    │ request_spec│ ← JSONB
                    │ response_spec│← JSONB
                    │ parameters  │ ← JSONB
                    └─────────────┘
```

**주요 ENUM 타입:**

```python
# Target Scope
class TargetScope(str, Enum):
    DOMAIN = "DOMAIN"       # 전체 도메인
    SUBDOMAIN = "SUBDOMAIN" # 서브도메인 포함
    URL_ONLY = "URL_ONLY"   # 특정 URL만

# Task Status
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Asset Type
class AssetType(str, Enum):
    URL = "url"
    FORM = "form"
    XHR = "xhr"

# Asset Source
class AssetSource(str, Enum):
    HTML = "html"
    JS = "js"
    NETWORK = "network"
    DOM = "dom"
```

**강점:**
1. CASCADE 삭제로 데이터 정합성 유지
2. JSONB 필드로 HTTP 데이터 유연하게 저장
3. Soft Delete (is_archived) 지원
4. content_hash로 Asset 중복 방지

**개선 필요:**
1. TargetScope ENUM이 실제 로직에서 미활용
2. Task.result가 TEXT - JSONB로 변경 고려

---

### 2.3 API 설계 전문가 분석

**API 엔드포인트 전체 목록:**

#### Projects API

| Method | Endpoint | 기능 | 응답 |
|--------|----------|------|------|
| POST | `/api/v1/projects/` | 프로젝트 생성 | 201 |
| GET | `/api/v1/projects/` | 목록 조회 | 200 |
| GET | `/api/v1/projects/{id}` | 단일 조회 | 200/404 |
| PATCH | `/api/v1/projects/{id}` | 수정 | 200/404 |
| DELETE | `/api/v1/projects/{id}` | 삭제 (soft/hard) | 204/404 |
| PATCH | `/api/v1/projects/{id}/restore` | 복원 | 204/404 |

#### Targets API

| Method | Endpoint | 기능 | 응답 |
|--------|----------|------|------|
| POST | `/api/v1/projects/{pid}/targets/` | 타겟 생성 | 201 |
| GET | `/api/v1/projects/{pid}/targets/` | 목록 조회 | 200 |
| GET | `/api/v1/projects/{pid}/targets/{tid}` | 단일 조회 | 200/404 |
| PATCH | `/api/v1/projects/{pid}/targets/{tid}` | 수정 | 200/404 |
| DELETE | `/api/v1/projects/{pid}/targets/{tid}` | 삭제 | 204/404 |
| GET | `/api/v1/projects/{pid}/targets/{tid}/assets` | Asset 목록 | 200 |

#### Tasks API

| Method | Endpoint | 기능 | 응답 |
|--------|----------|------|------|
| POST | `/api/v1/projects/{pid}/targets/{tid}/scan` | 스캔 시작 | 202 |
| GET | `/api/v1/tasks/{id}` | 상태 조회 | 200/404 |
| GET | `/api/v1/tasks/{id}/assets` | Task Asset | 200 |
| POST | `/api/v1/tasks/{id}/cancel` | 취소 | 200/400/404 |
| GET | `/api/v1/targets/{tid}/latest-task` | 최신 Task | 200/404 |

**Query Parameters:**

```
GET /api/v1/projects/
  ?skip=0          # 페이지네이션 오프셋
  &limit=100       # 페이지 크기
  &archived=false  # 아카이브 필터

DELETE /api/v1/projects/{id}
  ?permanent=false # true: 영구 삭제, false: 아카이브
```

**강점:**
- RESTful 컨벤션 준수
- 적절한 HTTP 상태 코드 (202 for async)
- Soft/Hard 삭제 구분

**개선 필요:**
- `/targets/{tid}/latest-task` 경로 일관성
- Cursor 기반 페이지네이션 고려

---

### 2.4 도메인 전문가 분석

**핵심 비즈니스 플로우:**

```
1. 프로젝트 생성
   └─→ Project 레코드 생성

2. 타겟 등록
   └─→ Target 레코드 생성 (URL, Scope 지정)

3. 스캔 시작 (POST /scan)
   ├─→ Task 레코드 생성 (status: PENDING)
   └─→ Redis Queue에 작업 등록

4. Worker 처리
   ├─→ Queue에서 작업 꺼내기 (LPOP)
   ├─→ Task 상태 → RUNNING
   ├─→ Playwright 크롤링 실행
   │   ├─→ 페이지 로드 (networkidle)
   │   ├─→ HTTP 요청/응답 인터셉트
   │   └─→ <a> 태그 링크 수집
   ├─→ Asset 저장 (중복 체크)
   └─→ Task 상태 → COMPLETED/FAILED

5. 취소 처리
   ├─→ Redis에 cancel flag 설정
   └─→ Worker가 5초마다 확인 후 중단
```

**서비스 레이어 책임 분리:**

| Service | 핵심 메서드 | 책임 |
|---------|-------------|------|
| ProjectService | create, get, update, archive, restore | 프로젝트 CRUD + 아카이브 |
| TargetService | create, get, update, delete | 타겟 CRUD (CASCADE 삭제) |
| TaskService | create_scan_task, cancel_task, get_latest_task | 스캔 작업 관리 |
| AssetService | process_asset | Asset 중복 처리 + HTTP 저장 |
| CrawlerService | crawl | Playwright 크롤링 |

**Asset 중복 처리 로직:**

```python
def _generate_content_hash(self, method: str, url: str) -> str:
    identifier = f"{method.upper()}:{url}"
    return hashlib.sha256(identifier.encode()).hexdigest()
```

---

### 2.5 인프라 엔지니어 분석

**Worker 아키텍처:**

```python
# worker.py - 메인 루프
async def run_worker():
    while True:
        async with async_session() as session:
            processed = await process_one_task(session, task_manager)
            if not processed:
                await asyncio.sleep(1)  # 폴링 간격 1초
```

**Redis Queue 메커니즘:**

```
Queue Key: "eazy_task_queue"

작업 추가 (RPUSH):
┌─────────────────────────────────────────┐
│ task1 → task2 → task3 → [new task]      │
└─────────────────────────────────────────┘

작업 꺼내기 (LPOP):
┌─────────────────────────────────────────┐
│ [pop] ← task1 → task2 → task3           │
└─────────────────────────────────────────┘
```

**Task Payload 구조:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "db_task_id": 123,
  "type": "crawl",
  "project_id": 1,
  "target_id": 1,
  "timestamp": "2026-01-10T12:00:00"
}
```

**취소 메커니즘:**

```
1. API 호출: POST /tasks/{id}/cancel
   │
   ├─→ Redis: SET task:{id}:cancel = "1" (TTL: 3600s)
   └─→ DB: Task.status = CANCELLED

2. Worker 처리 (5초마다 확인)
   │
   └─→ if cancel_flag exists:
       ├─→ 작업 중단
       ├─→ 진행 상황 저장
       └─→ Redis flag 삭제
```

**강점:**
- 간단하고 효과적인 Redis 큐
- Cooperative cancellation 구현

**개선 필요:**
- 단일 Worker (스케일 아웃 미고려)
- 재시도 로직 없음
- Dead Letter Queue 없음

---

### 2.6 보안 전문가 분석

**현재 보안 상태:**

| 항목 | 현재 상태 | 위험도 |
|------|----------|--------|
| CORS | `origins = ["*"]` | **높음** |
| 인증 | 미구현 | **높음** |
| 인가 | 미구현 | **높음** |
| Secret 관리 | 하드코딩 기본값 | **높음** |
| SQL Injection | SQLModel (안전) | 낮음 |
| Input Validation | Pydantic | 낮음 |

**상세 취약점:**

1. **CORS 정책** (`main.py:12`)
```python
origins = ["*"]  # Allow all origins for MVP
```
- XSS 공격에 취약
- 프로덕션 전 반드시 제한 필요

2. **Secret Key** (`config.py:22`)
```python
SECRET_KEY: str = "CHANGE_THIS_TO_A_SECURE_KEY_IN_PRODUCTION"
```
- 기본값 노출 위험
- .env 파일로 관리 권장

3. **SSL 검증 비활성화** (`crawler_service.py:31`)
```python
context = await browser.new_context(ignore_https_errors=True)
```
- MITM 공격 가능성
- 내부 네트워크에서만 사용 권장

4. **인가 없는 리소스 접근**
- 모든 프로젝트/타겟 접근 가능
- 다른 사용자 스캔 취소 가능

**권장 보안 조치:**

| 우선순위 | 조치 | 설명 |
|----------|------|------|
| 1 | JWT 인증 | FastAPI OAuth2 + JWT |
| 2 | RBAC | 역할 기반 접근 제어 |
| 3 | CORS 제한 | 화이트리스트 방식 |
| 4 | Rate Limiting | slowapi 라이브러리 |
| 5 | URL 화이트리스트 | 스캔 대상 제한 |

---

## 3. 코드 품질 분석

### 3.1 파일별 라인 수

| 파일 | 라인 수 | 평가 |
|------|---------|------|
| `worker.py` | 307 | **분리 필요** |
| `project.py` (endpoint) | 202 | 적절 |
| `asset_service.py` | 152 | 적절 |
| `crawler_service.py` | 164 | 적절 |
| `task_service.py` | 135 | 적절 |
| `task.py` (endpoint) | 114 | 적절 |
| `project_service.py` | 92 | 적절 |
| `target_service.py` | 64 | 적절 |

### 3.2 코드 중복

```python
# utc_now() 함수가 4개 파일에 중복 정의
# - project.py
# - target.py
# - task.py
# - asset.py

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

**권장:** `app/utils/datetime.py`로 통합

### 3.3 테스트 커버리지

```
tests/
├── api/                 # API 테스트
│   ├── test_health.py
│   ├── test_projects.py
│   ├── test_targets.py
│   ├── test_targets_mgmt.py
│   ├── test_tasks.py
│   ├── test_task_cancel.py
│   └── test_latest_task.py
├── core/                # 코어 테스트
│   ├── test_migration_cascade.py
│   ├── test_task_manager.py
│   └── test_worker.py
├── integration/         # 통합 테스트
│   ├── test_full_flow.py
│   ├── test_worker_http.py
│   └── test_worker_params.py
├── models/              # 모델 테스트
│   └── test_task_timestamps.py
├── services/            # 서비스 테스트
│   ├── test_asset_service.py
│   ├── test_asset_http.py
│   ├── test_asset_params.py
│   ├── test_crawler.py
│   ├── test_crawler_http.py
│   └── test_target_service_cascade.py
└── utils/               # 유틸 테스트
    └── test_url_parser.py
```

**평가:** 테스트 구조가 잘 갖춰져 있음 (22개 테스트 파일)

---

## 4. 종합 평가

### 4.1 영역별 점수

| 영역 | 점수 | 평가 |
|------|------|------|
| **아키텍처 설계** | 8/10 | 레이어드 구조, 비동기 처리 우수 |
| **데이터 모델** | 8/10 | JSONB 활용, CASCADE 설계 적절 |
| **API 설계** | 7/10 | RESTful, 일부 일관성 문제 |
| **비즈니스 로직** | 7/10 | 핵심 플로우 완성, 일부 미구현 |
| **Worker 시스템** | 6/10 | 기본 기능 동작, 확장성 부족 |
| **보안** | 4/10 | MVP 수준, 프로덕션 준비 필요 |
| **테스트** | 8/10 | 체계적인 테스트 구조 |

### 4.2 종합 점수: **6.9/10**

---

## 5. 개선 권장사항

### 5.1 높은 우선순위

| 항목 | 현재 | 권장 | 이유 |
|------|------|------|------|
| 인증/인가 | 없음 | JWT + RBAC | 보안 필수 |
| CORS | `*` | 화이트리스트 | 보안 필수 |
| Worker 스케일링 | 단일 | 다중 Worker + 잠금 | 성능 |
| 재시도 로직 | 없음 | 지수 백오프 | 안정성 |

### 5.2 중간 우선순위

| 항목 | 현재 | 권장 | 이유 |
|------|------|------|------|
| 크롤링 깊이 | 1-depth | 설정 가능한 재귀 | 기능 확장 |
| TargetScope | 미사용 | 범위 제한 로직 | 기능 완성 |
| 모니터링 | 없음 | Prometheus + Grafana | 운영 |
| Dead Letter Queue | 없음 | Redis + 재처리 | 안정성 |

### 5.3 권장 리팩토링

**worker.py 분리:**

```
현재:
worker.py (307 lines)

권장:
workers/
├── __init__.py
├── base_worker.py      # 공통 로직 (check_cancellation, 상태 업데이트)
├── crawl_worker.py     # 크롤링 전용 워커
├── scan_worker.py      # 스캔 전용 워커 (미래)
└── task_registry.py    # 작업 타입 등록/관리
```

**utc_now() 통합:**

```python
# app/utils/datetime.py
from datetime import datetime, timezone

def utc_now() -> datetime:
    """UTC 현재 시간 (naive datetime)"""
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

---

## 6. 결론

EAZY 백엔드는 **MVP로서 핵심 기능이 잘 구현**되어 있으며, 비동기 아키텍처와 레이어드 설계가 적절합니다. 다만 **프로덕션 배포를 위해서는 보안 강화와 Worker 확장성 개선**이 필수적입니다.

### 즉시 조치 필요 항목
1. 인증/인가 시스템 구현
2. CORS 정책 제한
3. 환경 변수로 민감 정보 관리

### 단기 개선 항목
1. Worker 다중화 및 재시도 로직
2. TargetScope 기반 크롤링 범위 제한
3. worker.py 모듈 분리

---

## 부록: 분석 메타데이터

| 항목 | 값 |
|------|-----|
| 분석 도구 | Sequential-Thinking MCP |
| 분석 단계 | 7단계 |
| 참여 페르소나 | 6명 |
| 분석 파일 수 | 30+ Python 파일 |
| 총 코드 라인 | ~2,500 lines |
| 문서 버전 | 1.0 |
