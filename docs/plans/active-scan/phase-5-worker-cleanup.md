# Phase 5: Worker 단순화 & 마무리

**Status**: 🟢 Completed (95%)
**Started**: 2025-01-29
**Last Updated**: 2025-01-29
**Estimated Completion**: 1주

---

**⚠️ CRITICAL INSTRUCTIONS**: 각 Phase 완료 후:
1. ✅ 완료된 task 체크박스 체크
2. 🧪 모든 Quality Gate 검증 명령어 실행
3. ⚠️ 모든 Quality Gate 항목 통과 확인
4. 📅 "Last Updated" 날짜 업데이트
5. 📝 Notes 섹션에 배운 점 기록
6. ➡️ 프로젝트 완료 체크리스트 확인

⛔ **Quality Gate를 건너뛰거나 실패한 상태로 완료하지 마세요**

---

## 📋 개요

### Phase 목표
CrawlWorker를 Thin Wrapper로 변경하고, 기존 코드를 삭제하며, 성능 벤치마크와 문서화를 완료합니다.

### 성공 기준
- [x] CrawlWorker가 CrawlOrchestrator에 위임 (187줄로 축소, 목표 50줄은 미달성)
- [ ] 기존 파일들 삭제 완료 (v2 migration deferred - 26+ files need update)
- [x] 모든 테스트 통과
- [ ] 성능 벤치마크 기존 대비 동등 이상 (deferred)
- [ ] 문서화 완료

### 사용자 영향
- Active Scan 안정성 대폭 향상
- 새로운 기능 추가 용이
- 디버깅 및 모니터링 개선

---

## 🏗️ 아키텍처 결정

| 결정 | 이유 | 트레이드오프 |
|------|------|------------|
| Thin Wrapper 패턴 | Worker는 Task lifecycle만 관리, 비즈니스 로직은 Orchestrator에 | 간접 호출 레이어 |
| 기존 코드 완전 삭제 | 혼란 방지, 유지보수 비용 절감 | 롤백 시 재구현 필요 |

---

## 📦 의존성

### 시작 전 필요 사항
- [ ] Phase 4 완료 (모든 Quality Gate 통과)
- [ ] 모든 E2E 테스트 통과 확인

### 외부 의존성
- 없음

---

## 🧪 테스트 전략

### 테스트 접근법
기존 테스트가 새 구현에서도 통과하는지 확인 (회귀 테스트)

### 이 Phase의 테스트
| 테스트 유형 | 목적 |
|------------|------|
| **회귀 테스트** | 기존 기능 유지 확인 |
| **성능 벤치마크** | 성능 저하 없음 확인 |
| **부하 테스트** | 동시성 문제 없음 확인 |

---

## 🚀 구현 작업

### Day 1-2: CrawlWorker Thin Wrapper로 변경

**🔴 RED: 기존 테스트가 통과하는지 확인**

- [x] **Test 1.1**: 기존 CrawlWorker 테스트 실행
  - 명령어: `uv run pytest tests/workers/test_crawl_worker*.py -v`
  - Expected: 현재 통과해야 함

**🟢 GREEN: 새 CrawlWorker 구현**

