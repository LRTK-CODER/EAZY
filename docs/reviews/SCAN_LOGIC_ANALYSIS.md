# EAZY 스캔 로직 심층 분석 보고서

> **분석 일자:** 2026-01-10
> **분석 방법:** Sequential-Thinking MCP 기반 다중 전문가 토론
> **분석 초점:** 유지보수성 및 성능
> **참여 전문가:** 소프트웨어 아키텍트, 코드 품질 전문가, 성능 엔지니어, 동시성/확장성 전문가, 에러 처리 전문가, 테스트 전문가, 리팩토링 전문가

---

## 1. 스캔 로직 개요

### 1.1 전체 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SCAN FLOW OVERVIEW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. API: POST /projects/{pid}/targets/{tid}/scan                    │
│     │                                                               │
│     ▼                                                               │
│  2. TaskService.create_scan_task()                                  │
│     ├─→ DB: INSERT Task (status=PENDING)                            │
│     └─→ Redis: RPUSH eazy_task_queue {payload}                      │
│                                                                     │
│  3. Worker: run_worker() - 무한 루프 폴링 (1초 간격)                 │
│     │                                                               │
│     ▼                                                               │
│  4. process_one_task()                                              │
│     ├─→ Redis: LPOP (작업 꺼내기)                                    │
│     ├─→ DB: UPDATE Task (status=RUNNING)                            │
│     │                                                               │
│     ▼                                                               │
│  5. CrawlerService.crawl(url)                                       │
│     ├─→ Playwright: 브라우저 시작                                    │
│     ├─→ HTTP 요청/응답 인터셉트                                      │
│     ├─→ <a> 태그 링크 추출                                          │
│     └─→ 브라우저 종료                                                │
│                                                                     │
│  6. Asset 저장 루프 (for link in links)                             │
│     ├─→ 5초마다 취소 플래그 확인                                     │
│     ├─→ AssetService.process_asset() - 매 링크마다 호출             │
│     │   ├─→ DB: SELECT (중복 체크)                                  │
│     │   ├─→ DB: INSERT/UPDATE Asset                                 │
│     │   ├─→ DB: COMMIT                                              │
│     │   └─→ DB: INSERT AssetDiscovery + COMMIT                      │
│     │                                                               │
│     ▼                                                               │
│  7. DB: UPDATE Task (status=COMPLETED/FAILED)                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 핵심 파일 구성

| 파일 | 라인 수 | 역할 |
|------|---------|------|
| `worker.py` | 307 | 워커 메인 루프 + 작업 처리 |
| `crawler_service.py` | 164 | Playwright 크롤링 + HTTP 인터셉트 |
| `asset_service.py` | 152 | Asset 저장 + 중복 처리 |
| `task_service.py` | 135 | 스캔 생성/취소/조회 |
| `queue.py` | 42 | Redis 큐 관리 |
| `task.py` (endpoint) | 114 | API 엔드포인트 |

---

## 2. 유지보수성 분석

### 2.1 코드 중복 문제 (DRY 위반)

#### 문제 1: process_task vs process_one_task 중복

```python
# worker.py 내 두 함수가 90% 동일한 로직

# process_task (line 35-147) - 113 lines
# 용도: 테스트용 단일 태스크 처리

# process_one_task (line 149-279) - 131 lines
# 용도: 실제 워커 루프에서 사용
```

**중복되는 로직:**
- Task 상태 업데이트 (PENDING → RUNNING → COMPLETED/FAILED/CANCELLED)
- 크롤링 실행 및 결과 처리
- Asset 저장 루프
- 5초 간격 취소 체크
- 에러 핸들링 및 로깅

**취소 처리 코드 중복 예시:**

```python
# process_task (line 79-107)
current_time = asyncio.get_event_loop().time()
if current_time - last_check_time >= 5.0:
    is_cancelled = await check_cancellation(task_manager, task_id)
    if is_cancelled:
        logger.info(f"Task {task_id} cancelled by user")
        task_record.status = TaskStatus.CANCELLED
        task_record.completed_at = utc_now()
        task_record.result = json.dumps({
            "cancelled": True,
            "processed_links": saved_count,
            # ...
        })
        # ...

# process_one_task (line 207-235) - 거의 동일한 코드
```

#### 문제 2: import json 반복

```python
# worker.py 내에서 6번 중복 import
# line 89, 132, 144 (process_task 내)
# line 217, 260, 272 (process_one_task 내)

# 권장: 파일 상단에 단일 import
import json  # line 1에서 한 번만
```

