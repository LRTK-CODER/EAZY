# EAZY 스캔 로직 개선 계획서

> **작성일:** 2026-01-10
> **분석 방법:** Sequential-Thinking MCP 기반 다중 전문가 토론
> **참조 문서:**
> - [PROJECT_STRUCTURE_ANALYSIS.md](./PROJECT_STRUCTURE_ANALYSIS.md)
> - [BACKEND_LOGIC_ANALYSIS.md](./BACKEND_LOGIC_ANALYSIS.md)
> - [SCAN_LOGIC_ANALYSIS.md](./SCAN_LOGIC_ANALYSIS.md)

---

## 1. 개요

### 1.1 현재 상태 요약

| 영역 | 현재 점수 | 주요 문제점 |
|-----|----------|-----------|
| 성능 | 2.5/10 | Asset당 2회 COMMIT, Polling 비효율 |
| 안정성 | 3.0/10 | LPOP 후 크래시 시 작업 손실 |
| 유지보수성 | 3.5/10 | 307줄 단일 파일, 90% 코드 중복 |
| 확장성 | 2.0/10 | 단일 Worker, 동시성 제어 없음 |
| 테스트 용이성 | 2.0/10 | 하드코딩된 의존성 |
| **종합** | **3.8/10** | - |

### 1.2 개선 목표

| 영역 | 목표 점수 | 예상 향상 |
|-----|----------|----------|
| 성능 | 8.0/10 | +5.5점 |
| 안정성 | 8.5/10 | +5.5점 |
| 유지보수성 | 8.0/10 | +4.5점 |
| 확장성 | 8.5/10 | +6.5점 |
| 테스트 용이성 | 8.0/10 | +6.0점 |
| **종합** | **8.2/10** | **+4.4점** |

---

## 2. 개선 우선순위 매트릭스

| 우선순위 | 개선 항목 | 노력 | 효과 | ROI |
|---------|----------|------|------|-----|
| **P0** | import 정리, BLPOP 적용 | 낮음 | 중간 | ★★★★★ |
| **P1** | 코드 중복 제거 | 중간 | 높음 | ★★★★☆ |
| **P2** | 배치 COMMIT | 중간 | 높음 | ★★★★☆ |
| **P3** | BRPOPLPUSH + ACK | 중간 | 높음 | ★★★★☆ |
| **P4** | Worker 모듈 분리 | 높음 | 높음 | ★★★☆☆ |
| **P5** | 브라우저 풀링 | 높음 | 중간 | ★★☆☆☆ |

---

## 3. Phase 1: Quick Wins (1-2일)

### 3.1 import 정리 (5분)

**현재 문제:** `import json`이 함수 내부에 6회 중복

```python
# Before (worker.py:89, 132, 141, 217, 260, 272)
async def process_task(...):
    ...
    import json  # 함수 내부 import
    task_record.result = json.dumps(...)
```

```python
# After: 파일 상단으로 이동
import json  # 추가
import asyncio
import logging
from redis.asyncio import Redis
...
```

### 3.2 BLPOP 적용 (15분)

**현재 문제:** LPOP + sleep(1) → CPU 낭비, 1초 지연

```python
# Before (queue.py)
async def dequeue_task(self) -> dict | None:
    data = await self.redis.lpop(self.queue_name)
    if data:
        return json.loads(data)
    return None

# Worker에서
if not processed:
    await asyncio.sleep(1)  # 낭비
```

```python
# After: BLPOP으로 즉시 응답
async def dequeue_task(self, timeout: int = 5) -> dict | None:
    """Block until task available or timeout."""
    result = await self.redis.blpop(self.queue_name, timeout=timeout)
    if result:
        _, data = result
        return json.loads(data)
    return None
```

### 3.3 명시적 타임아웃 (10분)

```python
# crawler_service.py 개선
async def crawl(self, url: str, timeout: int = 30000) -> tuple[list[str], dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        context.set_default_timeout(timeout)  # 명시적 타임아웃
        ...
```

**예상 효과:** 즉시 적용 가능, CPU 사용량 감소, 응답성 향상

---

## 4. Phase 2: 배치 처리 (2-3일)

### 4.1 현재 문제

- Asset 1개당 2회 COMMIT (Asset + AssetDiscovery)
- 100개 링크 → 200회 COMMIT → DB 병목

### 4.2 해결책: 배치 처리 패턴

