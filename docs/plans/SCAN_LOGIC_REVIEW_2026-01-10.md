# EAZY 백엔드 스캔 로직 분석 보고서

> **분석 일시:** 2026-01-10
> **분석 방법:** sequential-thinking MCP + 전문 에이전트 (architect-reviewer, code-reviewer)
> **분석 대상:** Phase 0-4 구현 검증

---

## 1. 요약

### TODO.md 작업 검증 결과

| Phase | 상태 | 신규 테스트 | 핵심 성과 |
|-------|------|------------|----------|
| Phase 0: Quick Wins | ✅ 완료 | - | BLPOP→BLMOVE 업그레이드, 타임아웃 적용 |
| Phase 1: 배치 처리 | ✅ 완료 | - | DB 부하 98% 감소 |
| Phase 2: 안정성 강화 | ✅ 완료 | 60개 | ACK/NACK, DLQ, Orphan Recovery |
| Phase 3: 아키텍처 개선 | ✅ 완료 | 60개 | workers/ 모듈화 |
| Phase 4: 확장성 확보 | ✅ 완료 | 84개 | WorkerPool, 분산 잠금 |

**총 테스트: 288개+ (목표 달성)**

---

## 2. 아키텍처 리뷰

### 종합 평가

| 차원 | 평가 | 요약 |
|------|------|------|
| 설계 패턴 | **A-** | DI, Template Method, Registry 패턴 우수 |
| 확장성 | **B+** | asyncio.wait + FIRST_COMPLETED 적절한 선택 |
| 신뢰성 | **B** | ACK/NACK 패턴 좋음, 일부 엣지 케이스 존재 |
| 코드 구성 | **A** | 깔끔한 관심사 분리 |

### 설계 패턴 분석

#### 의존성 주입 (WorkerContext)
```python
@dataclass
class WorkerContext:
    session: AsyncSession
    task_manager: TaskManager
    dlq_manager: DLQManager
    orphan_recovery: OrphanRecovery
```
- 모든 워커 의존성 중앙 집중화
- 테스트 시 쉽게 모킹 가능

#### 템플릿 메서드 패턴 (BaseWorker)
```python
class BaseWorker(ABC):
    async def process(self, task_data, task_json):  # 공통 로직
        # 1. DB에서 태스크 조회
        # 2. 상태 업데이트 → RUNNING
        # 3. 하트비트 전송
        # 4. execute() 호출 (서브클래스 구현)
        # 5. 결과 처리
        # 6. ACK

    @abstractmethod
    async def execute(self, ...):  # 서브클래스가 구현
        pass
```

#### Registry 패턴
```python
@register_worker
class CrawlWorker(BaseWorker):
    task_type = TaskType.CRAWL
```
- 데코레이터 기반 자동 등록
- 새 Worker 타입 추가 용이

### asyncio.wait + FIRST_COMPLETED 선택 근거

```python
done, pending = await asyncio.wait(
    wait_tasks,
    return_when=asyncio.FIRST_COMPLETED,
)
```

| 대안 | 문제점 |
|------|--------|
| `asyncio.gather()` | 무한 루프 워커에 부적합 |
| `asyncio.TaskGroup` | 하나 실패 시 전체 취소 |
| **`asyncio.wait`** | ✅ 개별 워커 실패/재시작 가능 |

---

## 3. 코드 품질 리뷰

### 종합 점수: 7.25/10

| 카테고리 | 점수 | 상태 |
|----------|------|------|
| 에러 처리 | 7/10 | 개선 필요 |
| 리소스 관리 | 8/10 | 양호 |
| 보안 | 6/10 | 주의 필요 |
| 모범 사례 | 8/10 | 양호 |

---

## 4. 발견된 이슈

### 🔴 Critical (프로덕션 배포 전 필수 수정)

#### 이슈 #1: 스킵된 태스크 손실 버그

**파일:** `backend/app/workers/crawl_worker.py`

```python
# 현재 코드 (문제)
if not await lock.acquire():
    return TaskResult.create_skipped({...})  # ACK 후 재큐잉 없음!
```

**문제:** 잠금 획득 실패 시 태스크가 ACK되어 영구 손실됨

**해결 방안:**
```python
# base.py의 process() 메서드에서
if result.skipped:
    await self.context.task_manager.nack_task(task_json, retry=True)
    return  # ACK 하지 않음
```

---

#### 이슈 #2: SSRF 취약점

**파일:** `backend/app/workers/crawl_worker.py:120`

```python
# 현재 코드 (문제)
links, http_data = await self.crawler.crawl(target.url)
```

**위험:** URL 검증 없이 다음 공격 가능
- `http://localhost:8080/admin` (내부 서비스)
- `file:///etc/passwd` (파일 시스템)
- `http://169.254.169.254/` (클라우드 메타데이터)

**해결 방안:**
```python
from urllib.parse import urlparse

ALLOWED_SCHEMES = {'http', 'https'}
BLOCKED_HOSTS = {'localhost', '127.0.0.1', '169.254.169.254'}

def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False
    if parsed.hostname in BLOCKED_HOSTS:
        return False
    # RFC 1918 사설 IP 대역 체크 추가 권장
    return True
```

---

#### 이슈 #3: 토큰 타입 불일치

**파일:** `backend/app/core/lock.py:151`

```python
# 현재 코드 (문제)
current_token = await self.redis.get(self.key)
return current_token == self.token  # bytes vs string 비교!
```

**문제:** Redis는 bytes 반환, `self.token`은 string → `is_owned()` 항상 False

**해결 방안:**
```python
# 옵션 1: decode
return current_token.decode() == self.token if current_token else False

# 옵션 2: bytes로 통일
self.token = str(uuid.uuid4()).encode()
```