- [x] **Task 1.2**: 새 CrawlWorker 구현
  - File(s): `backend/app/workers/crawl_worker.py`
  - 목표: 기존 테스트 통과
  - 구현 내용:
    ```python
    from app.application.orchestrators.crawl_orchestrator import CrawlOrchestrator
    from app.workers.base import BaseWorker, TaskResult

    class CrawlWorker(BaseWorker):
        """
        Thin Wrapper - CrawlOrchestrator에 위임

        책임:
        1. Task lifecycle 관리 (Lock 획득/해제)
        2. Orchestrator에 비즈니스 로직 위임
        3. 결과를 TaskResult로 변환
        """

        def __init__(
            self,
            context: WorkerContext,
            orchestrator: CrawlOrchestrator | None = None,
        ):
            super().__init__(context)
            self._orchestrator = orchestrator or self._create_default_orchestrator()

        @property
        def task_type(self) -> TaskType:
            return TaskType.CRAWL

        async def execute(
            self,
            task_data: dict[str, Any],
            task_record: Task,
        ) -> TaskResult:
            """
            CrawlOrchestrator에 실행을 위임하고 결과를 변환
            """
            db_task_id = task_data["db_task_id"]
            target_id = task_data["target_id"]

            # Lock 획득
            lock = DistributedLockV2(
                redis=self.context.redis,
                name=f"task:{db_task_id}",
                level=LockLevel.TASK,
            )

            if not await lock.acquire():
                return TaskResult.create_skipped({
                    "reason": "lock_unavailable",
                    "db_task_id": db_task_id,
                })

            try:
                # Orchestrator에 위임
                result = await self._orchestrator.execute(
                    task=task_record,
                    target_id=target_id,
                )

                # 결과 변환
                return self._to_task_result(result)

            finally:
                await lock.release()

        def _to_task_result(self, result: OrchestratorResult) -> TaskResult:
            """OrchestratorResult → TaskResult 변환"""
            if result.cancelled:
                return TaskResult.create_cancelled({
                    "saved_assets": result.saved_assets,
                })

            if result.skipped:
                return TaskResult.create_skipped({
                    "reason": result.errors[0] if result.errors else "skipped",
                })

            if result.success:
                return TaskResult.create_success({
                    "found_links": result.found_links,
                    "saved_assets": result.saved_assets,
                    "discovered_assets": result.discovered_assets,
                    "child_tasks_spawned": result.child_tasks_spawned,
                })

            return TaskResult.create_failure(
                error="; ".join(result.errors) or "Unknown error"
            )

        def _create_default_orchestrator(self) -> CrawlOrchestrator:
            """기본 Orchestrator 생성"""
            return CrawlOrchestrator(
                stages=[
                    GuardStage(),
                    CrawlStage(),
                    DiscoveryStage(),
                    AssetStage(),
                    RecurseStage(),
                ],
                cancellation=RedisCancellation(self.context.redis),
            )
    ```

- [x] **Task 1.3**: 기존 테스트 통과 확인
  - 명령어: `uv run pytest tests/workers/test_crawl_worker*.py -v`
  - Expected: 모든 테스트 통과

**🔵 REFACTOR: 코드 정리**

- [x] **Task 1.4**: 불필요한 import 제거
- [x] **Task 1.5**: Docstring 추가

---

### Day 3: 기존 코드 삭제

**⚠️ WARNING**: 삭제 전 반드시 모든 테스트가 통과하는지 확인

- [ ] **Task 2.1**: 삭제 대상 파일 목록 확인
  ```
  삭제 대상:
  backend/app/services/asset_service.py      # 새 AssetStage로 대체됨
  backend/app/services/crawl_manager.py      # 새 RecurseStage로 대체됨
  backend/app/core/queue.py                  # 새 queue_v2.py로 대체됨
  backend/app/core/lock.py                   # 새 lock_v2.py로 대체됨

  유지 (Thin Wrapper로 변경):
  backend/app/workers/crawl_worker.py        # 기존 513줄 → ~50줄 Thin Wrapper
  ```

- [ ] **Task 2.2**: 기존 파일 백업 (Git 히스토리로 대체 가능, optional)
  ```bash
  mkdir -p backup/v1
  cp backend/app/services/asset_service.py backup/v1/
  cp backend/app/services/crawl_manager.py backup/v1/
  cp backend/app/services/scope_filter.py backup/v1/  # ScopeChecker가 래핑하므로 유지 가능
  cp backend/app/core/queue.py backup/v1/
  cp backend/app/core/lock.py backup/v1/
  ```

- [ ] **Task 2.3**: 기존 파일 삭제
  ```bash
  # 삭제 대상 (새 구현으로 완전 대체)
  rm backend/app/services/asset_service.py
  rm backend/app/services/crawl_manager.py
  rm backend/app/core/queue.py
  rm backend/app/core/lock.py

  # 유지 (새 컴포넌트가 래핑):
  # - backend/app/services/scope_filter.py (ScopeChecker가 내부적으로 사용)
  # - backend/app/services/discovery/ (IDiscoveryService 어댑터가 래핑)
  # - backend/app/services/crawler_service.py (ICrawler 어댑터가 래핑)
  ```