```python
# asset_service.py 개선안
class AssetService:
    BATCH_SIZE = 50  # 배치 크기

    def __init__(self, session: AsyncSession):
        self.session = session
        self._pending_assets: list[Asset] = []
        self._pending_discoveries: list[AssetDiscovery] = []

    async def process_asset(self, ...) -> Asset:
        """자산을 배치에 추가 (즉시 커밋하지 않음)"""
        content_hash = self._compute_hash(url, method, request_spec)

        # 기존 자산 확인
        existing = await self._get_existing_asset(target_id, content_hash)
        if existing:
            discovery = AssetDiscovery(
                asset_id=existing.id,
                task_id=task_id,
                source=source
            )
            self._pending_discoveries.append(discovery)
        else:
            asset = Asset(...)
            self._pending_assets.append(asset)

        # 배치 크기 도달 시 플러시
        if len(self._pending_assets) >= self.BATCH_SIZE:
            await self.flush()

        return asset

    async def flush(self) -> None:
        """누적된 배치를 한 번에 커밋"""
        if self._pending_assets:
            self.session.add_all(self._pending_assets)
        if self._pending_discoveries:
            self.session.add_all(self._pending_discoveries)

        await self.session.commit()  # 단 1회 COMMIT

        self._pending_assets.clear()
        self._pending_discoveries.clear()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        """컨텍스트 종료 시 잔여 배치 플러시"""
        await self.flush()
```

### 4.3 Worker 수정

```python
# worker.py
async with AssetService(session) as asset_service:
    for link in links:
        await asset_service.process_asset(...)
    # __aexit__에서 자동 flush
```

**예상 효과:**
- 100개 링크: 200 COMMIT → 2~3 COMMIT
- DB 부하 98% 감소
- 처리 속도 5~10배 향상

---

## 5. Phase 3: 안정성 강화 (3-4일)

### 5.1 BRPOPLPUSH + ACK 패턴

**현재 문제:**
- LPOP 후 Worker 크래시 → 작업 영구 손실
- 재시도 로직 없음
- 작업 추적 불가

```python
# queue.py 개선안
class TaskManager:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.queue_name = "task_queue"
        self.processing_queue = "task_queue:processing"  # 신규
        self.max_retries = 3

    async def dequeue_task(self, timeout: int = 5) -> dict | None:
        """원자적으로 작업을 processing 큐로 이동"""
        result = await self.redis.brpoplpush(
            self.queue_name,
            self.processing_queue,
            timeout=timeout
        )
        if result:
            return json.loads(result)
        return None

    async def ack_task(self, task_data: dict) -> None:
        """작업 완료 시 processing 큐에서 제거"""
        await self.redis.lrem(
            self.processing_queue,
            1,
            json.dumps(task_data)
        )

    async def nack_task(self, task_data: dict, requeue: bool = True) -> None:
        """작업 실패 시 재큐잉 또는 DLQ 이동"""
        await self.redis.lrem(self.processing_queue, 1, json.dumps(task_data))

        retry_count = task_data.get("retry_count", 0)
        if requeue and retry_count < self.max_retries:
            task_data["retry_count"] = retry_count + 1
            await self.enqueue_task(task_data)
        else:
            # Dead Letter Queue로 이동
            await self.redis.rpush("task_queue:dlq", json.dumps(task_data))

    async def recover_orphaned_tasks(self, stale_seconds: int = 300) -> int:
        """오래된 processing 작업 복구 (Worker 크래시 대응)"""
        tasks = await self.redis.lrange(self.processing_queue, 0, -1)
        recovered = 0
        for task_json in tasks:
            task = json.loads(task_json)
            if self._is_stale(task, stale_seconds):
                await self.nack_task(task, requeue=True)
                recovered += 1
        return recovered
```

### 5.2 Exponential Backoff + 에러 분류

```python
# core/errors.py (신규)
from enum import Enum

class ErrorCategory(Enum):
    RETRYABLE = "retryable"      # 재시도 가능 (네트워크, 타임아웃)
    PERMANENT = "permanent"       # 재시도 불가 (잘못된 URL, 인증 실패)
    TRANSIENT = "transient"       # 일시적 (DB 연결, Redis 연결)

def classify_error(error: Exception) -> ErrorCategory:
    """에러를 카테고리로 분류"""
    if isinstance(error, (TimeoutError, ConnectionError, OSError)):
        return ErrorCategory.RETRYABLE
    if isinstance(error, (ValueError, KeyError)):
        return ErrorCategory.PERMANENT
    if "connection" in str(error).lower():
        return ErrorCategory.TRANSIENT
    return ErrorCategory.RETRYABLE  # 기본값: 재시도
```

