# Active Scan V2 재설계 계획

**Status**: 🟡 Phase 5 진행 중 (95% 완료)
**Started**: 2025-01-28
**Last Updated**: 2025-01-29
**Estimated Completion**: 2025-03-07 (5주)

---

## 개요

Active Scan 시스템을 Pipeline + Hexagonal Architecture 하이브리드로 완전히 재설계하는 프로젝트입니다.

### ⚠️ 주의사항

| 항목 | 내용 |
|------|------|
| **Python 환경** | 반드시 **UV**를 사용해야 합니다 (`pip`, `poetry` 대신 `uv` 명령어 사용) |
| **Redis** | **Docker 컨테이너**로 동작 중입니다 - 테스트 전 컨테이너 상태 확인 필요 |

```bash
# Python 실행
uv run python script.py
uv run pytest

# Redis 컨테이너 상태 확인
docker ps --filter name=eazy-redis
docker start eazy-redis  # 필요 시 시작
```

### 문제점

현재 Active Scan 시스템에는 다음과 같은 심각한 문제가 있습니다:

| 문제 | 원인 | 파일 위치 |
|------|------|----------|
| Task Stuck | ACK 실패, Session 닫힘 후 에러 핸들링 | `workers/base.py:286-322` (`_handle_failure` 메서드) |
| IntegrityError | 배치 내 중복 저장 시 hash 충돌 | `services/asset_service.py:140-148, 183-188` (pending buffer 중복 체크 및 추가 로직) |
| 무한 재시도 | Lock 경합 시 retry 제한 | `workers/base.py:198-222` (MAX_RETRIES로 제한됨, 개선 가능) |
| SRP 위반 | CrawlWorker에 8가지 책임 (513줄) | `workers/crawl_worker.py` |

### 목표

- CrawlWorker 513줄 → ~50줄로 축소 (-90%)
- 테스트 커버리지 ~70% → ~95%로 향상
- 모듈화된 구조로 유지보수성 및 확장성 향상
- 새로운 Discovery 모듈 추가 시간 2시간 → 30분으로 단축

---

## 브랜치 전략

- **작업 브랜치**: `feature/active-scan-v2`
- **기준 브랜치**: `main`
- **기존 코드 처리**: 완전 삭제 후 새로 구현

---

## Phase 목록

| Phase | 이름 | 예상 기간 | 문서 |
|-------|------|----------|------|
| **Phase 1** | 인프라 계층 분리 | 1주 | [phase-1-infrastructure.md](./phase-1-infrastructure.md) |
| **Phase 2** | Domain 계층 추출 | 1주 | [phase-2-domain.md](./phase-2-domain.md) |
| **Phase 3** | Pipeline 구조 구현 (1) | 1주 | [phase-3-pipeline-1.md](./phase-3-pipeline-1.md) |
| **Phase 4** | Pipeline 구조 구현 (2) | 1주 | [phase-4-pipeline-2.md](./phase-4-pipeline-2.md) |
| **Phase 5** | Worker 단순화 & 마무리 | 1주 | [phase-5-worker-cleanup.md](./phase-5-worker-cleanup.md) |

---

## 아키텍처 개요

### 새로운 레이어 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  (API Endpoints, Worker Entry Points)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              CrawlOrchestrator (조율자)               │   │
│  └──────────────────────────────────────────────────────┘   │
│     ┌─────────┬──────────┬───────────┬──────────┬────────┐  │
│     │ Guard   │  Crawl   │ Discovery │  Asset   │ Recurse│  │
│     │ Stage   │  Stage   │  Stage    │  Stage   │ Stage  │  │
│     └─────────┴──────────┴───────────┴──────────┴────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  • UrlValidator (SSRF 검증)                                 │
│  • DataTransformer (데이터 변환)                            │
│  • ScopeChecker (범위 검증)                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│  Ports: ICrawler, IAssetRepository, ILockManager, ITaskQueue│
│  Adapters: PlaywrightCrawler, PostgresAssetRepo, RedisLock  │
└─────────────────────────────────────────────────────────────┘
```

### 파이프라인 흐름

```
Guard Stage → Crawl Stage → Discovery Stage → Asset Stage → Recurse Stage
     │             │              │               │              │
     ▼             ▼              ▼               ▼              ▼
 SSRF/Scope    크롤링 실행    자산 발견       자산 저장     자식 Task 생성
   검증                                      (배치+중복제거)
