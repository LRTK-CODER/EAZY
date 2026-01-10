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

## Phase 4: 확장성 확보 (3-4일)

> **목표:** 수평 확장 가능

### WorkerPool 구현
- [ ] `WorkerPool` 클래스 생성
- [ ] `num_workers` 설정 (환경변수 지원)
- [ ] `start()` 메서드
- [ ] `_run_worker()` 메서드
- [ ] Graceful Shutdown 핸들러 (`SIGTERM`, `SIGINT`)
- [ ] `shutdown_event` 구현

### 분산 잠금
- [ ] `core/lock.py` 생성
- [ ] `DistributedLock` 클래스 구현
- [ ] `acquire()` 메서드 (Redis SET NX)
- [ ] `release()` 메서드 (Lua 스크립트)
- [ ] Context Manager 지원
- [ ] `LockAcquisitionError` 예외

### Target 중복 스캔 방지
- [ ] CrawlWorker에 분산 잠금 적용
- [ ] 잠금 실패 시 재큐잉 로직

### 우선순위 큐 (선택)
- [ ] `PriorityTaskManager` 클래스
- [ ] 우선순위별 큐 (`high`, `normal`, `low`)
- [ ] `blpop` 다중 큐 지원

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
| 🟢 P4 | 확장성 확보 | 3-4일 | 수평 확장 | - |
| ⚪ P5 | DAST 핵심 기능 | 미정 | 제품 완성 | - |

**현재 상태: 204개 테스트 통과, 커버리지 78%**
