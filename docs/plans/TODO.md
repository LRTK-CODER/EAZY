# EAZY 프로젝트 TODO List

> **생성일:** 2026-01-10
> **기반 문서:** SCAN_IMPROVEMENT_PLAN.md, SCAN_LOGIC_ANALYSIS.md

---

## 진행 상태 범례

- [ ] 미시작
- [x] 완료
- [~] 진행 중

---

## Phase 0: Quick Wins - TDD (45분)

> **목표:** 최소 노력으로 즉각적인 효과
> **개발 방식:** TDD (Test-Driven Development)

### Step 1: 코드 정리 (5분) ✅
- [x] `worker.py` 상단에 `import json` 추가
- [x] `worker.py` 함수 내부 `import json` 6개 제거 (line 89, 132, 141, 217, 260, 272)

### Step 2: BLPOP 적용 - TDD (20분) ✅

#### RED: 테스트 작성
- [x] `tests/core/test_task_manager.py`에 BLPOP 테스트 추가
  - [x] `test_dequeue_task_blpop()` - 정상 동작 테스트
  - [x] `test_dequeue_task_empty_queue()` - 빈 큐 테스트
- [x] `pytest tests/core/test_task_manager.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `queue.py`의 `lpop` → `blpop` 변경
- [x] `pytest tests/core/test_task_manager.py -v` 실행 → 통과 확인

#### REFACTOR
- [x] `worker.py`의 `asyncio.sleep(1)` 제거

### Step 3: 타임아웃 추가 - TDD (15분) ✅

#### RED: 테스트 작성
- [x] `tests/services/test_crawler_timeout.py` 신규 생성
  - [x] `test_crawler_uses_explicit_timeout()` 테스트 작성
- [x] `pytest tests/services/test_crawler_timeout.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `crawler_service.py`에 명시적 타임아웃 추가 (`timeout=30000`)
- [x] `pytest tests/services/test_crawler_timeout.py -v` 실행 → 통과 확인

### 검증 ✅
- [x] `pytest tests/ -v` 전체 테스트 통과
- [x] `python -m py_compile` 정적 검증

---

## Phase 1: 배치 처리 (2-3일) ✅

> **목표:** DB 부하 98% 감소
> **개발 방식:** TDD (Test-Driven Development)

### AssetService 리팩토링
- [x] `BATCH_SIZE` 상수 추가 (50개)
- [x] `_pending_assets` 리스트 추가
- [x] `_pending_discoveries` 리스트 추가
- [x] `flush()` 메서드 구현
- [x] `__aenter__` / `__aexit__` 구현 (Context Manager)
- [x] `process_asset()` 수정 - 즉시 커밋 제거

### Worker 수정
- [x] `AssetService`를 Context Manager로 사용하도록 변경
- [x] 배치 처리 로직 적용
- [x] 취소 시 flush 보장

### 테스트
- [x] 배치 저장 단위 테스트 작성 (`test_asset_service_batch.py`)
- [x] Context Manager 테스트
- [x] flush 테스트
- [x] Context Exit flush 테스트

---

## Phase 2: 안정성 강화 - TDD (5일)

> **목표:** 작업 손실 0% 달성
> **개발 방식:** TDD (Test-Driven Development)
> **안정성 점수:** 3.0/10 → 8.0/10

### Day 1: 에러 분류 시스템 ✅

#### RED: 테스트 작성
- [x] `tests/core/test_error_classification.py` 신규 생성
  - [x] `test_classify_timeout_as_retryable()`
  - [x] `test_classify_connection_error_as_retryable()`
  - [x] `test_classify_404_as_permanent()`
  - [x] `test_classify_invalid_data_as_permanent()`
  - [x] `test_classify_rate_limit_as_transient()`
  - [x] `test_classify_503_as_transient()`
  - [x] `test_unknown_error_defaults_to_retryable()`
- [x] `pytest tests/core/test_error_classification.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `core/errors.py` 생성
  - [x] `ErrorCategory` Enum 정의 (RETRYABLE, PERMANENT, TRANSIENT)
  - [x] `classify_error()` 함수 구현
- [x] `core/retry.py` 생성
  - [x] `MAX_RETRIES = 3`, `BASE_DELAY = 1.0`, `MAX_DELAY = 60.0`
  - [x] `calculate_backoff()` 함수 (Exponential + Jitter)
  - [x] `TaskRetryInfo` dataclass
- [x] `pytest tests/core/test_error_classification.py -v` 실행 → 통과 확인 (27개)

---

### Day 2: BRPOPLPUSH + ACK 패턴 ✅

#### RED: 테스트 작성
- [x] `tests/core/test_task_manager_ack.py` 신규 생성
  - [x] `test_brpoplpush_moves_to_processing()`
  - [x] `test_ack_removes_from_processing()`
  - [x] `test_nack_retry_moves_back_to_queue()`
  - [x] `test_nack_dlq_moves_to_dead_letter()`
  - [x] `test_processing_queue_persists_on_crash()`
- [x] `pytest tests/core/test_task_manager_ack.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `core/queue.py` 수정
  - [x] `processing_key = "eazy_task_queue:processing"` 추가
  - [x] `dlq_key = "eazy_task_queue:dlq"` 추가
  - [x] `dequeue_task()` → `blmove` 변경 (BRPOPLPUSH 대체)
  - [x] `ack_task(task_json: str)` 메서드 구현
  - [x] `nack_task(task_json: str, retry: bool)` 메서드 구현
  - [x] `get_processing_tasks()` 메서드 추가