```python
# core/retry.py (신규)
import asyncio
import random
from functools import wraps

def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """Exponential backoff 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    category = classify_error(e)

                    if category == ErrorCategory.PERMANENT:
                        raise  # 즉시 실패

                    if attempt < max_retries:
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        # Jitter 추가로 thundering herd 방지
                        delay *= (0.5 + random.random())

                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)

            raise last_error
        return wrapper
    return decorator
```

**예상 효과:**
- 작업 손실 0%
- 자동 재시도로 일시적 오류 복구
- DLQ로 문제 작업 분리/분석 가능

---

## 6. Phase 4: 아키텍처 개선 (4-5일)

### 6.1 디렉토리 구조

```
backend/app/
├── workers/                    # 신규 디렉토리
│   ├── __init__.py
│   ├── base.py                # 기반 Worker 클래스
│   ├── crawl_worker.py        # 크롤 작업 처리
│   ├── attack_worker.py       # 공격 작업 처리 (미래)
│   └── runner.py              # 메인 실행 루프
├── core/
│   ├── queue.py               # 큐 관리 (기존)
│   ├── errors.py              # 에러 분류 (신규)
│   ├── retry.py               # 재시도 로직 (신규)
│   └── lock.py                # 분산 잠금 (신규)
└── services/
    └── ...                    # 비즈니스 로직 (기존)
```

### 6.2 BaseWorker 추상 클래스

```python
# workers/base.py
from abc import ABC, abstractmethod
from typing import Any

class BaseWorker(ABC):
    """작업 처리를 위한 기반 클래스"""

    def __init__(self, session: AsyncSession, task_manager: TaskManager):
        self.session = session
        self.task_manager = task_manager

    @abstractmethod
    async def execute(self, task_data: dict) -> dict:
        """작업 실행 (서브클래스에서 구현)"""
        pass

    async def process(self, task_data: dict) -> None:
        """공통 처리 로직: 상태 업데이트 + 실행 + 결과 저장"""
        task_record = await self._get_task_record(task_data["db_task_id"])

        try:
            await self._update_status(task_record, TaskStatus.RUNNING)
            result = await self.execute(task_data)
            await self._complete_task(task_record, result)
            await self.task_manager.ack_task(task_data)
        except Exception as e:
            await self._fail_task(task_record, str(e))
            await self.task_manager.nack_task(task_data)
            raise

    async def _get_task_record(self, task_id: int) -> Task:
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def _update_status(self, task: Task, status: TaskStatus) -> None:
        task.status = status
        if status == TaskStatus.RUNNING:
            task.started_at = utc_now()
        self.session.add(task)
        await self.session.commit()

    async def _complete_task(self, task: Task, result: dict) -> None:
        task.status = TaskStatus.COMPLETED
        task.completed_at = utc_now()
        task.result = json.dumps(result)
        self.session.add(task)
        await self.session.commit()

    async def _fail_task(self, task: Task, error: str) -> None:
        task.status = TaskStatus.FAILED
        task.completed_at = utc_now()
        task.result = json.dumps({"error": error})
        self.session.add(task)
        await self.session.commit()
```

### 6.3 CrawlWorker 구현

```python
# workers/crawl_worker.py
class CrawlWorker(BaseWorker):
    """크롤링 작업 전용 Worker"""

    def __init__(
        self,
        session: AsyncSession,
        task_manager: TaskManager,
        crawler_service: CrawlerService = None,
        asset_service: AssetService = None
    ):
        super().__init__(session, task_manager)
        # 의존성 주입으로 테스트 용이
        self.crawler = crawler_service or CrawlerService()
        self.asset_service = asset_service or AssetService(session)

    async def execute(self, task_data: dict) -> dict:
        target = await self.session.get(Target, task_data["target_id"])
        if not target:
            raise ValueError(f"Target {task_data['target_id']} not found")

        links, http_data = await self.crawler.crawl(target.url)

        saved_count = 0
        async with self.asset_service:
            for link in links:
                if await self._check_cancellation(task_data["db_task_id"]):
                    return {
                        "cancelled": True,
                        "processed_links": saved_count,
                        "total_links": len(links)
                    }

                link_http_data = http_data.get(link, {})
                await self.asset_service.process_asset(
                    target_id=task_data["target_id"],
                    task_id=task_data["db_task_id"],
                    url=link,
                    method=link_http_data.get("request", {}).get("method", "GET"),
                    type=AssetType.URL,
                    source=AssetSource.HTML,
                    request_spec=link_http_data.get("request"),
                    response_spec=link_http_data.get("response"),
                    parameters=link_http_data.get("parameters")
                )
                saved_count += 1

        return {"found_links": len(links), "saved_assets": saved_count}

    async def _check_cancellation(self, task_id: int) -> bool:
        cancel_key = f"task:{task_id}:cancel"
        return await self.task_manager.redis.get(cancel_key) is not None
```