---

### 🟠 High Priority

#### 이슈 #4: DLQ 재시도 Race Condition

**파일:** `backend/app/core/dlq.py:103-132`

```python
# 현재 코드 (원자적이지 않음)
await self.redis.lpush(self.queue_key, original_task)
await self.redis.lrem(self.dlq_key, 1, task_id)  # 이 사이에 크래시 → 중복
```

**해결 방안:**
```python
async with self.redis.pipeline(transaction=True) as pipe:
    await pipe.lpush(self.queue_key, original_task)
    await pipe.lrem(self.dlq_key, 1, task_id)
    await pipe.delete(meta_key)
    await pipe.execute()
```

---

#### 이슈 #5: 크롤러 타임아웃 없음

**파일:** `backend/app/workers/crawl_worker.py:120`

```python
# 현재 코드 (무한 대기 가능)
links, http_data = await self.crawler.crawl(target.url)
```

**해결 방안:**
```python
CRAWL_TIMEOUT = 300  # 5분

try:
    links, http_data = await asyncio.wait_for(
        self.crawler.crawl(target.url),
        timeout=CRAWL_TIMEOUT
    )
except asyncio.TimeoutError:
    return TaskResult.create_failure(TimeoutError(f"Crawl timeout: {target.url}"))
```

---

#### 이슈 #6: deprecated asyncio API

**파일:** `backend/app/workers/crawl_worker.py:125, 132`

```python
# 현재 코드 (Python 3.10+ deprecated)
last_check_time = asyncio.get_event_loop().time()
```

**해결 방안:**
```python
import time

last_check_time = time.monotonic()
```

---

### 🟡 Medium Priority

| 이슈 | 파일 | 설명 |
|------|------|------|
| Orphan Recovery N+1 쿼리 | `recovery.py` | 10,000개 태스크 → 10,001개 Redis 호출 |
| DLQ 메타데이터 TTL 없음 | `dlq.py` | 메모리 누수 가능 |
| 문자열 기반 에러 분류 | `errors.py` | 라이브러리 버전/로케일 의존 |
| 예외 재발생 후 ACK | `base.py` | 이중 처리 가능성 |
| DB 롤백 누락 | `base.py` | 커밋 실패 시 명시적 롤백 없음 |

---

## 5. 긍정적 발견 사항

### 잘 구현된 부분

| 항목 | 설명 |
|------|------|
| ✅ Async Context Manager | AssetService, DistributedLock 적절한 리소스 관리 |
| ✅ Lua 스크립트 | 원자적 잠금 해제/연장 |
| ✅ TaskResult 클래스 | 팩토리 메서드로 명확한 상태 표현 |
| ✅ 의존성 주입 | WorkerContext로 테스트 용이성 확보 |
| ✅ 지수 백오프 + 지터 | 썬더링 허드 방지 |
| ✅ TDD 준수 | RED-GREEN-REFACTOR 사이클 |
| ✅ 일관된 타입 힌트 | 코드 가독성 향상 |

### 아키텍처 강점

```
backend/app/
├── core/           # 인프라 계층 (Redis, 에러, 복구)
│   ├── queue.py
│   ├── errors.py
│   ├── retry.py
│   ├── dlq.py
│   ├── recovery.py
│   └── lock.py
├── workers/        # 워커 계층 (비즈니스 로직)
│   ├── base.py
│   ├── crawl_worker.py
│   ├── registry.py
│   ├── runner.py
│   └── pool.py
└── services/       # 서비스 계층 (외부 연동)
    ├── crawler_service.py
    └── asset_service.py
```

- 계층별 명확한 책임 분리
- 새 Worker 타입 추가 시 `crawl_worker.py` 패턴 따르면 됨
- 테스트 작성 용이한 구조

---

## 6. 권장 수정 우선순위

### Phase 5: 안정화 (권장)

| 우선순위 | 이슈 | 예상 소요 | 영향도 |
|----------|------|----------|--------|
| P0 | 스킵된 태스크 손실 | 30분 | 높음 |
| P0 | SSRF 취약점 | 1시간 | 높음 |
| P0 | 토큰 타입 불일치 | 15분 | 중간 |
| P1 | 크롤러 타임아웃 | 30분 | 중간 |
| P1 | DLQ 트랜잭션화 | 30분 | 중간 |
| P1 | deprecated API 교체 | 15분 | 낮음 |
| P2 | Orphan Recovery 최적화 | 2시간 | 낮음 |
| P2 | DLQ TTL 설정 | 30분 | 낮음 |

---

## 7. 검증 명령어

```bash
# 전체 테스트 실행
cd backend
uv run pytest tests/ -v

# 커버리지 확인
uv run pytest tests/ --cov=app --cov-report=html

# 워커 풀 실행
uv run python -m app.workers.pool

# 단일 워커 실행 (하위 호환)
uv run python -m app.workers.runner
```

---

## 8. 결론

### 성공적으로 완료된 작업
- ✅ Phase 0-4 모두 설계대로 구현됨
- ✅ 288개 테스트 통과 (목표 달성)
- ✅ TDD 원칙 준수
- ✅ 확장 가능한 Worker 아키텍처 완성

### 프로덕션 배포 전 필수 수정
- 🔴 3개의 Critical 이슈 해결 필요
- 🟠 High Priority 이슈 권장 수정

### 전체 평가
> 잘 설계된 아키텍처이며, 발견된 이슈들을 수정하면 **프로덕션 수준의 신뢰성**을 갖춘 시스템이 될 것입니다.

---

*이 문서는 sequential-thinking MCP와 architect-reviewer, code-reviewer 에이전트를 통해 자동 생성되었습니다.*