- [x] `worker.py` 수정 - dequeue_task 반환값 처리
- [x] `pytest tests/core/test_task_manager_ack.py -v` 실행 → 통과 확인 (10개)

---

### Day 3: DLQ 관리자 ✅

#### RED: 테스트 작성
- [x] `tests/core/test_dlq_manager.py` 신규 생성
  - [x] `test_move_to_dlq_stores_metadata()`
  - [x] `test_move_to_dlq_adds_to_list()`
  - [x] `test_list_dlq_tasks_returns_with_meta()`
  - [x] `test_retry_dlq_moves_back_to_queue()`
  - [x] `test_retry_dlq_clears_metadata()`
  - [x] `test_purge_dlq_removes_completely()`
  - [x] `test_dlq_preserves_original_task_data()`
- [x] `pytest tests/core/test_dlq_manager.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `core/dlq.py` 신규 생성
  - [x] `DLQManager` 클래스 구현
  - [x] `move_to_dlq()` 메서드 (메타데이터 저장)
  - [x] `list_dlq_tasks()` 메서드 (목록 조회)
  - [x] `retry_dlq_task()` 메서드 (수동 재시도)
  - [x] `purge_dlq_task()` 메서드 (영구 삭제)
- [x] `pytest tests/core/test_dlq_manager.py -v` 실행 → 통과 확인 (9개)

---

### Day 4: 고아 작업 복구 ✅

#### RED: 테스트 작성
- [x] `tests/core/test_orphan_recovery.py` 신규 생성
  - [x] `test_orphan_detected_without_heartbeat()`
  - [x] `test_orphan_detected_after_timeout()`
  - [x] `test_orphan_recovered_to_queue()`
  - [x] `test_recovery_count_increments()`
  - [x] `test_excessive_recovery_sends_to_dlq()`
  - [x] `test_heartbeat_prevents_orphan_detection()`
  - [x] `test_heartbeat_expires_after_timeout()`
- [x] `pytest tests/core/test_orphan_recovery.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `core/recovery.py` 신규 생성
  - [x] `ORPHAN_TIMEOUT = 600` (10분)
  - [x] `MAX_RECOVERY_COUNT = 3`
  - [x] `OrphanRecovery` 클래스 구현
  - [x] `find_orphan_tasks()` 메서드
  - [x] `recover_orphan_tasks()` 메서드
  - [x] `send_heartbeat()` 메서드
  - [x] `clear_heartbeat()` 메서드
- [x] `pytest tests/core/test_orphan_recovery.py -v` 실행 → 통과 확인 (9개)

---

### Day 5: Worker 통합 + E2E 테스트 ✅

#### RED: 테스트 작성
- [x] `tests/integration/test_worker_reliability.py` 신규 생성
  - [x] `test_worker_acks_on_success()`
  - [x] `test_worker_nacks_on_retryable_error()`
  - [x] `test_worker_sends_to_dlq_on_permanent_error()`
  - [x] `test_worker_retries_with_backoff()`
  - [x] `test_worker_crash_recovery()`
- [x] `pytest tests/integration/test_worker_reliability.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `worker.py` 수정
  - [x] ACK/NACK 패턴 적용
  - [x] 성공 시 `ack_task()` 호출
  - [x] 취소 시 `ack_task()` 호출
  - [x] 실패 시 `ack_task()` 호출
  - [x] 유효하지 않은 작업 처리
- [x] `pytest tests/integration/test_worker_reliability.py -v` 실행 → 통과 확인 (5개)

---

### 검증 ✅
- [x] `pytest tests/ -v` 전체 테스트 통과 (144개)
- [x] `pytest tests/ --cov=app --cov-report=html` 커버리지 확인 (77%)
- [x] Worker 크래시 시뮬레이션 → 작업 복구 확인
- [x] DLQ 수동 재시도 테스트

---

### 파일 구조 변경

```
backend/app/core/
├── queue.py       # 수정: BRPOPLPUSH, ack, nack
├── errors.py      # 신규: ErrorCategory, classify_error
├── retry.py       # 신규: calculate_backoff, TaskRetryInfo
├── dlq.py         # 신규: DLQManager
└── recovery.py    # 신규: OrphanRecovery

backend/tests/core/
├── test_error_classification.py  # 신규 (27개 테스트)
├── test_task_manager_ack.py      # 신규 (10개 테스트)
├── test_dlq_manager.py           # 신규 (9개 테스트)
└── test_orphan_recovery.py       # 신규 (9개 테스트)