```

---

## 디렉토리 구조

```
backend/app/
├── domain/                          # [NEW] Domain Layer
│   ├── entities/
│   │   ├── asset.py
│   │   └── crawl_result.py
│   ├── value_objects/
│   │   ├── discovered_asset.py
│   │   └── url.py
│   └── services/
│       ├── url_validator.py
│       ├── data_transformer.py
│       └── scope_checker.py
│
├── application/                     # [NEW] Application Layer
│   ├── orchestrators/
│   │   └── crawl_orchestrator.py
│   ├── stages/
│   │   ├── base.py
│   │   ├── guard_stage.py
│   │   ├── crawl_stage.py
│   │   ├── discovery_stage.py
│   │   ├── asset_stage.py
│   │   └── recurse_stage.py
│   └── context/
│       └── pipeline_context.py
│
├── infrastructure/
│   ├── ports/                       # [NEW] Interfaces
│   │   ├── crawler.py
│   │   ├── asset_repository.py
│   │   ├── lock_manager.py
│   │   └── task_queue.py
│   ├── adapters/                    # [NEW] Implementations
│   │   ├── playwright_crawler.py
│   │   ├── postgres_asset_repo.py
│   │   ├── redis_lock_manager.py
│   │   └── redis_task_queue.py
│   └── persistence/
│       └── session_manager.py
│
├── workers/                         # [SIMPLIFIED]
│   ├── base.py
│   ├── crawl_worker.py
│   └── runner.py
│
├── core/
│   ├── queue_v2.py
│   ├── lock_v2.py
│   └── session.py
│
└── services/discovery/              # [KEPT]
```

---

## 삭제 대상 파일

기존 로직 완전 삭제 예정:

```
backend/app/workers/crawl_worker.py      # 새 구현으로 대체 (Thin Wrapper)
backend/app/services/asset_service.py    # AssetStage + IAssetRepository로 대체
backend/app/services/crawl_manager.py    # RecurseStage로 대체
backend/app/core/queue.py                # TaskQueueV2로 대체
backend/app/core/lock.py                 # DistributedLockV2로 대체
```

---

## 어댑터 전략

기존 서비스와 새로운 Port 인터페이스 간 통합을 위한 어댑터 전략입니다.

### CrawlerService → ICrawler Adapter

**현재 인터페이스** (`services/crawler_service.py:150-152`):
```python
# CrawlerService.crawl() 반환값
tuple[List[str], Dict[str, HttpData], List[JsContent]]  # (links, http_data, js_contents)
# HttpData: app/types/http.py:42 (TypedDict)
# JsContent: app/types/http.py:78 (TypedDict)
```

**새 인터페이스** (`infrastructure/ports/crawler.py`):
```python
from app.types.http import HttpData, JsContent

class ICrawler(Protocol):
    async def crawl(self, url: str) -> CrawlData: ...

@dataclass
class CrawlData:
    links: List[str]
    http_data: Dict[str, HttpData]  # 기존 타입 유지
    js_contents: List[JsContent]    # 기존 타입 유지
```

**어댑터 구현**:
```python
class PlaywrightCrawlerAdapter:
    """기존 CrawlerService를 ICrawler로 래핑"""
    def __init__(self, crawler_service: CrawlerService):
        self._crawler = crawler_service

    async def crawl(self, url: str) -> CrawlData:
        links, http_data, js_contents = await self._crawler.crawl(url)
        return CrawlData(links=links, http_data=http_data, js_contents=js_contents)
```

### DiscoveryService → IDiscoveryService Adapter

**현재 인터페이스** (`services/discovery/service.py:65-74`):
```python
# DiscoveryService.run() 메서드
async def run(self, context: DiscoveryContext) -> List[DiscoveredAsset]: ...
```

**새 인터페이스** (`infrastructure/ports/discovery.py`):
```python
class IDiscoveryService(Protocol):
    async def discover(self, context: DiscoveryContext) -> List[DiscoveredAsset]: ...