#### 문제 3: utc_now() 함수 중복

4개 파일에서 동일한 함수 정의:

```python
# models/project.py, target.py, task.py, asset.py
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

**권장:** `utils/datetime.py`로 통합

### 2.2 단일 책임 원칙 (SRP) 위반

**worker.py가 담당하는 8가지 역할:**

| # | 책임 | 라인 범위 |
|---|------|----------|
| 1 | Redis 연결 관리 | 285-286 |
| 2 | DB 세션 관리 | 288-289, 295 |
| 3 | 작업 큐 폴링 | 154-156 |
| 4 | Task 상태 업데이트 | 183-186, 259-265 |
| 5 | 취소 확인 로직 | 20-33, 209-235 |
| 6 | 크롤링 오케스트레이션 | 196-202 |
| 7 | Asset 저장 조율 | 205-257 |
| 8 | 에러 처리 및 로깅 | 270-277 |

**권장:** 최소 4개 모듈로 분리

### 2.3 유지보수성 점수: 4/10

---

## 3. 성능 분석

### 3.1 DB COMMIT 과다 (Critical)

#### 현재 구현:

```python
# asset_service.py:137-149
async def process_asset(...):
    # ...
    await self.session.commit()      # Commit 1: Asset INSERT/UPDATE
    await self.session.refresh(asset)

    discovery = AssetDiscovery(...)
    self.session.add(discovery)
    await self.session.commit()      # Commit 2: AssetDiscovery INSERT
```

#### 성능 영향 계산:

| 발견 링크 수 | COMMIT 횟수 | 예상 지연 (100ms/COMMIT) |
|-------------|-------------|-------------------------|
| 10 | 20 | 2초 |
| 100 | 200 | 20초 |
| 1000 | 2000 | 3분 20초 |
| 5000 | 10000 | 16분 40초 |

#### 권장 수정:

```python
async def process_assets_batch(self, assets_data: List[AssetInput]) -> List[Asset]:
    assets = []
    discoveries = []

    for data in assets_data:
        # 처리 로직 (COMMIT 없이)
        assets.append(asset)
        discoveries.append(discovery)

    # 단일 트랜잭션
    self.session.add_all(assets)
    self.session.add_all(discoveries)
    await self.session.commit()  # 1회만 COMMIT

    return assets