backend/tests/integration/
└── test_worker_reliability.py    # 신규 (5개 테스트)
```

**총 신규 테스트: 60개** ✅

---

## Phase 3: 아키텍처 개선 - TDD (5일) ✅

> **목표:** 유지보수성 향상, 코드 중복 제거, 확장성 확보
> **개발 방식:** TDD (Test-Driven Development)
> **변환:** `worker.py` (323줄) → `workers/` 모듈화 구조
> **결과:** 204개 테스트 통과, 커버리지 78%

### Day 1: BaseWorker + WorkerContext (기초 추상화) ✅

#### RED: 테스트 작성
- [x] `tests/workers/test_base_worker.py` 신규 생성 (16개 테스트)
  - [x] WorkerContext 테스트
  - [x] TaskResult 테스트
  - [x] BaseWorker 추상 클래스 테스트
  - [x] process() 메서드 테스트
- [x] `pytest tests/workers/test_base_worker.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `app/workers/__init__.py` 생성
- [x] `app/workers/base.py` 생성
  - [x] `WorkerContext` dataclass (의존성 주입 컨테이너)
  - [x] `TaskResult` dataclass (실행 결과)
  - [x] `BaseWorker` 추상 클래스
  - [x] `process()` 공통 로직 구현
- [x] `pytest tests/workers/test_base_worker.py -v` 실행 → 통과 확인 (16개)

---

### Day 2: CrawlWorker (크롤링 Worker 분리) ✅

#### RED: 테스트 작성
- [x] `tests/workers/test_crawl_worker.py` 신규 생성 (15개 테스트)
  - [x] CrawlWorker 속성 테스트
  - [x] execute() 메서드 테스트
  - [x] 취소 처리 테스트
  - [x] HTTP 데이터 추출 테스트
- [x] `pytest tests/workers/test_crawl_worker.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `app/workers/crawl_worker.py` 생성
  - [x] `CrawlWorker` 클래스 구현 (BaseWorker 상속)
  - [x] 의존성 주입 지원 (`crawler_service`, `asset_service_factory`)
  - [x] `task_type` 속성 정의
  - [x] `execute()` 메서드 구현
  - [x] 취소 확인 로직 (시간 기반 + 아이템 기반)
- [x] `pytest tests/workers/test_crawl_worker.py -v` 실행 → 통과 확인 (15개)

---

### Day 3: Worker Registry (확장성 확보) ✅

#### RED: 테스트 작성
- [x] `tests/workers/test_registry.py` 신규 생성 (12개 테스트)
  - [x] WORKER_REGISTRY 테스트
  - [x] get_worker_class() 테스트
  - [x] @register_worker 데코레이터 테스트
  - [x] create_worker() 팩토리 테스트
- [x] `pytest tests/workers/test_registry.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `app/workers/registry.py` 생성
  - [x] `WORKER_REGISTRY` dict 정의
  - [x] `get_worker_class()` 함수
  - [x] `@register_worker` 데코레이터
  - [x] `create_worker()` 팩토리 함수
- [x] `pytest tests/workers/test_registry.py -v` 실행 → 통과 확인 (12개)

---

### Day 4: Worker Runner (메인 루프) ✅

#### RED: 테스트 작성
- [x] `tests/workers/test_runner.py` 신규 생성 (9개 테스트)
  - [x] process_one_task() 테스트
  - [x] create_worker_context() 테스트
  - [x] 통합 테스트
- [x] `pytest tests/workers/test_runner.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `app/workers/runner.py` 생성
  - [x] `create_worker_context()` 함수
  - [x] `process_one_task()` 함수
  - [x] `run_worker()` 메인 루프
- [x] Redis 단일 연결 문제 해결 (`single_connection_client=True`)
- [x] `pytest tests/workers/test_runner.py -v` 실행 → 통과 확인 (9개)

---

### Day 5: 통합 + 마이그레이션 ✅

#### RED: 테스트 작성
- [x] `tests/workers/test_runner.py`에 추가 (8개 테스트)
  - [x] TestPackageExports 클래스 (7개 테스트)
  - [x] TestDeprecation 클래스 (1개 테스트)
- [x] `pytest tests/workers/ -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `app/workers/__init__.py` 공개 API 정의 완료
- [x] `tests/workers/conftest.py` Worker 전용 fixtures
- [x] `tests/conftest.py` Redis 단일 연결 설정 적용
- [x] `app/worker.py` → 폐기 예정 표시 + DeprecationWarning 추가
- [x] `pytest tests/workers/ -v` 실행 → 통과 확인 (60개)

---

### 검증 ✅
- [x] `pytest tests/ -v` 전체 테스트 통과 (204개)
- [x] `pytest tests/ --cov=app` 커버리지 확인 (78%)
- [x] `python -c "from app.workers import run_worker; print('OK')"` import 확인
- [x] 기존 스캔 기능 정상 동작 확인

---

### 파일 구조 변경 ✅