```

**어댑터 구현**:
```python
class DiscoveryServiceAdapter:
    """기존 DiscoveryService를 IDiscoveryService로 래핑"""
    def __init__(self, discovery_service: DiscoveryService):
        self._service = discovery_service

    async def discover(self, context: DiscoveryContext) -> List[DiscoveredAsset]:
        return await self._service.run(context)  # run() -> discover() 매핑
```

### AssetService → IAssetRepository Adapter

**현재 인터페이스** (`services/asset_service.py`):
```python
class AssetService:
    async def process_asset(self, ...) -> Asset: ...
    async def flush(self) -> None: ...
```

**새 인터페이스** (`infrastructure/ports/asset_repository.py`):
```python
class IAssetRepository(Protocol):
    async def save_batch(self, assets: List[Asset], task_id: int) -> int: ...
    async def find_by_hash(self, content_hash: str) -> Optional[Asset]: ...
```

**어댑터 구현**:
```python
class PostgresAssetRepositoryAdapter:
    """기존 AssetService를 IAssetRepository로 래핑 + 향상"""
    def __init__(self, session: AsyncSession):
        self._session = session
        self._asset_service = AssetService(session)

    async def save_batch(self, assets: List[Asset], task_id: int) -> int:
        count = 0
        async with self._asset_service as svc:
            for asset in assets:
                await svc.process_asset(...)
                count += 1
        return count
```

---

## 기존 코드 추출 vs 새 구현

| 컴포넌트 | 전략 | 원본 위치 | 비고 |
|----------|------|----------|------|
| **UrlValidator** | 추출 + 개선 | `workers/crawl_worker.py:132-186` (`is_safe_url`) | 클래스로 래핑, ValidationResult 추가 |
| **DataTransformer** | 추출 + 개선 | `workers/crawl_worker.py:39-124` (매핑 함수들) | 클래스로 통합 |
| **ScopeChecker** | 래핑 | `services/scope_filter.py` (ScopeFilter 클래스) | 기존 ScopeFilter 활용 |
| **SessionManager** | 새 구현 | - | SQLAlchemy async session 래핑 |
| **TaskQueueV2** | 새 구현 | - | 기존 TaskPriority 재사용 |
| **DistributedLockV2** | 새 구현 | - | Fencing token 추가 |

### ScopeChecker와 ScopeFilter 관계

`ScopeChecker`는 기존 `ScopeFilter`(`services/scope_filter.py`)를 래핑합니다:

```python
class ScopeChecker:
    """Domain 계층의 Scope 검증 서비스"""
    def __init__(self):
        self._filter: Optional[ScopeFilter] = None

    def is_in_scope(self, url: str, target: Target) -> bool:
        # ScopeFilter 인스턴스 생성 (lazy)
        filter = ScopeFilter(target.url, target.scope)
        return filter.is_in_scope(url)
```

---

## 우선순위 시스템 통합

### TaskPriority vs QueuePriority

기존 `TaskPriority` (`core/priority.py`)를 **그대로 사용**합니다:

```python
# 기존 (유지)
class TaskPriority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
```

**TaskQueueV2**는 기존 `TaskPriority`를 import하여 사용:
```python
from app.core.priority import TaskPriority, PRIORITY_ORDER, get_queue_key

class TaskQueueV2:
    async def enqueue(self, task_data: dict, priority: TaskPriority = TaskPriority.NORMAL) -> str:
        queue_key = get_queue_key(self._base_key, priority)
        ...