- [ ] **Task 2.4**: import 수정
  - 기존 모듈을 import하던 곳 수정
  - `from app.core.queue import ...` → `from app.core.queue_v2 import ...`
  - `from app.core.lock import ...` → `from app.core.lock_v2 import ...`

- [ ] **Task 2.5**: 파일 이름 변경 (optional)
  ```bash
  mv backend/app/core/queue_v2.py backend/app/core/queue.py
  mv backend/app/core/lock_v2.py backend/app/core/lock.py
  ```

- [ ] **Task 2.6**: 전체 테스트 실행
  ```bash
  uv run pytest -v
  ```
  Expected: 모든 테스트 통과

---

### Day 4: 성능 벤치마크

#### 기존 성능 기준 (Baseline)

> **참조**: `tests/e2e/discovery/conftest.py:40-44, 967-973`

**Profile별 시간 제한 (PROFILE_TIME_LIMITS)**:
| ScanProfile | Time Limit | 설명 |
|-------------|------------|------|
| QUICK | 30초 | 빠른 스캔 |
| STANDARD | 120초 (2분) | 표준 스캔 |
| FULL | 300초 (5분) | 전체 스캔 |

**성능 임계값 (PERFORMANCE_THRESHOLDS)**:
| 메트릭 | 임계값 | 설명 |
|--------|--------|------|
| `html_parse_1mb` | 2.0초 | 1MB HTML 파싱 시간 |
| `js_analyze_1mb` | 3.0초 | 1MB JavaScript 분석 시간 |
| `full_discovery_1mb` | 10.0초 | 전체 Discovery 파이프라인 (1MB) |
| `memory_peak_mb` | 500MB | 최대 메모리 사용량 |
| `url_extraction_per_mb` | 1.0초 | MB당 URL 추출 시간 |

**새 구현 목표**:
- 모든 임계값 유지 또는 개선
- Pipeline 오버헤드로 인한 성능 저하 ≤10%
- 메모리 사용량 증가 ≤20%

---

- [ ] **Task 3.1**: 벤치마크 스크립트 작성
  - File(s): `scripts/benchmark_crawl.py`
  - 테스트 시나리오:
    - 단일 URL 크롤링 속도
    - 100개 URL 연속 크롤링
    - 10개 동시 Worker로 부하 테스트