```
backend/app/workers/
├── __init__.py      # 패키지 공개 API (47줄)
├── base.py          # BaseWorker, WorkerContext, TaskResult (245줄)
├── crawl_worker.py  # CrawlWorker 구현 (104줄)
├── registry.py      # WORKER_REGISTRY, @register_worker (103줄)
└── runner.py        # run_worker() 메인 루프 (131줄)

backend/tests/workers/
├── __init__.py              # 패키지 초기화
├── conftest.py              # Worker 전용 fixtures (89줄)
├── test_base_worker.py      # 16개 테스트
├── test_crawl_worker.py     # 15개 테스트
├── test_registry.py         # 12개 테스트
└── test_runner.py           # 17개 테스트 (9 + 8)
```

**총 신규 테스트: 60개** ✅

---

## Phase 4: 확장성 확보 - TDD (5일) ✅

> **목표:** 수평 확장 가능, Target 중복 스캔 방지
> **개발 방식:** TDD (Test-Driven Development)
> **신규 테스트:** 84개 (33 + 18 + 13 + 20)
> **결과:** 288개 테스트 통과

### 기술 결정사항

| 항목 | 결정 | 근거 |
|-----|------|------|
| 동시성 패턴 | `asyncio.wait` + `FIRST_COMPLETED` | 구조적 동시성, shutdown 대응 |
| 시그널 핸들링 | `loop.add_signal_handler` | 비동기 안전, asyncio 통합 |
| Redis 연결 | 워커별 독립 연결 | `BLMOVE` 블로킹 격리 |
| DB 세션 | 태스크별 생성 (현재 유지) | 트랜잭션 격리 |
| 분산 잠금 | 단순 SETNX + Lua | Redlock 불필요 (단일 Redis) |
| 잠금 TTL | 600초 | OrphanRecovery와 일치 |

---

### Day 1-2: WorkerPool + Graceful Shutdown (TDD) ✅

#### RED: 테스트 작성
- [x] `tests/workers/test_pool.py` 신규 생성 (33개 테스트)
  - [x] `TestWorkerPoolConfig` (4개 테스트)
  - [x] `TestWorkerPoolInit` (5개 테스트)
  - [x] `TestWorkerPoolStart` (6개 테스트)
  - [x] `TestWorkerPoolStop` (6개 테스트)
  - [x] `TestSignalHandling` (4개 테스트)
  - [x] `TestWorkerRestart` (4개 테스트)
  - [x] `TestResourceManagement` (2개 테스트)
  - [x] `TestWorkerPoolProperties` (2개 테스트)
- [x] `uv run pytest tests/workers/test_pool.py -v` 실행 → 통과 확인 (33개)

#### GREEN: 구현
- [x] `app/core/config.py` 수정
  - [x] `WORKER_NUM_WORKERS: int = 4` 추가
  - [x] `WORKER_SHUTDOWN_TIMEOUT: int = 30` 추가
  - [x] `WORKER_MAX_RESTARTS: int = 5` 추가
- [x] `app/workers/pool.py` 신규 생성 (342줄)
  - [x] `WorkerPoolConfig` dataclass + `from_env()` 메서드
  - [x] `WorkerPool` 클래스
  - [x] `start()` 메서드 (asyncio.wait + FIRST_COMPLETED 패턴)
  - [x] `stop()` 메서드
  - [x] `_setup_signal_handlers()` 메서드
  - [x] `_run_single_worker()` 메서드
  - [x] `_run_worker_supervised()` 메서드 (재시작 래퍼)
  - [x] `_cleanup()` 메서드

---

### Day 3: 분산 잠금 시스템 (TDD) ✅

#### RED: 테스트 작성
- [x] `tests/core/test_distributed_lock.py` 신규 생성 (18개 테스트)
  - [x] `TestLockAcquisition` (3개 테스트)
  - [x] `TestLockRelease` (3개 테스트)
  - [x] `TestContextManager` (3개 테스트)
  - [x] `TestLockExtension` (2개 테스트)
  - [x] `TestConcurrency` (2개 테스트)
  - [x] `TestIsOwned` (2개 테스트)
  - [x] `TestLockInfo` (3개 테스트)
- [x] `uv run pytest tests/core/test_distributed_lock.py -v` 실행 → 통과 확인 (18개)

#### GREEN: 구현
- [x] `app/core/lock.py` 신규 생성 (162줄)
  - [x] `RELEASE_SCRIPT` Lua 스크립트 (토큰 검증 후 삭제)
  - [x] `EXTEND_SCRIPT` Lua 스크립트 (토큰 검증 후 TTL 연장)
  - [x] `LockAcquisitionError` 예외 클래스
  - [x] `DistributedLock` 클래스
    - [x] `__init__(redis, name, ttl, prefix)` 메서드
    - [x] `acquire()` 메서드 (SET NX EX)
    - [x] `release()` 메서드 (Lua 스크립트)
    - [x] `extend()` 메서드 (Lua 스크립트)
    - [x] `is_owned()` 메서드
    - [x] `__aenter__()` / `__aexit__()` (Context Manager)

---

### Day 4: CrawlWorker 잠금 통합 (TDD) ✅