### 6.4 Worker Registry 패턴

```python
# workers/runner.py
from app.workers.crawl_worker import CrawlWorker
from app.models.task import TaskType

WORKER_REGISTRY = {
    TaskType.CRAWL: CrawlWorker,
    # TaskType.ATTACK: AttackWorker,  # 미래 확장
    # TaskType.ANALYSIS: AnalysisWorker,
}

async def process_one_task(session: AsyncSession, task_manager: TaskManager) -> bool:
    task_data = await task_manager.dequeue_task()
    if not task_data:
        return False

    task_type = TaskType(task_data.get("type"))
    worker_class = WORKER_REGISTRY.get(task_type)

    if not worker_class:
        logger.warning(f"Unknown task type: {task_type}")
        return True

    worker = worker_class(session, task_manager)
    await worker.process(task_data)
    return True
```

**예상 효과:**
- 코드 중복 100% 제거
- 307줄 → ~80줄/파일로 분할
- 테스트 용이 (Mock 주입 가능)
- 새 작업 타입 추가 용이

---

## 7. Phase 5: 확장성 확보 (3-4일)

### 7.1 다중 Worker 지원

```python
# workers/runner.py
import os
import signal

class WorkerPool:
    """다중 Worker 관리자"""

    def __init__(self, num_workers: int = None):
        self.num_workers = num_workers or int(os.getenv("WORKER_COUNT", 4))
        self.workers: list[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()
        self.redis = None
        self.task_manager = None

    async def start(self):
        """Worker 풀 시작"""
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.task_manager = TaskManager(self.redis)

        for i in range(self.num_workers):
            task = asyncio.create_task(
                self._run_worker(worker_id=i),
                name=f"worker-{i}"
            )
            self.workers.append(task)

        # Graceful shutdown 핸들러
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_shutdown)

        logger.info(f"Started {self.num_workers} workers")
        await asyncio.gather(*self.workers, return_exceptions=True)

    async def _run_worker(self, worker_id: int):
        """개별 Worker 실행 루프"""
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession)

        logger.info(f"Worker {worker_id} started")

        while not self.shutdown_event.is_set():
            try:
                async with async_session() as session:
                    await process_one_task(session, self.task_manager)
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"Worker {worker_id} stopped")
        await engine.dispose()

    def _handle_shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutdown signal received")
        self.shutdown_event.set()

# 실행
if __name__ == "__main__":
    pool = WorkerPool()
    asyncio.run(pool.start())
```

### 7.2 분산 잠금 (Target 중복 스캔 방지)

```python
# core/lock.py (신규)
import uuid

class DistributedLock:
    """Redis 기반 분산 잠금"""

    def __init__(self, redis: Redis, name: str, ttl: int = 300):
        self.redis = redis
        self.name = f"lock:{name}"
        self.ttl = ttl
        self.token = str(uuid.uuid4())

    async def acquire(self) -> bool:
        """잠금 획득 시도"""
        return await self.redis.set(
            self.name,
            self.token,
            nx=True,  # 존재하지 않을 때만
            ex=self.ttl
        )

    async def release(self) -> bool:
        """잠금 해제 (본인 토큰만)"""
        script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        else
            return 0
        end
        """
        return await self.redis.eval(script, 1, self.name, self.token)

    async def __aenter__(self):
        if not await self.acquire():
            raise LockAcquisitionError(f"Cannot acquire lock: {self.name}")
        return self

    async def __aexit__(self, *args):
        await self.release()

class LockAcquisitionError(Exception):
    pass
```

### 7.3 사용 예시