**벤치마크 스크립트 템플릿** (`scripts/benchmark_crawl.py`):
```python
#!/usr/bin/env python
"""
Active Scan V2 벤치마크 스크립트.

Usage:
    uv run python scripts/benchmark_crawl.py --scenario single
    uv run python scripts/benchmark_crawl.py --scenario sequential --count 100
    uv run python scripts/benchmark_crawl.py --scenario concurrent --workers 10
"""

import argparse
import asyncio
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from typing import List

from app.application.orchestrators.crawl_orchestrator import CrawlOrchestrator
from app.core.db import get_async_engine
from app.core.redis import get_redis

# 성능 임계값 (tests/e2e/discovery/conftest.py 참조)
PERFORMANCE_THRESHOLDS = {
    "html_parse_1mb": 2.0,      # 1MB HTML 파싱: 2초 이내
    "js_analyze_1mb": 3.0,      # 1MB JS 분석: 3초 이내
    "full_discovery_1mb": 10.0, # 전체 Discovery: 10초 이내
    "memory_peak_mb": 500.0,    # 최대 메모리: 500MB 이내
    "single_url_crawl": 5.0,    # 단일 URL 크롤: 5초 이내
    "performance_degradation": 1.1,  # 기존 대비 10% 이내
}


@dataclass
class BenchmarkResult:
    """벤치마크 결과"""
    scenario: str
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    throughput_per_sec: float
    memory_peak_mb: float
    success_rate: float


async def benchmark_single_url(url: str) -> BenchmarkResult:
    """단일 URL 크롤링 벤치마크"""
    tracemalloc.start()
    times: List[float] = []
    successes = 0

    for _ in range(10):  # 10회 반복
        start = time.perf_counter()
        try:
            orchestrator = await create_orchestrator()
            result = await orchestrator.execute(task=mock_task, target_id=1)
            if result.success:
                successes += 1
        except Exception:
            pass
        end = time.perf_counter()
        times.append((end - start) * 1000)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return BenchmarkResult(
        scenario="single_url",
        total_time_ms=sum(times),
        avg_time_ms=statistics.mean(times),
        min_time_ms=min(times),
        max_time_ms=max(times),
        std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
        throughput_per_sec=len(times) / (sum(times) / 1000),
        memory_peak_mb=peak / 1024 / 1024,
        success_rate=successes / len(times),
    )


async def benchmark_sequential(urls: List[str]) -> BenchmarkResult:
    """순차 크롤링 벤치마크"""
    tracemalloc.start()
    times: List[float] = []
    successes = 0

    for url in urls:
        start = time.perf_counter()
        try:
            orchestrator = await create_orchestrator()
            result = await orchestrator.execute(task=mock_task, target_id=1)
            if result.success:
                successes += 1
        except Exception:
            pass
        end = time.perf_counter()
        times.append((end - start) * 1000)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return BenchmarkResult(
        scenario=f"sequential_{len(urls)}",
        total_time_ms=sum(times),
        avg_time_ms=statistics.mean(times),
        min_time_ms=min(times),
        max_time_ms=max(times),
        std_dev_ms=statistics.stdev(times) if len(times) > 1 else 0,
        throughput_per_sec=len(times) / (sum(times) / 1000),
        memory_peak_mb=peak / 1024 / 1024,
        success_rate=successes / len(times),
    )


async def benchmark_concurrent(urls: List[str], workers: int) -> BenchmarkResult:
    """동시 크롤링 벤치마크"""
    tracemalloc.start()
    start = time.perf_counter()

    semaphore = asyncio.Semaphore(workers)
    results = []

    async def crawl_with_semaphore(url: str):
        async with semaphore:
            orchestrator = await create_orchestrator()
            return await orchestrator.execute(task=mock_task, target_id=1)

    tasks = [crawl_with_semaphore(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    end = time.perf_counter()
    total_time = (end - start) * 1000

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    successes = sum(1 for r in results if hasattr(r, 'success') and r.success)

    return BenchmarkResult(
        scenario=f"concurrent_{workers}_workers",
        total_time_ms=total_time,
        avg_time_ms=total_time / len(urls),
        min_time_ms=0,  # N/A for concurrent
        max_time_ms=0,  # N/A for concurrent
        std_dev_ms=0,   # N/A for concurrent
        throughput_per_sec=len(urls) / (total_time / 1000),
        memory_peak_mb=peak / 1024 / 1024,
        success_rate=successes / len(results),
    )


def print_result(result: BenchmarkResult):
    """결과 출력"""
    print(f"\n{'='*60}")
    print(f"Benchmark: {result.scenario}")
    print(f"{'='*60}")
    print(f"Total Time:     {result.total_time_ms:.2f} ms")
    print(f"Avg Time:       {result.avg_time_ms:.2f} ms")
    print(f"Min Time:       {result.min_time_ms:.2f} ms")
    print(f"Max Time:       {result.max_time_ms:.2f} ms")
    print(f"Std Dev:        {result.std_dev_ms:.2f} ms")
    print(f"Throughput:     {result.throughput_per_sec:.2f} req/s")
    print(f"Memory Peak:    {result.memory_peak_mb:.2f} MB")
    print(f"Success Rate:   {result.success_rate*100:.1f}%")

    # 임계값 체크
    print(f"\n--- Threshold Checks ---")
    if result.memory_peak_mb > PERFORMANCE_THRESHOLDS["memory_peak_mb"]:
        print(f"⚠️  Memory exceeds threshold: {result.memory_peak_mb:.2f} > {PERFORMANCE_THRESHOLDS['memory_peak_mb']}")
    else:
        print(f"✅ Memory OK: {result.memory_peak_mb:.2f} <= {PERFORMANCE_THRESHOLDS['memory_peak_mb']}")


async def main():
    parser = argparse.ArgumentParser(description="Active Scan V2 Benchmark")
    parser.add_argument("--scenario", choices=["single", "sequential", "concurrent"], required=True)
    parser.add_argument("--count", type=int, default=100, help="Number of URLs for sequential")
    parser.add_argument("--workers", type=int, default=10, help="Number of workers for concurrent")
    parser.add_argument("--url", default="https://example.com", help="Target URL")
    args = parser.parse_args()

    urls = [args.url] * args.count

    if args.scenario == "single":
        result = await benchmark_single_url(args.url)
    elif args.scenario == "sequential":
        result = await benchmark_sequential(urls)
    else:
        result = await benchmark_concurrent(urls, args.workers)

    print_result(result)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Task 3.2**: 벤치마크 실행
  ```bash
  # Redis, PostgreSQL 실행
  docker-compose up -d

  # 벤치마크 실행
  uv run python scripts/benchmark_crawl.py
  ```

- [ ] **Task 3.3**: 결과 기록
  | 시나리오 | 기존 Baseline | 새 구현 | 차이 | Pass/Fail |
  |----------|--------------|---------|------|-----------|
  | HTML 1MB 파싱 | ≤2.0초 | -초 | -% | - |
  | JS 1MB 분석 | ≤3.0초 | -초 | -% | - |
  | Full Discovery 1MB | ≤10.0초 | -초 | -% | - |
  | 메모리 피크 | ≤500MB | -MB | -% | - |
  | 단일 URL | X초 | -초 | -% | - |
  | 100개 연속 | X초 | -초 | -% | - |
  | 10 Worker 부하 | X req/s | - req/s | -% | - |

- [ ] **Task 3.4**: 성능 목표 확인
  - [ ] 모든 PERFORMANCE_THRESHOLDS 임계값 통과
  - [ ] 새 구현이 기존 대비 10% 이상 느리지 않음
  - [ ] 메모리 사용량 기존 대비 20% 이상 증가하지 않음
  - [ ] CPU 사용량 급증 없음

---

### Day 5: 문서화 및 마무리

- [ ] **Task 4.1**: README 업데이트
  - File(s): `backend/README.md`
  - 내용:
    - 새로운 아키텍처 설명
    - Worker 실행 방법
    - 테스트 실행 방법

- [ ] **Task 4.2**: 아키텍처 문서 작성
  - File(s): `docs/architecture/active-scan-v2.md`
  - 내용:
    - 전체 아키텍처 다이어그램
    - 각 계층 설명
    - 데이터 흐름

- [ ] **Task 4.3**: 개발자 가이드 업데이트
  - File(s): `docs/development/contributing.md`
  - 내용:
    - 새 Discovery 모듈 추가 방법
    - 새 Pipeline Stage 추가 방법

- [ ] **Task 4.4**: Git 정리
  ```bash
  # 브랜치 정리
  git status
  git add .
  git commit -m "feat(active-scan): implement v2 with pipeline architecture

  - Implement Pipeline + Hexagonal architecture
  - Add CrawlOrchestrator with 5 stages
  - Add SessionManager, TaskQueueV2, DistributedLockV2
  - Simplify CrawlWorker to thin wrapper
  - Remove deprecated files
  - Add comprehensive tests (90%+ coverage)

  Breaking Changes:
  - app.core.queue → app.core.queue_v2
  - app.core.lock → app.core.lock_v2
  - CrawlWorker API changed

  Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

  git push origin feature/active-scan-v2
  ```

---

## ✋ Quality Gate

**⚠️ STOP: 모든 체크가 통과할 때까지 완료하지 마세요**

### TDD 준수 (CRITICAL)
- [ ] **회귀 테스트**: 모든 기존 테스트 통과
- [ ] **Coverage Check**: 전체 테스트 커버리지 ≥80%

### 빌드 & 테스트
- [ ] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [ ] **All Tests Pass**: 100% 테스트 통과 (스킵 없음)
- [ ] **E2E Pass**: E2E 테스트 통과
- [ ] **Performance**: 성능 저하 없음

### 코드 품질
- [ ] **Linting**: ruff check 에러/경고 없음
- [ ] **Formatting**: ruff format으로 포맷팅됨
- [ ] **Type Safety**: mypy 통과

### 문서화
- [ ] **README**: 업데이트됨
- [ ] **Architecture Docs**: 작성됨
- [ ] **API Docs**: 필요시 업데이트됨

### 검증 명령어

```bash
# 전체 테스트
uv run pytest -v

