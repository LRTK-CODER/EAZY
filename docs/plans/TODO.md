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

## Phase 1: 배치 처리 (2-3일)

> **목표:** DB 부하 98% 감소

### AssetService 리팩토링
- [ ] `BATCH_SIZE` 상수 추가 (50개)
- [ ] `_pending_assets` 리스트 추가
- [ ] `_pending_discoveries` 리스트 추가
- [ ] `flush()` 메서드 구현
- [ ] `__aenter__` / `__aexit__` 구현 (Context Manager)
- [ ] `process_asset()` 수정 - 즉시 커밋 제거

### Worker 수정
- [ ] `AssetService`를 Context Manager로 사용하도록 변경
- [ ] 배치 처리 로직 적용

### 테스트
- [ ] 배치 저장 단위 테스트 작성
- [ ] 성능 비교 테스트 (Before/After COMMIT 횟수)

---

## Phase 2: 안정성 강화 (3-4일)

> **목표:** 작업 손실 0%

### Redis Queue 개선
- [ ] `processing_queue` 추가 (`task_queue:processing`)
- [ ] `dequeue_task()` → `brpoplpush` 사용
- [ ] `ack_task()` 메서드 구현
- [ ] `nack_task()` 메서드 구현
- [ ] Dead Letter Queue 추가 (`task_queue:dlq`)
- [ ] `recover_orphaned_tasks()` 메서드 구현

### 에러 분류 시스템
- [ ] `core/errors.py` 생성
- [ ] `ErrorCategory` Enum 정의 (RETRYABLE, PERMANENT, TRANSIENT)
- [ ] `classify_error()` 함수 구현

### 재시도 로직
- [ ] `core/retry.py` 생성
- [ ] `@with_retry` 데코레이터 구현
- [ ] Exponential Backoff 로직
- [ ] Jitter 추가

### Worker 수정
- [ ] ACK/NACK 패턴 적용
- [ ] 재시도 로직 적용

---

## Phase 3: 아키텍처 개선 (4-5일)

> **목표:** 유지보수성 향상, 코드 중복 제거

### 디렉토리 구조
- [ ] `backend/app/workers/` 디렉토리 생성
- [ ] `workers/__init__.py` 생성

### BaseWorker 구현
- [ ] `workers/base.py` 생성
- [ ] `BaseWorker` 추상 클래스 구현
- [ ] `execute()` 추상 메서드 정의
- [ ] `process()` 공통 로직 구현
- [ ] `_get_task_record()` 헬퍼 메서드
- [ ] `_update_status()` 헬퍼 메서드
- [ ] `_complete_task()` 헬퍼 메서드
- [ ] `_fail_task()` 헬퍼 메서드

### CrawlWorker 구현
- [ ] `workers/crawl_worker.py` 생성
- [ ] `CrawlWorker` 클래스 구현
- [ ] 의존성 주입 지원 (CrawlerService, AssetService)
- [ ] `execute()` 메서드 구현
- [ ] `_check_cancellation()` 메서드

### Worker Runner
- [ ] `workers/runner.py` 생성
- [ ] `WORKER_REGISTRY` 딕셔너리
- [ ] `process_one_task()` 함수
- [ ] 메인 실행 로직

### 기존 코드 제거
- [ ] `worker.py`의 `process_task()` 제거
- [ ] `worker.py`의 `process_one_task()` 제거
- [ ] 기존 `worker.py` → 새 구조로 마이그레이션

### 테스트
- [ ] `BaseWorker` 단위 테스트
- [ ] `CrawlWorker` 단위 테스트 (Mock 사용)

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

| 우선순위 | Phase | 예상 소요 | 효과 |
|----------|-------|----------|------|
| 🔴 P0 | Quick Wins | 30분 | 즉시 개선 |
| 🔴 P1 | 배치 처리 | 2-3일 | 성능 98%↑ |
| 🟠 P2 | 안정성 강화 | 3-4일 | 작업 손실 0% |
| 🟡 P3 | 아키텍처 개선 | 4-5일 | 유지보수성↑ |
| 🟢 P4 | 확장성 확보 | 3-4일 | 수평 확장 |
| ⚪ P5 | DAST 핵심 기능 | 미정 | 제품 완성 |