```python
# workers/crawl_worker.py
async def execute(self, task_data: dict) -> dict:
    target_id = task_data["target_id"]

    try:
        async with DistributedLock(self.task_manager.redis, f"target:{target_id}"):
            # 이 Target은 현재 Worker만 처리
            return await self._do_crawl(task_data)
    except LockAcquisitionError:
        # 다른 Worker가 처리 중 → 재큐잉
        raise RetryableError("Target already being processed")
```

### 7.4 우선순위 큐 (선택)

```python
# core/queue.py 확장
class PriorityTaskManager(TaskManager):
    """우선순위 지원 큐"""

    PRIORITY_QUEUES = ["task_queue:high", "task_queue:normal", "task_queue:low"]

    async def enqueue_task(self, task: dict, priority: str = "normal"):
        queue = f"task_queue:{priority}"
        await self.redis.rpush(queue, json.dumps(task))

    async def dequeue_task(self, timeout: int = 5) -> dict | None:
        """우선순위 순서로 작업 가져오기"""
        result = await self.redis.blpop(self.PRIORITY_QUEUES, timeout=timeout)
        if result:
            _, data = result
            return json.loads(data)
        return None
```

**예상 효과:**
- 처리량 N배 증가 (Worker 수 비례)
- Target 중복 스캔 방지
- Graceful shutdown으로 작업 손실 방지
- 긴급 스캔 우선 처리 가능

---

## 8. 구현 로드맵 요약

### 8.1 타임라인

```
Week 1:
├── Day 1-2: Phase 1 (Quick Wins)
│   ├── import 정리
│   ├── BLPOP 적용
│   └── 명시적 타임아웃
└── Day 3-5: Phase 2 (배치 처리)
    ├── AssetService 리팩토링
    └── 배치 COMMIT 구현

Week 2:
├── Day 1-4: Phase 3 (안정성)
│   ├── BRPOPLPUSH + ACK 패턴
│   ├── Dead Letter Queue
│   └── 재시도 로직
└── Day 5: 테스트 및 검증

Week 3:
├── Day 1-5: Phase 4 (아키텍처)
│   ├── workers/ 디렉토리 생성
│   ├── BaseWorker, CrawlWorker
│   └── 단위 테스트 작성

Week 4:
├── Day 1-4: Phase 5 (확장성)
│   ├── WorkerPool 구현
│   ├── 분산 잠금
│   └── 우선순위 큐
└── Day 5: 통합 테스트 및 배포
```

### 8.2 즉시 실행 가능한 체크리스트

- [ ] `worker.py` 상단에 `import json` 추가 및 함수 내 import 제거
- [ ] `queue.py`의 `lpop` → `blpop` 변경
- [ ] `crawler_service.py`에 명시적 타임아웃 추가
- [ ] `asset_service.py`에 배치 처리 로직 추가
- [ ] `queue.py`에 ACK/NACK 메서드 추가
- [ ] `workers/` 디렉토리 생성 및 모듈 분리
- [ ] 단위 테스트 작성

---

## 9. 주의사항

### 9.1 테스트 우선
각 Phase 완료 후 반드시 테스트 실행

### 9.2 점진적 배포
한 번에 모든 변경 배포 금지. Phase별로 배포 및 검증

### 9.3 모니터링
성능 메트릭 수집 후 효과 측정 필수

### 9.4 롤백 계획
문제 발생 시 즉시 복구 가능하도록 이전 버전 백업

---

## 10. 기대 효과 요약

| 지표 | 현재 | 개선 후 | 향상률 |
|-----|------|--------|-------|
| DB COMMIT 횟수 | N×2회/Task | ~3회/Task | 98% 감소 |
| 작업 손실률 | 있음 | 0% | 100% 개선 |
| 코드 라인 | 307줄 | ~80줄/모듈 | 74% 감소 |
| Worker 확장 | 불가 | N배 확장 | 무제한 |
| 테스트 커버리지 | 낮음 | 높음 | 대폭 향상 |
| **종합 점수** | **3.8/10** | **8.2/10** | **+116%** |

---

## 부록: 분석 메타데이터

| 항목 | 값 |
|------|-----|
| 분석 도구 | Sequential-Thinking MCP |
| 분석 단계 | 8단계 |
| 참여 페르소나 | 프로젝트 매니저, 코드 품질 전문가, 성능 엔지니어, 안정성 전문가, 소프트웨어 아키텍트, 에러 핸들링 전문가, 확장성 전문가 |
| 참조 문서 | 3개 |
| 문서 버전 | 1.0 |