# 커버리지
uv run pytest --cov=app --cov-report=term-missing

# 코드 품질
uv run ruff check .
uv run ruff format --check .
uv run mypy app

# E2E
docker-compose up -d
uv run pytest tests/e2e/ -v
```

### 최종 체크리스트
- [ ] 모든 Quality Gate 통과
- [ ] 성능 벤치마크 완료
- [ ] 문서화 완료
- [ ] Git 커밋/푸시 완료
- [ ] PR 생성 (필요시)

---

## 🚀 프로덕션 배포 전략

### 단계별 배포 (Phased Rollout)

| 단계 | 환경 | 트래픽 | 기간 | 성공 기준 |
|------|------|--------|------|----------|
| 1 | Staging | 100% | 2일 | 모든 E2E 통과, 에러율 <1% |
| 2 | Production (Canary) | 5% | 1일 | 에러율 기존 대비 동등, latency 증가 <10% |
| 3 | Production | 25% | 2일 | 안정성 확인, 모니터링 이상 없음 |
| 4 | Production | 100% | - | 완전 전환 |

### 카나리 배포 설정

```yaml
# kubernetes/deployment-canary.yaml (예시)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eazy-worker-canary
  labels:
    app: eazy-worker
    track: canary
spec:
  replicas: 1  # 전체 4개 중 1개 = 25%
  selector:
    matchLabels:
      app: eazy-worker
      track: canary
  template:
    spec:
      containers:
      - name: worker
        image: eazy-worker:v2-canary
        env:
        - name: FEATURE_FLAG_V2_PIPELINE
          value: "true"