```

### 3.2 브라우저 재시작 오버헤드

```python
# crawler_service.py:29-31
async def crawl(self, url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()  # 매번 시작 (~500ms-2s)
        # ...
        await browser.close()                 # 매번 종료
```

**오버헤드:**
- Chromium 시작 시간: 500ms ~ 2s
- 메모리 할당/해제 비용
- 프로세스 생성 오버헤드

**권장:** Browser Pool 또는 재사용 Context

```python
class CrawlerService:
    _browser: Optional[Browser] = None

    async def get_browser(self):
        if self._browser is None:
            p = await async_playwright().start()
            self._browser = await p.chromium.launch()
        return self._browser
```

### 3.3 동기적 Asset 저장

```python
# worker.py:208-257
for index, link in enumerate(links, start=1):
    # 순차 처리 - 병렬화 없음
    await asset_service.process_asset(...)
    saved_count += 1
```

**권장:** asyncio.gather() 또는 배치 처리

```python
# 병렬 처리 예시
tasks = [
    asset_service.process_asset(target_id, task_id, link, ...)
    for link in links[:batch_size]
]
await asyncio.gather(*tasks)
```

### 3.4 폴링 비효율

```python
# worker.py:294-298
while True:
    processed = await process_one_task(session, task_manager)
    if not processed:
        await asyncio.sleep(1)  # 빈 큐일 때도 매초 확인
```

**권장:** Redis BLPOP (Blocking Pop)

```python
# queue.py 개선
async def dequeue_task_blocking(self, timeout: int = 5):
    result = await self.redis.blpop(self.queue_key, timeout=timeout)
    if result:
        _, data = result
        return json.loads(data)
    return None
```

### 3.5 성능 병목 우선순위

| 순위 | 문제 | 영향도 | 수정 난이도 | ROI |
|------|------|--------|-------------|-----|
| 1 | DB COMMIT 과다 | **높음** | 중간 | **최고** |
| 2 | 동기 Asset 저장 | **높음** | 중간 | 높음 |
| 3 | 브라우저 재시작 | 중간 | 높음 | 중간 |
| 4 | 폴링 비효율 | 낮음 | **낮음** | 중간 |

### 3.6 성능 점수: 4/10

---

## 4. 확장성 분석

### 4.1 단일 Worker 문제

```python
# worker.py - 단일 프로세스 설계
async def run_worker() -> None:
    while True:
        async with async_session() as session:
            processed = await process_one_task(session, task_manager)
```

**문제점:**
- 다중 Worker 실행 시 경쟁 상태 가능
- 분산 잠금(Distributed Lock) 없음
- 수평 확장 불가

### 4.2 작업 손실 위험

```python
# queue.py:30-38
async def dequeue_task(self):
    data = await self.redis.lpop(self.queue_key)  # 꺼내면 즉시 삭제
    return json.loads(data) if data else None
```

**위험 시나리오:**

```
1. Worker가 LPOP으로 작업 꺼냄 (Redis에서 제거됨)
2. Worker가 크래시 (OOM, 네트워크 오류, 등)
3. 작업 영구 손실
   - Redis: 작업 없음
   - DB: Task가 PENDING 상태로 영원히 남음
```

**권장:** Redis BRPOPLPUSH + ACK 패턴

```python
# 개선된 패턴
class TaskManager:
    MAIN_QUEUE = "eazy_task_queue"
    PROCESSING_QUEUE = "eazy_task_processing"

    async def dequeue_safe(self, timeout: int = 5):
        # 메인 큐 → 처리 중 큐로 이동 (원자적)
        data = await self.redis.brpoplpush(
            self.MAIN_QUEUE,
            self.PROCESSING_QUEUE,
            timeout=timeout
        )
        return json.loads(data) if data else None

    async def ack_task(self, task_data: str):
        # 처리 완료 후 처리 중 큐에서 제거
        await self.redis.lrem(self.PROCESSING_QUEUE, 1, task_data)

    async def recover_stale_tasks(self, max_age_seconds: int = 300):
        # 5분 이상 처리 중인 작업 복구
        # ...
```

### 4.3 취소 신호 전파 지연

```python
# worker.py:211-212
if current_time - last_check_time >= 5.0:  # 5초 간격
    is_cancelled = await check_cancellation(...)
```

**문제:**
- 크롤링 중에는 취소 확인 안 함
- 최악의 경우: 크롤링 완료 후 + 5초 후에야 취소 인지

**타임라인 예시:**

```
t=0s   : 취소 요청 (API)
t=0s   : 크롤링 시작
t=30s  : 크롤링 완료, Asset 저장 시작
t=35s  : 첫 취소 확인 (5초 후)
t=35s  : 취소 처리

총 지연: 35초
```

### 4.4 동시 스캔 제한 없음

```python
# task_service.py:14-51
async def create_scan_task(self, project_id: int, target_id: int) -> Task:
    # 중복 스캔 검증 없음
    task = Task(
        project_id=project_id,
        target_id=target_id,
        type=TaskType.CRAWL,
        status=TaskStatus.PENDING
    )
```

**권장:**

```python
async def create_scan_task(self, project_id: int, target_id: int) -> Task:
    # 실행 중인 스캔 확인
    existing = await self._get_active_task_for_target(target_id)
    if existing:
        raise ValueError(f"Scan already in progress for target {target_id}")

    task = Task(...)
```

### 4.5 확장성 점수: 3/10

---

## 5. 에러 처리 분석

### 5.1 에러 핸들링 취약점

#### 크롤러 에러 무시

```python
# crawler_service.py - 여러 곳에서 에러 무시
except Exception as e:
    print(f"Request interception error: {e}")  # 1. print 사용
                                                # 2. 에러 후 계속 진행
                                                # 3. 부분 실패 추적 불가
```

**문제:**
- `print()` 대신 `logger` 사용해야 함
- 에러 발생 시에도 빈 결과로 "성공" 처리
- 어떤 요청이 실패했는지 추적 불가

#### Worker 에러 처리

```python
# worker.py:270-277
except Exception as e:
    logger.error(f"Task execution failed: {e}")
    task_record.status = TaskStatus.FAILED
    task_record.result = json.dumps({"error": str(e)})
    # 재시도 없이 즉시 FAILED
    # 스택트레이스 미저장
```

### 5.2 트랜잭션 일관성 문제

```python
# asset_service.py:137-149
await self.session.commit()     # Commit 1: Asset 저장
await self.session.refresh(asset)

discovery = AssetDiscovery(...)
self.session.add(discovery)
await self.session.commit()     # Commit 2: Discovery 저장
```

**문제 시나리오:**

```
1. Commit 1 성공 → Asset 저장됨
2. 네트워크 오류 발생
3. Commit 2 실패 → Discovery 저장 실패
4. 결과: Asset은 있지만 Discovery 이력 없음 (데이터 불일치)
```

**권장:**

```python
async with self.session.begin():
    self.session.add(asset)
    self.session.add(discovery)
    # 자동 COMMIT 또는 ROLLBACK
```

### 5.3 Graceful Shutdown 미흡

```python
# worker.py:299-303
except KeyboardInterrupt:
    logger.info("Worker stopped")
finally:
    await redis.close()
    await engine.dispose()
```

**문제:**
- SIGTERM 처리 없음 (컨테이너 환경에서 중요)
- 진행 중인 작업 완료 대기 없음
- RUNNING 상태 Task 복구 방안 없음

**권장:**

```python
import signal

class GracefulWorker:
    def __init__(self):
        self._should_stop = False
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        logger.info("Shutdown signal received, finishing current task...")
        self._should_stop = True

    async def run(self):
        while not self._should_stop:
            await self._process_one_task()
        logger.info("Worker stopped gracefully")
```

### 5.4 타임아웃 관리 부재

```python
# crawler_service.py:140
await page.goto(url, wait_until="networkidle")  # 기본 타임아웃만
```

**권장:**

```python
await page.goto(
    url,
    wait_until="networkidle",
    timeout=30000  # 명시적 30초 타임아웃
)
```

### 5.5 에러 처리 점수: 3/10

---

## 6. 테스트 가능성 분석

### 6.1 하드코딩된 의존성

#### CrawlerService

```python
# crawler_service.py
class CrawlerService:
    async def crawl(self, url: str):
        async with async_playwright() as p:  # 하드코딩
            browser = await p.chromium.launch()
```

**문제:**
- Playwright 의존성 하드코딩
- Mock 불가능
- 단위 테스트 시 실제 브라우저 필요

**권장:**

```python
class CrawlerService:
    def __init__(self, playwright_factory=None):
        self._factory = playwright_factory or async_playwright

    async def crawl(self, url: str):
        async with self._factory() as p:
            # ...
```

#### Worker

```python
# worker.py:196
crawler = CrawlerService()  # 하드코딩
```

### 6.2 테스트하기 어려운 긴 함수

| 함수 | 라인 수 | 분기 복잡도 |
|------|---------|------------|
| process_task | 113 | 높음 |
| process_one_task | 131 | 높음 |
| crawl | 135 | 중간 |
| process_asset | 97 | 중간 |

**권장 분리:**

```python
# 현재: 하나의 거대 함수
async def process_one_task(session, task_manager):
    # 150+ lines

# 권장: 책임별 분리
async def fetch_task_from_queue(task_manager) -> TaskPayload
async def update_task_status(session, task_id, status) -> Task
async def execute_crawl(crawler, url) -> CrawlResult
async def save_assets_batch(asset_service, assets) -> List[Asset]
async def handle_cancellation(task_manager, task_id) -> bool
```

### 6.3 테스트 가능성 점수: 5/10

---

## 7. 리팩토링 권장사항

### 7.1 Worker 모듈 분리 (우선순위: 높음)

#### 현재:

```
worker.py (307 lines)
```

#### 권장:

```
workers/
├── __init__.py
├── base.py              # BaseWorker 추상 클래스
│   ├── run()            # 메인 루프
│   ├── process_one()    # 단일 작업 처리
│   └── shutdown()       # Graceful shutdown
├── crawl_worker.py      # 크롤링 전용
│   └── execute()        # 크롤링 실행
├── task_executor.py     # 작업 실행 오케스트레이터
│   ├── fetch_task()
│   ├── update_status()
│   └── handle_result()
├── cancellation.py      # 취소 처리
│   ├── check()
│   └── process()
└── retry.py             # 재시도 정책
    ├── should_retry()
    └── calculate_delay()
```

### 7.2 Asset 배치 저장 (우선순위: 높음)

```python
# asset_service.py 추가
async def process_assets_batch(
    self,
    target_id: int,
    task_id: int,
    assets_data: List[AssetInput],
    batch_size: int = 100
) -> BatchResult:
    """배치로 Asset 저장"""
    results = BatchResult()

    for i in range(0, len(assets_data), batch_size):
        batch = assets_data[i:i + batch_size]

        async with self.session.begin():
            for data in batch:
                asset = await self._create_or_update_asset(data)
                discovery = AssetDiscovery(
                    task_id=task_id,
                    asset_id=asset.id
                )
                self.session.add(discovery)
                results.add(asset)

        # 배치별 진행 상황 보고
        yield results

    return results
```

### 7.3 재시도 로직 추가 (우선순위: 중간)

```python
# workers/retry.py
class RetryPolicy:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def should_retry(self, attempt: int, error: Exception) -> bool:
        if attempt >= self.max_retries:
            return False

        # 재시도 가능한 에러 타입
        retryable = (
            ConnectionError,
            TimeoutError,
            # ...
        )
        return isinstance(error, retryable)

    def get_delay(self, attempt: int) -> float:
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
```

### 7.4 리팩토링 로드맵

| 단계 | 작업 | 예상 효과 | 난이도 | 예상 시간 |
|------|------|----------|--------|----------|
| 1 | Asset 배치 저장 | 성능 80%↑ | 중간 | 1-2일 |
| 2 | Worker 모듈 분리 | 유지보수성 70%↑ | 높음 | 3-5일 |
| 3 | BLPOP 적용 | CPU 50%↓ | 낮음 | 2시간 |
| 4 | 재시도 로직 | 안정성 40%↑ | 중간 | 1-2일 |
| 5 | DI 패턴 적용 | 테스트 가능성 60%↑ | 중간 | 2-3일 |
| 6 | Graceful Shutdown | 안정성 20%↑ | 낮음 | 4시간 |

---

## 8. 종합 평가

### 8.1 영역별 점수

| 영역 | 점수 | 핵심 문제 |
|------|------|----------|
| **유지보수성** | 4/10 | 코드 중복, SRP 위반, 307줄 단일 파일 |
| **성능** | 4/10 | N×2 COMMIT, 동기 처리, 브라우저 재시작 |
| **확장성** | 3/10 | 단일 Worker, 분산 잠금 없음, 작업 손실 위험 |
| **에러 처리** | 3/10 | 재시도 없음, 트랜잭션 불일치, Graceful shutdown 미흡 |
| **테스트 가능성** | 5/10 | 하드코딩 의존성, 긴 함수, Mock 어려움 |

### 8.2 종합 점수: **3.8/10**

### 8.3 핵심 문제 요약

#### Critical (즉시 개선 필요)

| # | 문제 | 영향 | 해결책 |
|---|------|------|--------|
| 1 | DB COMMIT 과다 | 1000 링크 = 3분+ 지연 | 배치 INSERT |
| 2 | 작업 손실 위험 | 데이터 정합성 파괴 | BRPOPLPUSH + ACK |
| 3 | 코드 중복 | 유지보수 비용 2배 | 공통 로직 추출 |

#### High (단기 개선)

| # | 문제 | 해결책 |
|---|------|--------|
| 4 | Worker 307줄 | 4-5개 모듈 분리 |
| 5 | 재시도 없음 | 지수 백오프 (최대 3회) |
| 6 | 중복 스캔 가능 | 타겟당 1개 제한 |

### 8.4 즉시 적용 가능한 Quick Wins

```python
# 1. BLPOP 적용 (5분 작업)
# queue.py
async def dequeue_task_blocking(self, timeout: int = 5):
    result = await self.redis.blpop(self.queue_key, timeout=timeout)
    if result:
        _, data = result
        return json.loads(data)
    return None

# 2. 명시적 타임아웃 (2분 작업)
# crawler_service.py
await page.goto(url, wait_until="networkidle", timeout=30000)

# 3. import json 정리 (1분 작업)
# worker.py 상단으로 이동

# 4. utc_now() 통합 (10분 작업)
# utils/datetime.py 생성
```

---

## 9. 결론

### MVP 평가
- **기능:** 스캔 기능은 동작함
- **품질:** 프로덕션 준비 안됨
- **리팩토링 필요 시간:** 약 2-3주 (풀타임 기준)

### 우선순위 권장
1. **즉시:** 배치 저장 적용 (성능 80% 향상)
2. **1주차:** Worker 모듈 분리
3. **2주차:** 재시도 로직 + BRPOPLPUSH
4. **3주차:** DI 패턴 + 테스트 강화

---

## 부록: 분석 메타데이터

| 항목 | 값 |
|------|-----|
| 분석 도구 | Sequential-Thinking MCP |
| 분석 단계 | 8단계 |
| 참여 페르소나 | 7명 |
| 분석 파일 수 | 6개 핵심 파일 |
| 총 분석 코드 | ~900 lines |
| 문서 버전 | 1.0 |