```

---

## 큐 데이터 마이그레이션 전략

### 전환 기간 처리

1. **Dual-Write 기간 (Phase 1-4)**
   - 기존 `TaskManager`와 `TaskQueueV2` 병행 운영
   - 새 Task는 두 큐에 모두 enqueue
   - Worker는 기존 큐에서만 dequeue

2. **전환 (Phase 5 시작 시)**
   - 기존 큐가 비어있는지 확인
   - 비어있지 않으면 기존 큐 먼저 소진
   - 새 Worker는 `TaskQueueV2`에서만 dequeue

3. **정리 (Phase 5 완료 후)**
   - 기존 큐 키 삭제
   - 기존 `TaskManager` 코드 삭제

### Dual-Write 중복 처리 방지

Dual-Write 기간 동안 Task가 두 번 처리되는 것을 방지하기 위한 전략:

**1. Task ID 기반 중복 감지**:
```python
# core/deduplication.py
class TaskDeduplicator:
    """Task 중복 처리 방지"""

    PROCESSED_KEY_PREFIX = "task:processed:"
    PROCESSED_TTL = 86400  # 24시간

    def __init__(self, redis: Redis):
        self._redis = redis

    async def is_processed(self, task_id: int) -> bool:
        """Task가 이미 처리되었는지 확인"""
        key = f"{self.PROCESSED_KEY_PREFIX}{task_id}"
        return await self._redis.exists(key) > 0

    async def mark_processed(self, task_id: int) -> None:
        """Task를 처리됨으로 표시"""
        key = f"{self.PROCESSED_KEY_PREFIX}{task_id}"
        await self._redis.setex(key, self.PROCESSED_TTL, "1")
```

**2. Worker에서 사용**:
```python
# workers/crawl_worker.py
async def execute(self, task_data: dict, task_record: Task) -> TaskResult:
    # 중복 처리 방지
    if await self._deduplicator.is_processed(task_record.id):
        logger.info("Task already processed, skipping", task_id=task_record.id)
        return TaskResult.create_skipped({"reason": "already_processed"})

    # 처리 시작 전 표시
    await self._deduplicator.mark_processed(task_record.id)

    # 실제 처리 로직...
```

**3. 대안: 단일 큐 전환 (Blue-Green)**

Dual-Write 대신 Blue-Green 전환 방식을 사용할 수도 있습니다:
- 특정 시점에 모든 Worker를 중지
- 기존 큐의 모든 Task 처리 완료 대기
- 새 Worker만 시작 (TaskQueueV2 사용)
- 장점: 중복 처리 불가능
- 단점: 짧은 다운타임 발생

### 마이그레이션 스크립트

```python
# scripts/migrate_queue.py
async def migrate_pending_tasks():
    """기존 큐의 pending tasks를 새 큐로 이동"""
    old_queue = TaskManager(redis)
    new_queue = TaskQueueV2(redis)

    while task := await old_queue.dequeue():
        await new_queue.enqueue(task.data, task.priority)
        await old_queue.ack(task)
```

---

## 공통 명령어

### UV 환경 설정

```bash
# 가상환경 생성
uv venv --python 3.11
source .venv/bin/activate

# 의존성 설치
uv pip install -e ".[dev]"
```

### 테스트 실행

```bash
# 전체 테스트
uv run pytest

# 단위 테스트만
uv run pytest -m "unit"

# 커버리지 포함
uv run pytest --cov=app --cov-report=html

# 병렬 실행
uv run pytest -n auto
```

### 코드 품질

```bash
# 린팅
uv run ruff check .
uv run ruff format .
uv run mypy app
```

### Worker 실행

```bash
uv run worker-pool
```

---

## 참고 자료

- Architect 상세 계획: `/Users/lrtk/.claude/plans/bright-exploring-haven-agent-a4534b3.md`
- Backend Developer 상세 계획: `/Users/lrtk/.claude/plans/bright-exploring-haven-agent-ae8d82b.md`
- Code Quality Guidelines: `/Users/lrtk/.claude/plans/bright-exploring-haven-agent-adfa6a5.md`

---

## 진행 상황

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 1 | ✅ Completed | 100% |
| Phase 2 | ✅ Completed | 100% |
| Phase 3 | ✅ Completed | 100% |
| Phase 4 | ✅ Completed | 100% |
| Phase 5 | 🟡 In Progress | 95% |

**전체 진행률**: 95%

### 구현 통계
| 계층 | 코드량 | 테스트 |
|------|--------|--------|
| Infrastructure (Ports + Adapters) | 416줄 | ✅ |
| Application (Stages + Orchestrator) | 901줄 | ✅ |
| Domain (Services) | 398줄 | ✅ |
| Core V2 (Queue + Lock + Session) | 1,066줄 | ✅ |
| **총합** | **2,781줄** | **30개 파일 (8,061줄)** |