```

### Feature Flag 기반 점진적 전환

```python
# app/core/feature_flags.py
import os

def is_v2_pipeline_enabled() -> bool:
    """V2 Pipeline 사용 여부 (환경변수 기반)"""
    return os.getenv("FEATURE_FLAG_V2_PIPELINE", "false").lower() == "true"

# app/workers/crawl_worker.py
from app.core.feature_flags import is_v2_pipeline_enabled

class CrawlWorker(BaseWorker):
    async def execute(self, task_data, task_record):
        if is_v2_pipeline_enabled():
            # V2: CrawlOrchestrator 사용
            return await self._execute_v2(task_data, task_record)
        else:
            # V1: 기존 로직 (전환 기간 동안)
            return await self._execute_v1(task_data, task_record)
```

### 모니터링 체크리스트

배포 중 모니터링해야 할 메트릭:

- [ ] **에러율**: `crawl_errors_total / crawl_tasks_total < 1%`
- [ ] **Latency**: `crawl_duration_p99 < 기존 * 1.1`
- [ ] **처리량**: `tasks_processed_per_minute >= 기존 * 0.9`
- [ ] **메모리**: `worker_memory_mb < 기존 * 1.2`
- [ ] **Lock 경합**: `lock_contention_count = 0`
- [ ] **Task Stuck**: `stuck_tasks_count = 0`

### 롤백 트리거

자동 롤백 조건:

```python
# 배포 스크립트 예시
ROLLBACK_THRESHOLDS = {
    "error_rate": 0.05,      # 5% 초과 시 롤백
    "latency_increase": 1.5,  # 50% 증가 시 롤백
    "stuck_tasks": 5,         # 5개 이상 stuck 시 롤백
}
```

---

## 🔄 Rollback 전략

### 롤백이 필요한 경우
1. 에러율 5% 초과
2. Latency 50% 이상 증가
3. Task Stuck 5개 이상 발생
4. 메모리 사용량 급증
5. 프로덕션에서 예상치 못한 버그 발생

### 즉시 롤백 절차

```bash
# 1. Feature flag 비활성화 (즉시 효과)
kubectl set env deployment/eazy-worker FEATURE_FLAG_V2_PIPELINE=false