#### RED: 테스트 작성
- [x] `tests/workers/test_crawl_worker_lock.py` 신규 생성 (13개 테스트)
  - [x] `TestCrawlWorkerLockIntegration` (5개 테스트)
  - [x] `TestLockFailureHandling` (3개 테스트)
  - [x] `TestLockTTL` (2개 테스트)
  - [x] `TestConcurrentLocks` (1개 테스트)
  - [x] `TestLockKey` (2개 테스트)
- [x] `uv run pytest tests/workers/test_crawl_worker_lock.py -v` 실행 → 통과 확인 (13개)

#### GREEN: 구현
- [x] `app/workers/base.py` 수정
  - [x] `TaskResult`에 `_skipped` 필드 추가
  - [x] `status` property 추가 ("success", "cancelled", "skipped", "failed")
  - [x] `create_skipped()` class method 추가
- [x] `app/workers/crawl_worker.py` 수정
  - [x] 상수 추가: `LOCK_TTL = 600`, `LOCK_PREFIX = "eazy:lock:"`
  - [x] `execute()` 메서드에 잠금 통합
  - [x] `_execute_with_lock()` 메서드 분리

---

### Day 5: 통합 테스트 + 마무리 (TDD) ✅

#### RED: 테스트 작성
- [x] `tests/integration/test_worker_pool_e2e.py` 신규 생성 (20개 테스트)
  - [x] `TestWorkerPoolConfiguration` (3개 테스트)
  - [x] `TestDistributedLockIntegration` (4개 테스트)
  - [x] `TestCrawlWorkerLockIntegration` (2개 테스트)
  - [x] `TestTaskResultIntegration` (4개 테스트)
  - [x] `TestPoolLifecycle` (2개 테스트)
  - [x] `TestErrorHandlingIntegration` (2개 테스트)
  - [x] `TestComponentExports` (3개 테스트)
- [x] `uv run pytest tests/integration/test_worker_pool_e2e.py -v` 실행 → 통과 확인 (20개)

#### GREEN: 구현
- [x] 통합 테스트 통과
- [x] 모든 컴포넌트 정상 동작 확인

---

### Day 5 버그 수정 (TDD) ✅

> **발견 일자:** 2026-01-10
> **수정 방식:** TDD (Red → Green → Refactor)

#### Bug Fix #1: Skipped Task Loss (CRITICAL)
- [x] **RED:** `TestSkippedTaskHandling` 테스트 작성 (3개)
  - [x] `test_skipped_result_calls_nack_not_ack()`
  - [x] `test_skipped_result_does_not_update_db_status()`
  - [x] `test_skipped_result_clears_heartbeat()`
- [x] **GREEN:** `base.py` process() 메서드에 skipped 처리 추가
- [x] **REFACTOR:** 코드 정리

#### Bug Fix #2: SSRF 취약점 (HIGH)
- [x] **RED:** `TestURLValidation` 테스트 작성 (20개)
  - [x] `test_unsafe_urls_rejected` (12개 parametrize)
  - [x] `test_safe_urls_allowed` (5개 parametrize)
  - [x] `test_empty_url_rejected`
  - [x] `test_invalid_url_rejected`
  - [x] `test_execute_rejects_unsafe_url`
- [x] **GREEN:** `crawl_worker.py`에 `is_safe_url()` 함수 구현
- [x] **GREEN:** `execute()` 메서드에 URL 검증 추가
- [x] **REFACTOR:** 코드 정리

---

### 검증 ✅
- [x] `uv run pytest tests/ -v` 전체 테스트 통과 (311개)
- [x] WorkerPool 다중 워커 동작 확인
- [x] Graceful Shutdown 테스트 (SIGTERM 전송)
- [x] Target 중복 스캔 방지 테스트 (분산 잠금)
- [x] Skipped Task Loss 버그 수정 검증
- [x] SSRF 취약점 수정 검증

---

### 파일 구조 변경 ✅

```
backend/app/
├── core/
│   ├── config.py       # 수정: WORKER_NUM_WORKERS, WORKER_SHUTDOWN_TIMEOUT, WORKER_MAX_RESTARTS
│   └── lock.py         # 신규: DistributedLock, LockAcquisitionError (162줄)
└── workers/
    ├── base.py         # 수정: TaskResult skipped 상태, process() skipped 처리 (Day 5 Bug Fix)
    ├── pool.py         # 신규: WorkerPool, WorkerPoolConfig (342줄)
    └── crawl_worker.py # 수정: 분산 잠금 통합, is_safe_url() SSRF 방지 (Day 5 Bug Fix)

backend/tests/
├── core/
│   └── test_distributed_lock.py   # 신규 (18개 테스트)
├── workers/
│   ├── test_pool.py               # 신규 (33개 테스트)
│   ├── test_crawl_worker_lock.py  # 신규 (13개 테스트)
│   ├── test_base_worker.py        # 추가: TestSkippedTaskHandling (3개 테스트) - Day 5 Bug Fix
│   └── test_crawl_worker.py       # 추가: TestURLValidation (20개 테스트) - Day 5 Bug Fix
└── integration/
    └── test_worker_pool_e2e.py    # 신규 (20개 테스트)
```