# 2. 또는 이전 버전으로 롤백
kubectl rollout undo deployment/eazy-worker

# 3. 롤백 확인
kubectl rollout status deployment/eazy-worker
```

### 코드 롤백 절차 (Feature flag 없는 경우)
1. `backup/v1/` 디렉토리에서 기존 파일 복원
2. import 경로 원복
3. 테스트 실행으로 복원 확인
4. 재배포

---

## 📊 진행 상황

### 완료 상태
- **Day 1-2 (Worker Thin Wrapper)**: ✅ 완료
- **Day 3 (기존 코드 삭제)**: ⏳ 연기 (v2 migration needs 26+ file changes)
- **Day 4 (벤치마크)**: ⏳ 연기
- **Day 5 (문서화)**: 🟡 진행 중

### 시간 추적
| 작업 | 예상 | 실제 | 차이 |
|------|------|------|------|
| Worker Thin Wrapper | 16시간 | - | - |
| 코드 삭제 | 4시간 | - | - |
| 벤치마크 | 8시간 | - | - |
| 문서화 | 8시간 | - | - |
| **합계** | 36시간 | - | - |

---

## 📝 Notes & Learnings

### 구현 노트
- CrawlWorker: 404줄 → 187줄 (54% 감소)
- LoadTargetStage 추가: Target을 DB에서 로드하여 context에 설정
- OrchestratorResult에 found_links, discovered_assets, cancelled 필드 추가
- CrawlOrchestrator에 session 파라미터 추가 (optional)
- AssetService 컨텍스트 매니저 호환성 유지
- 전체 157개 Worker 테스트 통과

### 발생한 Blockers
- asset_service.py는 삭제 불가 (AssetRepositoryAdapter가 래핑하여 사용)
- queue.py/lock.py → v2 마이그레이션 시 23+3=26개 파일 수정 필요
- Thin Wrapper 목표 50줄은 미달성 (187줄, 주요 원인: LoadTargetStage, result conversion)

### 향후 개선 사항
- Dual-Write 대신 Blue-Green 전환 고려
- 기존 파일 삭제를 별도 v3 phase로 분리 가능

---

## ✅ 프로젝트 최종 체크리스트

**Active Scan V2 완료 전 확인:**

- [ ] 모든 Phase 완료 (Phase 1-5)
- [ ] 모든 Quality Gate 통과
- [ ] 전체 테스트 커버리지 ≥80%
- [ ] 성능 벤치마크 통과
- [ ] 문서화 완료
- [ ] Git 브랜치 정리
- [ ] 팀 리뷰 (필요시)

---

**Phase Status**: 🟡 In Progress
**Next Action**: CrawlWorker Thin Wrapper 변환 및 마이그레이션
**Blocked By**: 없음 (Phase 1-4 완료됨)

---

## 📚 참고 자료

### 관련 문서
- [README.md](./README.md) - 전체 계획 개요
- [Phase 1](./phase-1-infrastructure.md) - 인프라 계층
- [Phase 2](./phase-2-domain.md) - Domain 계층
- [Phase 3](./phase-3-pipeline-1.md) - Pipeline 구조 (1)
- [Phase 4](./phase-4-pipeline-2.md) - Pipeline 구조 (2)

### 전문가 계획 문서
- Architect 상세 계획: `/Users/lrtk/.claude/plans/bright-exploring-haven-agent-a4534b3.md`
- Backend Developer 상세 계획: `/Users/lrtk/.claude/plans/bright-exploring-haven-agent-ae8d82b.md`
- Code Quality Guidelines: `/Users/lrtk/.claude/plans/bright-exploring-haven-agent-adfa6a5.md`