**총 신규 테스트: 107개** (84 + 23) ✅
**전체 테스트: 311개** ✅

---

### 실행 방법

```bash
# 워커 풀 실행 (권장)
uv run python -m app.workers.pool

# 환경변수로 워커 수 조절
WORKER_NUM_WORKERS=8 uv run python -m app.workers.pool

# 기존 단일 워커 (하위 호환)
uv run python -m app.workers.runner
```

### Docker Compose 설정 예시

```yaml
services:
  worker:
    build: ./backend
    command: uv run python -m app.workers.pool
    environment:
      - WORKER_NUM_WORKERS=4
      - WORKER_SHUTDOWN_TIMEOUT=30
    stop_grace_period: 35s
```

---

## Phase 4.5: 우선순위 큐 - TDD (3-5일) ✅

> **목표:** 우선순위 기반 태스크 처리, Starvation 방지
> **개발 방식:** TDD (Test-Driven Development)
> **신규 테스트:** 39개 ✅
> **설계:** Multi-Queue 접근법 (기존 BLMOVE 패턴 유지)
> **결과:** 350개 테스트 통과

### 기술 결정사항

| 항목 | 결정 | 근거 |
|------|------|------|
| 큐 구조 | Multi-Queue (4개 우선순위 큐) | 기존 blmove 패턴 유지, 하위호환 |
| 우선순위 | CRITICAL(3) > HIGH(2) > NORMAL(1) > LOW(0) | 세분화된 제어 |
| Starvation 방지 | Aging 메커니즘 | 대기 시간 기반 자동 승격 |
| 하위호환 | NORMAL 큐 = 기존 `eazy_task_queue` | 기존 코드 변경 없이 동작 |

### Redis 키 구조

```
eazy_task_queue:critical    ← Priority 3 (먼저 처리)
eazy_task_queue:high        ← Priority 2
eazy_task_queue             ← Priority 1 (normal, 하위호환)
eazy_task_queue:low         ← Priority 0 (마지막 처리)
eazy_task_queue:processing  ← 공용 처리 큐
eazy_task_queue:dlq         ← 공용 DLQ
```

---

### Day 1: TaskPriority Enum + Priority Enqueue ✅

#### RED: 테스트 작성
- [x] `tests/core/test_priority_queue.py` 신규 생성 (9개 테스트)
  - [x] `test_priority_enum_exists()` - TaskPriority enum 존재 확인
  - [x] `test_priority_has_four_levels()` - LOW, NORMAL, HIGH, CRITICAL 존재
  - [x] `test_priority_values_are_ordered()` - LOW < NORMAL < HIGH < CRITICAL
  - [x] `test_priority_integer_values()` - 0, 1, 2, 3 값 검증
  - [x] `test_enqueue_with_default_priority()` - 기본값 NORMAL 확인
  - [x] `test_enqueue_with_critical_priority()` - CRITICAL 큐 enqueue
  - [x] `test_enqueue_with_high_priority()` - HIGH 큐 enqueue
  - [x] `test_enqueue_with_low_priority()` - LOW 큐 enqueue
  - [x] `test_enqueue_stores_priority_in_payload()` - payload에 priority 필드
- [x] `uv run pytest tests/core/test_priority_queue.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `app/core/priority.py` 신규 생성
  - [x] `TaskPriority` IntEnum 정의 (LOW=0, NORMAL=1, HIGH=2, CRITICAL=3)
  - [x] `PRIORITY_QUEUE_SUFFIXES` 딕셔너리
  - [x] `get_queue_key()` 함수
- [x] `app/core/queue.py` 수정
  - [x] `enqueue_crawl_task()`에 `priority` 파라미터 추가
  - [x] payload에 `priority`, `enqueued_at` 필드 추가
- [x] `uv run pytest tests/core/test_priority_queue.py -v` 실행 → 통과 확인 (9개)

---

### Day 2: Priority-Ordered Dequeue ✅

#### RED: 테스트 작성
- [x] `tests/core/test_priority_dequeue.py` 신규 생성 (7개 테스트)
  - [x] `test_dequeue_critical_before_high()` - CRITICAL → HIGH 순서
  - [x] `test_dequeue_high_before_normal()` - HIGH → NORMAL 순서
  - [x] `test_dequeue_normal_before_low()` - NORMAL → LOW 순서
  - [x] `test_dequeue_fifo_within_same_priority()` - 동일 우선순위 FIFO
  - [x] `test_dequeue_moves_to_processing_queue()` - processing 큐 이동
  - [x] `test_dequeue_full_priority_order()` - 전체 순서 검증
  - [x] `test_dequeue_empty_returns_none()` - 빈 큐 None 반환
- [x] `uv run pytest tests/core/test_priority_dequeue.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `app/core/queue.py` 수정
  - [x] `PRIORITY_ORDER` 사용 (priority.py에서 import)
  - [x] `dequeue_task()` 우선순위 순서 dequeue 구현
  - [x] `lmove` (non-blocking) + `blmove` (blocking for LOW) 패턴
  - [x] FIFO 유지를 위해 "LEFT" 방향 사용
- [x] `uv run pytest tests/core/test_priority_dequeue.py -v` 실행 → 통과 확인 (7개)
- [x] 기존 `test_task_manager.py` 테스트 업데이트 (priority queue 호환)

---

### Day 3: Starvation Prevention (Aging 메커니즘) ✅

#### RED: 테스트 작성
- [x] `tests/core/test_priority_aging.py` 신규 생성 (10개 테스트)
  - [x] `test_enqueue_adds_enqueued_at()` - enqueued_at 타임스탬프
  - [x] `test_aging_config_exists()` - AgingConfig 클래스
  - [x] `test_default_aging_thresholds()` - 기본 임계값
  - [x] `test_custom_aging_thresholds()` - 커스텀 임계값
  - [x] `test_promote_aged_low_to_normal()` - LOW → NORMAL 승격
  - [x] `test_promote_updates_priority_in_payload()` - priority 필드 업데이트
  - [x] `test_no_promotion_for_fresh_tasks()` - 신규 태스크 미승격
  - [x] `test_cascading_promotion_normal_to_high()` - NORMAL → HIGH 승격
  - [x] `test_cascading_promotion_high_to_critical()` - HIGH → CRITICAL 승격
  - [x] `test_critical_tasks_not_promoted()` - CRITICAL은 승격 안함
- [x] `uv run pytest tests/core/test_priority_aging.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `app/core/priority.py` 수정
  - [x] `AgingConfig` dataclass 추가
  - [x] `get_next_priority()` 함수 추가
- [x] `app/core/queue.py` 수정
  - [x] `promote_aged_tasks()` 메서드 구현
  - [x] 승격 시 `enqueued_at` 리셋 (cascading 방지)
- [x] `uv run pytest tests/core/test_priority_aging.py -v` 실행 → 통과 확인 (10개)

---

### Day 4: NACK 우선순위 보존 ✅

#### RED: 테스트 작성
- [x] `tests/core/test_priority_nack.py` 신규 생성 (6개 테스트)
  - [x] `test_nack_returns_to_same_priority_queue()` - 원래 큐로 반환
  - [x] `test_nack_critical_returns_to_critical()` - CRITICAL 유지
  - [x] `test_nack_low_returns_to_low()` - LOW 유지
  - [x] `test_nack_increments_retry_count()` - retry_count 증가
  - [x] `test_nack_dlq_preserves_priority_info()` - DLQ priority 보존
  - [x] `test_get_all_queue_lengths()` - 큐 길이 조회
- [x] `uv run pytest tests/core/test_priority_nack.py -v` 실행 → 실패 확인

#### GREEN: 구현
- [x] `app/core/queue.py` 수정
  - [x] `nack_task()` 우선순위 보존 로직
  - [x] `retry_count` 증가 로직
  - [x] `get_all_queue_lengths()` 메서드 추가
- [x] `uv run pytest tests/core/test_priority_nack.py -v` 실행 → 통과 확인 (6개)

---

### Day 5: 통합 테스트 ✅

#### RED: 테스트 작성
- [x] `tests/integration/test_priority_queue_e2e.py` 신규 생성 (7개 테스트)
  - [x] `test_existing_enqueue_still_works()` - 하위호환성 (enqueue)
  - [x] `test_existing_dequeue_still_works()` - 하위호환성 (dequeue)
  - [x] `test_worker_processes_critical_first()` - Worker 우선순위 처리
  - [x] `test_worker_handles_mixed_arrivals()` - 혼합 도착 처리
  - [x] `test_aging_promotes_during_idle()` - Aging 통합
  - [x] `test_queue_stats_api()` - 큐 통계 API
  - [x] `test_queue_stats_with_dlq()` - DLQ 통계
- [x] `uv run pytest tests/integration/test_priority_queue_e2e.py -v` 실행 → 통과 확인 (7개)

#### GREEN: 구현
- [x] 모든 기능이 Day 1-4에서 이미 구현됨
- [ ] (선택) `app/workers/pool.py` 수정 - aging 태스크 추가 (추후 구현 가능)

---

### 검증 ✅
- [x] `uv run pytest tests/ -v` 전체 350개 통과 (311 + 39)
- [x] 우선순위 처리 순서 검증 (CRITICAL → HIGH → NORMAL → LOW)
- [x] 동일 우선순위 FIFO 검증
- [x] Starvation 방지 테스트 (Aging)
- [x] 하위호환성 검증

---

### 파일 구조 변경

```
backend/app/core/
├── priority.py          # 신규: TaskPriority, AgingConfig, get_queue_key, get_next_priority
└── queue.py             # 수정: 우선순위 지원, promote_aged_tasks, get_all_queue_lengths

backend/tests/core/
├── test_priority_queue.py     # 신규 (9개 테스트)
├── test_priority_dequeue.py   # 신규 (7개 테스트)
├── test_priority_aging.py     # 신규 (10개 테스트)
└── test_priority_nack.py      # 신규 (6개 테스트)

backend/tests/integration/
└── test_priority_queue_e2e.py # 신규 (7개 테스트)
```

**총 신규 테스트: 39개** ✅

---

## 인프라 설정

### Docker
- [ ] `Dockerfile` (Backend) 생성
- [ ] `Dockerfile` (Frontend) 생성
- [ ] `docker-compose.yml` 생성
- [ ] `docker-compose.prod.yml` 생성

### 환경 설정
- [ ] `.env.example` 생성
- [ ] `Makefile` 생성 (개발 명령어)

### CI/CD
- [ ] GitHub Actions 워크플로우 설정
- [ ] 테스트 자동화
- [ ] 린트 자동화

---

## 테스트 강화

### Backend 테스트
- [ ] 테스트 현황 파악
- [ ] `pytest.ini` 설정 확인
- [ ] 테스트 커버리지 측정 설정
- [ ] Quick Wins 테스트 작성
- [ ] 배치 처리 테스트 작성
- [ ] Queue ACK 패턴 테스트 작성
- [ ] Worker 단위 테스트 작성

### 통합 테스트
- [ ] 스캔 End-to-End 테스트
- [ ] 취소 기능 테스트
- [ ] 에러 복구 테스트

---

## 코드 품질

### 유틸리티 통합
- [ ] `utils/datetime.py` 생성
- [ ] `utc_now()` 함수 통합 (4개 파일에서 중복)
- [ ] 기존 파일들의 `utc_now()` import 변경

### 로깅 개선
- [ ] `crawler_service.py`의 `print()` → `logger` 변경
- [ ] 로깅 포맷 통일

### CORS 설정
- [ ] 프로덕션용 CORS 화이트리스트 설정
- [ ] 환경별 CORS 분기

---

## Frontend (미확인 - 점검 필요)

### 구조 확인
- [ ] `pages/` 디렉토리 존재 여부 확인
- [ ] `store/` 디렉토리 존재 여부 확인
- [ ] 라우팅 설정 확인

### 페이지 구현
- [ ] Dashboard 페이지
- [ ] Projects 페이지
- [ ] Targets 페이지
- [ ] Scans 페이지
- [ ] Results 페이지

### API 연동
- [ ] API 클라이언트 구현 확인
- [ ] React Query hooks 구현 확인
- [ ] 스캔 실행 UI
- [ ] 스캔 결과 표시 UI

---

## DAST 핵심 기능 (장기)

### 엔진 구조
- [ ] `backend/app/engine/` 디렉토리 생성
- [ ] `engine/scanner/` 디렉토리
- [ ] `engine/payload/` 디렉토리
- [ ] `engine/analyzer/` 디렉토리

### 취약점 스캐너
- [ ] `base_scanner.py` 구현
- [ ] `xss_scanner.py` 구현
- [ ] `sqli_scanner.py` 구현
- [ ] 페이로드 정의 (`payloads.json`)

### AI 분석
- [ ] LLM API 연동 (GPT-4o / Claude)
- [ ] 비즈니스 로직 취약점 분석

### 리포트
- [ ] 리포트 템플릿 설계
- [ ] PDF 출력 기능
- [ ] HTML 출력 기능

---

## 완료된 항목

### 분석 문서
- [x] PROJECT_STRUCTURE_ANALYSIS.md 작성
- [x] BACKEND_LOGIC_ANALYSIS.md 작성
- [x] SCAN_LOGIC_ANALYSIS.md 작성
- [x] SCAN_IMPROVEMENT_PLAN.md 작성

---

## 우선순위 요약

| 우선순위 | Phase | 예상 소요 | 효과 | 테스트 |
|----------|-------|----------|------|--------|
| ✅ P0 | Quick Wins | 30분 | 즉시 개선 | 완료 |
| ✅ P1 | 배치 처리 | 2-3일 | 성능 98%↑ | 완료 |
| ✅ P2 | 안정성 강화 | 5일 | 작업 손실 0% | 60개 |
| ✅ P3 | 아키텍처 개선 (TDD) | 5일 | 유지보수성↑ | 60개 |
| ✅ P4 | 확장성 확보 (TDD) | 5일 | 수평 확장 + 중복 방지 | 107개 |
| ✅ P4.5 | 우선순위 큐 (TDD) | 완료 | 우선순위 처리 + Starvation 방지 | 39개 |
| ⚪ P5 | DAST 핵심 기능 | 미정 | 제품 완성 | - |

**현재 상태: 350개 테스트 통과** ✅ (Phase 4.5 완료)

### Phase 4 Day 5 버그 수정 내역
- **Skipped Task Loss (Critical):** Lock 획득 실패 시 작업이 NACK되어 재시도 큐로 반환
- **SSRF 취약점 (High):** 내부 네트워크/메타데이터 엔드포인트 접근 차단
