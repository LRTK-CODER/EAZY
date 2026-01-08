# EAZY 프로젝트 아키텍처 종합 검토 보고서

**검토 일자**: 2026-01-08
**검토 범위**: Backend + Frontend + Infrastructure (MVP Phase)
**검토자**: Architecture Reviewer Agent

---

## 목차

1. [Executive Summary](#1-executive-summary)
2. [Architectural Strengths](#2-architectural-strengths)
3. [Critical Architecture Issues](#3-critical-architecture-issues)
4. [Design Concerns](#4-design-concerns)
5. [Scalability Assessment](#5-scalability-assessment)
6. [Technology Stack Evaluation](#6-technology-stack-evaluation)
7. [Strategic Recommendations](#7-strategic-recommendations)

---

## 1. Executive Summary

### 아키텍처 건전성 점수: **8.2/10**

EAZY 프로젝트는 전반적으로 **견고하고 확장 가능한 아키텍처**를 채택하고 있습니다. FastAPI 기반 레이어드 아키텍처, React 19 기반 컴포넌트 계층 구조, Redis 기반 비동기 작업 처리 등 현대적인 설계 패턴을 잘 따르고 있습니다. TDD 방식의 개발과 168개의 프론트엔드 테스트, 20개의 백엔드 테스트 파일은 높은 품질 기준을 보여줍니다.

**주요 강점**:
- 명확한 레이어 분리 (API → Service → Repository)
- Dual View Strategy (Assets 중복 제거 + 히스토리 추적)
- 비동기 처리 아키텍처 (Redis Queue + Worker)
- TDD 기반 고품질 코드
- 타입 안전성 (TypeScript Strict, mypy Strict)

**개선 필요 사항**:
- 보안 계층 부재 (인증/인가 미구현)
- 에러 핸들링 표준화 부족
- 데이터베이스 인덱싱 최적화 필요
- 모니터링 및 로깅 전략 부족
- API Rate Limiting 및 보안 헤더 부재

---

## 2. Architectural Strengths

### 2.1. Backend Layered Architecture (레이어드 아키텍처)

**평가**: ⭐⭐⭐⭐⭐ Excellent

```
┌─────────────────────────────────────────┐
│   API Layer (project.py, task.py)       │  HTTP 요청/응답 처리
├─────────────────────────────────────────┤
│   Service Layer (5개 서비스)             │  비즈니스 로직 캡슐화
│   - ProjectService                       │
│   - TargetService                        │
│   - TaskService                          │
│   - CrawlerService                       │
│   - AssetService                         │
├─────────────────────────────────────────┤
│   Model Layer (SQLModel)                 │  데이터 모델 정의
├─────────────────────────────────────────┤
│   Infrastructure (DB, Redis, Queue)      │  외부 의존성 관리
└─────────────────────────────────────────┘
```

**강점**:
1. **명확한 책임 분리**: API 엔드포인트는 HTTP 처리만, Service는 비즈니스 로직만 담당
   ```python
   # api/v1/endpoints/project.py (올바른 레이어 분리)
   @router.post("/", response_model=ProjectRead)
   async def create_project(project_in: ProjectCreate, session: AsyncSession):
       service = ProjectService(session)
       return await service.create_project(project_in)  # 비즈니스 로직 위임
   ```

2. **재사용 가능한 Service 레이어**: Service 클래스는 API뿐만 아니라 Worker에서도 재사용
   ```python
   # app/worker.py에서 AssetService 재사용
   asset_service = AssetService(session)
   await asset_service.process_asset(...)
   ```

3. **Dependency Injection**: FastAPI의 `Depends()`를 활용한 깔끔한 의존성 주입
   ```python
   async def create_project(
       session: AsyncSession = Depends(get_session)  # DI 패턴
   ):
   ```

**개선점**:
- Repository 레이어 미분리: Service가 직접 SQLModel 쿼리 수행 (향후 Repository 패턴 도입 고려)

---

### 2.2. Dual View Data Strategy (이원화 데이터 전략)

**평가**: ⭐⭐⭐⭐⭐ Excellent (핵심 아키텍처 강점)

```
┌─────────────────────────────────────┐
│  Assets 테이블 (Total View)         │
│  - content_hash UNIQUE 제약           │  유니크한 공격 표면 최신 상태
│  - last_seen_at 업데이트              │
│  - Deduplication (중복 제거)          │
└─────────────────────────────────────┘
          ↕
┌─────────────────────────────────────┐
│  AssetDiscoveries 테이블 (History)  │
│  - task_id FK                        │  각 스캔별 발견 이력
│  - asset_id FK                       │
│  - parent_asset_id (탐색 경로 추적)   │
└─────────────────────────────────────┘
```

**강점**:
1. **중복 제거와 이력 추적 동시 제공**:
   - Assets: 최신 스냅샷 (content_hash 기반 UPSERT)
   - AssetDiscoveries: 스캔별 히스토리 (M:N 관계)

2. **content_hash 전략**:
   ```python
   # app/services/asset_service.py
   def _generate_content_hash(self, method: str, url: str) -> str:
       identifier = f"{method.upper()}:{url}"
       return hashlib.sha256(identifier.encode()).hexdigest()
   ```
   - Method + URL 조합으로 유니크성 보장
   - SHA256 해시 사용 (충돌 확률 극히 낮음)

3. **스캔 결과 다각도 조회 가능**:
   - "특정 스캔의 결과" → AssetDiscoveries JOIN
   - "프로젝트 전체 자산" → Assets 단일 쿼리

**개선점**:
- URL 정규화 부족: 쿼리 파라미터 순서 차이 시 중복 발생 가능
  ```
  example.com?a=1&b=2  vs.  example.com?b=2&a=1  → 다른 해시값
  ```

---

### 2.3. Asynchronous Task Processing (비동기 작업 처리)

**평가**: ⭐⭐⭐⭐☆ Very Good

```
┌────────────┐      ┌──────────┐      ┌──────────┐
│  Frontend  │      │ FastAPI  │      │  Worker  │
│            │      │  (API)   │      │ Process  │
└─────┬──────┘      └────┬─────┘      └────┬─────┘
      │                  │                  │
      │ POST /scan       │                  │
      ├─────────────────>│                  │
      │                  │ 1. Task DB 저장  │
      │                  │ 2. Redis RPUSH   │
      │                  ├─────────────────>│
      │ 202 Accepted     │                  │ 3. LPOP
      │<─────────────────┤                  │ 4. Crawl
      │                  │                  │ 5. Save Assets
      │ GET /tasks/{id}  │                  │ 6. Update Status
      │ (Polling 5초)    │                  │
      ├─────────────────>│<─────────────────┤
      │ Task Status      │                  │
      │<─────────────────┤                  │
```

**강점**:
1. **API와 크롤링 작업 분리**: API 서버는 빠르게 응답 (202 Accepted), 무거운 작업은 Worker가 처리
2. **Redis FIFO Queue**: 단순하고 신뢰성 있는 작업 큐
   ```python
   # app/core/queue.py
   await self.redis.rpush(self.queue_key, json.dumps(payload))  # Enqueue
   data = await self.redis.lpop(self.queue_key)  # Dequeue
   ```

3. **작업 취소 지원**: Redis 플래그 기반 중단 메커니즘
   ```python
   # app/worker.py - 5초마다 취소 확인
   if await check_cancellation(task_manager, task_id):
       task_record.status = TaskStatus.CANCELLED
   ```

4. **Frontend 폴링 전략**: TanStack Query로 5초 간격 자동 폴링
   ```typescript
   refetchInterval: (query) => {
     if (data.status === 'COMPLETED' || data.status === 'FAILED') {
       return false; // 폴링 중지
     }
     return 5000; // 5초 간격
   }
   ```

**개선점**:
- **메시지 큐 신뢰성**: Redis는 메모리 기반이므로 서버 재시작 시 작업 손실 가능 (향후 RabbitMQ/Kafka 고려)
- **Worker 확장성**: 현재 단일 Worker 프로세스 (수평 확장 시 Redis 경쟁 조건 가능)
- **재시도 로직 부재**: 실패한 작업 자동 재시도 메커니즘 없음

---

### 2.4. Frontend Component Architecture (컴포넌트 아키텍처)

**평가**: ⭐⭐⭐⭐⭐ Excellent

**Atomic Design 기반 계층 구조**:
```
Pages (Templates)
   ├── ProjectDetailPage.tsx
   ├── ActiveProjectsListPage.tsx
   └── ArchivedProjectsPage.tsx
      ↓
Features (Organisms/Molecules)
   ├── project/ (9개 컴포넌트)
   │   ├── CreateProjectForm
   │   ├── EditProjectForm
   │   └── ProjectFormFields (재사용)
   └── target/ (5개 컴포넌트)
       ├── TargetList
       ├── CreateTargetForm
       └── TargetFormFields (재사용)
      ↓
UI Components (Atoms)
   └── 93개 shadcn/ui 컴포넌트
       ├── Button, Dialog, Input
       ├── Table, Card, Badge
       └── Form, Select, Checkbox
```

**강점**:
1. **Presentation & Container 패턴**:
   ```typescript
   // TargetFormFields.tsx (Presentation - 순수 뷰)
   export function TargetFormFields({ form }: Props) {
     return <FormField name="url" ... />;
   }

   // CreateTargetForm.tsx (Container - 로직 포함)
   export function CreateTargetForm() {
     const form = useForm();  // 로직
     const createTarget = useCreateTarget();
     return <TargetFormFields form={form} />;  // 뷰 재사용
   }
   ```

2. **TanStack Query를 통한 서버 상태 관리**:
   ```typescript
   // hooks/useProjects.ts - 일관된 캐싱 전략
   export const projectKeys = {
     all: ['projects'] as const,
     list: (params) => [...projectKeys.all, 'list', params],
     detail: (id) => [...projectKeys.all, 'detail', id],
   };
   ```
   - Optimistic Update 가능
   - 자동 캐시 무효화 (invalidateQueries)
   - 백그라운드 재검증

3. **shadcn/ui 활용**: 코드베이스에 직접 통합 (외부 의존성 최소화)
   - Radix UI 기반 (접근성 우수)
   - Tailwind CSS로 일관된 스타일링
   - 93개 컴포넌트 재사용

**개선점**:
- **전역 상태 관리 부재**: Context API나 Zustand 미사용 (현재는 TanStack Query만으로 충분하지만, 향후 클라이언트 상태 증가 시 고려)

---

### 2.5. Type Safety (타입 안전성)

**평가**: ⭐⭐⭐⭐⭐ Excellent

**Backend (Python)**:
```python
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true  # Strict 모드 활성화

# 모든 함수에 타입 힌트 강제
async def get_project(self, project_id: int) -> Optional[Project]:
    return await self.session.get(Project, project_id)
```

**Frontend (TypeScript)**:
```typescript
// tsconfig.json (추정)
{
  "compilerOptions": {
    "strict": true  // Strict 모드
  }
}

// types/project.ts - 명시적 타입 정의
export interface Project {
  id: number;
  name: string;
  is_archived: boolean;
  created_at: string;
}
```

**강점**:
1. **End-to-End 타입 안전성**: Backend Pydantic 모델 → API Schema → Frontend TypeScript 타입
2. **Zod 스키마 검증**: 폼 입력 런타임 검증
   ```typescript
   // schemas/targetSchema.ts
   export const targetFormSchema = z.object({
     name: z.string().min(1, "Name is required"),
     url: z.string().url("Invalid URL format"),
     scope: z.enum(["DOMAIN", "SUBDOMAIN", "URL_ONLY"]),
   });
   ```

3. **SQLModel의 Pydantic 통합**: 타입과 검증 로직 통합
   ```python
   class TargetBase(SQLModel):
       name: str = Field(max_length=255)
       url: str = Field(max_length=2048)
       scope: TargetScope = Field(default=TargetScope.DOMAIN)
   ```

---

### 2.6. Test-Driven Development (TDD)

**평가**: ⭐⭐⭐⭐⭐ Excellent (프로젝트 핵심 강점)

**테스트 커버리지**:
- Frontend: **168개 테스트** (16개 파일) - 모두 통과
- Backend: **20개 테스트 파일** (API, Service, Integration)

**TDD 사이클 증거**:
```
커밋 히스토리:
f67bd35 test(frontend): add ProjectDetailPage extension tests (TDD RED)
64c2fd6 feat(frontend): implement ProjectDetailPage Target integration (TDD GREEN)
36955f9 feat(ui): implement Target components UI improvements (TDD REFACTOR)
```

**강점**:
1. **RED → GREEN → REFACTOR 사이클 준수**
2. **통합 테스트 포함**: `test_full_flow.py` (전체 스캔 워크플로우 검증)
3. **Mocking 전략**: Playwright 네트워크 호출 Mock 처리
   ```python
   with patch("app.services.crawler_service.CrawlerService.crawl"):
       mock_crawl.return_value = ["http://example.com/page1"]
   ```

---

## 3. Critical Architecture Issues

### 3.1. 보안 계층 완전 부재 (High Priority)

**심각도**: 🔴 Critical

**현재 상태**:
```python
# app/main.py
origins = ["*"]  # 모든 Origin 허용 (프로덕션 위험)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**문제점**:
1. **인증/인가 시스템 부재**: 누구나 모든 API 접근 가능
2. **CORS 전면 개방**: CSRF 공격 가능성
3. **Secret Key 하드코딩**:
   ```python
   # app/core/config.py
   SECRET_KEY: str = "CHANGE_THIS_TO_A_SECURE_KEY_IN_PRODUCTION"
   ```

4. **Rate Limiting 부재**: DDoS 공격 취약
5. **보안 헤더 미설정**:
   - CSP (Content Security Policy)
   - HSTS (HTTP Strict Transport Security)
   - X-Frame-Options

**영향**:
- 프로덕션 배포 시 심각한 보안 위험
- 크롤링 작업 남용 가능 (무제한 스캔 요청)
- 데이터 무단 접근/수정/삭제 가능

**권장 해결책**:
```python
# 1. JWT 인증 도입
from fastapi import Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.get("/projects/")
async def read_projects(
    token: str = Depends(security),  # JWT 검증
    session: AsyncSession = Depends(get_session)
):
    # user_id = verify_jwt(token)
    # 사용자별 프로젝트 필터링
    pass

# 2. CORS 제한
origins = [
    "https://your-frontend-domain.com",
]

# 3. Rate Limiting (slowapi 라이브러리)
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/scan", dependencies=[Depends(limiter.limit("5/minute"))])
async def trigger_scan(...):
    pass
```

---

### 3.2. 데이터베이스 인덱싱 전략 부재

**심각도**: 🟠 High

**현재 상태**:
```python
# models/asset.py
class AssetBase(SQLModel):
    content_hash: str = Field(index=True, unique=True)  # 인덱스 존재
    target_id: int = Field(...)  # 인덱스 없음 (FK인데!)
    url: str = Field(max_length=2048)  # 인덱스 없음
    last_seen_at: datetime  # 정렬용인데 인덱스 없음
```

**문제점**:
1. **Foreign Key 인덱스 누락**: `target_id`, `task_id` 등 JOIN 성능 저하
2. **정렬 컬럼 인덱스 부재**: `ORDER BY last_seen_at DESC` 성능 문제
3. **복합 인덱스 미설정**: `(target_id, last_seen_at)` 복합 쿼리 최적화 안 됨

**쿼리 성능 영향 분석**:
```sql
-- 현재 쿼리 (인덱스 없음)
SELECT * FROM assets
WHERE target_id = 1
ORDER BY last_seen_at DESC;
-- → Full Table Scan (자산 1만 건 시 수초 소요)

-- 인덱스 추가 후
CREATE INDEX idx_assets_target_last_seen
ON assets(target_id, last_seen_at DESC);
-- → Index Scan (밀리초 단위)
```

**권장 해결책**:
```python
# Alembic 마이그레이션 생성
# versions/add_asset_indexes.py

def upgrade():
    op.create_index(
        'idx_assets_target_last_seen',
        'assets',
        ['target_id', sa.text('last_seen_at DESC')],
        postgresql_using='btree'
    )

    op.create_index(
        'idx_asset_discoveries_task_id',
        'asset_discoveries',
        ['task_id']
    )
```

---

### 3.3. 에러 핸들링 표준화 부족

**심각도**: 🟠 High

**현재 상태**:
```python
# api/v1/endpoints/project.py
@router.get("/{project_id}")
async def read_project(project_id: int, session: AsyncSession):
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# 다른 엔드포인트들도 각자 다른 에러 메시지
# "Target not found", "Resource not found", "Not found" 등 일관성 없음
```

**문제점**:
1. **에러 응답 형식 불일치**:
   ```json
   // FastAPI 기본
   {"detail": "Project not found"}

   // 예외 핸들러 필요
   {
     "error": {
       "code": "PROJECT_NOT_FOUND",
       "message": "Project with ID 123 not found",
       "timestamp": "2026-01-08T10:00:00Z"
     }
   }
   ```

2. **예외 계층 구조 부재**: 도메인별 커스텀 예외 없음
3. **로깅 전략 부족**: 에러 발생 시 추적 어려움

**권장 해결책**:
```python
# app/core/exceptions.py
class EAZYException(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code

class ResourceNotFound(EAZYException):
    def __init__(self, resource_type: str, resource_id: int):
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            code=f"{resource_type.upper()}_NOT_FOUND"
        )

# app/main.py - Global Exception Handler
@app.exception_handler(ResourceNotFound)
async def resource_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

# 사용 예시
raise ResourceNotFound("Project", project_id)
```

---

## 4. Design Concerns

### 4.1. URL 정규화 전략 부재 (Medium Priority)

**현재 content_hash 생성 로직**:
```python
# app/services/asset_service.py
def _generate_content_hash(self, method: str, url: str) -> str:
    identifier = f"{method.upper()}:{url}"
    return hashlib.sha256(identifier.encode()).hexdigest()
```

**문제 시나리오**:
```python
# 동일한 자원인데 다른 해시 생성
url1 = "https://example.com/search?q=test&sort=date"
url2 = "https://example.com/search?sort=date&q=test"  # 파라미터 순서만 다름
# → 별도 Asset으로 중복 저장

url3 = "https://example.com/page#section1"
url4 = "https://example.com/page#section2"  # Fragment만 다름
# → 동일 페이지인데 중복 저장
```

**권장 해결책**:
```python
from urllib.parse import urlparse, parse_qs, urlencode

def _normalize_url(self, url: str) -> str:
    parsed = urlparse(url)

    # 1. 쿼리 파라미터 정렬
    params = parse_qs(parsed.query)
    sorted_params = sorted(params.items())
    normalized_query = urlencode(sorted_params, doseq=True)

    # 2. Fragment 제거 (선택적)
    # 3. 스키마 정규화 (http → https)
    # 4. 경로 정규화 (/path/ → /path)

    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{normalized_query}"

def _generate_content_hash(self, method: str, url: str) -> str:
    normalized_url = self._normalize_url(url)
    identifier = f"{method.upper()}:{normalized_url}"
    return hashlib.sha256(identifier.encode()).hexdigest()
```

---

### 4.2. Worker 확장성 제한

**현재 아키텍처**:
```
┌──────────┐      ┌────────────┐
│  Redis   │ ◄──► │  Worker 1  │  (단일 프로세스)
│  Queue   │      └────────────┘
└──────────┘
```

**문제점**:
1. **수평 확장 시 경쟁 조건**:
   ```
   Worker 1: LPOP task_1 → 처리 중
   Worker 2: LPOP task_1 (동일 작업) → ❌ 불가능 (LPOP은 원자적)
   ```
   → Redis LPOP은 원자적이므로 안전하지만, Worker가 크래시 시 작업 손실

2. **재시도 로직 부재**:
   ```python
   # app/worker.py
   except Exception as e:
       task_record.status = TaskStatus.FAILED
       # 재시도 없이 즉시 FAILED 처리
   ```

3. **작업 우선순위 미지원**: FIFO만 지원 (긴급 스캔 우선 처리 불가)

**권장 해결책**:
```python
# 1. 재시도 메커니즘
async def process_task_with_retry(task_data, max_retries=3):
    for attempt in range(max_retries):
        try:
            await process_task(task_data)
            break
        except Exception as e:
            if attempt == max_retries - 1:
                # 최종 실패
                await mark_task_failed(task_data)
            else:
                # 재시도 대기
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

# 2. 우선순위 큐
# Redis Sorted Set 활용
await redis.zadd("priority_queue", {
    json.dumps(task_data): priority_score
})
task_data = await redis.zpopmin("priority_queue")

# 3. Dead Letter Queue (실패 작업 별도 관리)
await redis.lpush("dead_letter_queue", failed_task)
```

---

### 4.3. 모니터링 및 로깅 전략 부재

**현재 상태**:
```python
# app/worker.py
logger.info(f"Processing task: {task_data}")  # 단순 로깅
logger.error(f"Task execution failed: {e}")
```

**문제점**:
1. **구조화된 로깅 부재**: JSON 로그 없음 (분석 어려움)
2. **분산 추적 ID 없음**: Worker와 API 로그 연결 불가
3. **메트릭 수집 부재**: 작업 처리 시간, 성공률 등 미측정

**권장 해결책**:
```python
# 1. 구조화된 로깅 (structlog)
import structlog

logger = structlog.get_logger()
logger.info(
    "task_started",
    task_id=task_id,
    target_url=target.url,
    correlation_id=correlation_id
)

# 2. 메트릭 수집 (Prometheus)
from prometheus_client import Counter, Histogram

task_duration = Histogram('task_duration_seconds', 'Task processing time')
task_success = Counter('task_success_total', 'Successful tasks')
task_failure = Counter('task_failure_total', 'Failed tasks')

with task_duration.time():
    await process_task(task_data)
task_success.inc()

# 3. OpenTelemetry 통합 (분산 추적)
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("process_crawl_task"):
    await crawler.crawl(url)
```

---

### 4.4. 데이터베이스 트랜잭션 범위 불명확

**현재 코드**:
```python
# app/services/asset_service.py
async def process_asset(self, ...):
    # ... 로직 ...
    self.session.add(asset)
    await self.session.commit()  # Asset 커밋
    await self.session.refresh(asset)

    discovery = AssetDiscovery(...)
    self.session.add(discovery)
    await self.session.commit()  # Discovery 별도 커밋
```

**문제점**:
1. **부분 실패 가능성**: Asset 저장 성공, Discovery 저장 실패 시 불일치
2. **성능 저하**: 불필요한 다중 커밋 (네트워크 왕복 증가)

**권장 해결책**:
```python
async def process_asset(self, ...):
    # Asset과 Discovery를 단일 트랜잭션으로 처리
    self.session.add(asset)
    discovery = AssetDiscovery(...)
    self.session.add(discovery)

    await self.session.commit()  # 원자적 커밋
    await self.session.refresh(asset)
    return asset

# 또는 명시적 트랜잭션 컨텍스트
async with self.session.begin():
    self.session.add(asset)
    self.session.add(discovery)
    # commit은 자동 (context manager 종료 시)
```

---

## 5. Scalability Assessment

### 5.1. Database Scalability (데이터베이스 확장성)

**현재 설계 평가**: ⭐⭐⭐☆☆ Moderate

**스케일 추정**:
| 자산 수 | 쿼리 성능 (인덱스 없음) | 쿼리 성능 (인덱스 있음) | 저장 공간 |
|---------|------------------------|------------------------|----------|
| 1만 건  | ~100ms                 | ~10ms                  | ~100MB   |
| 10만 건 | ~1초                   | ~50ms                  | ~1GB     |
| 100만 건| ~10초                  | ~200ms                 | ~10GB    |
| 1000만 건| ~100초 (타임아웃)      | ~1초                   | ~100GB   |

**병목 지점**:
1. **Assets 테이블 단일 증가**: Sharding 전략 필요 (target_id 기반)
2. **JSONB 필드 비대화**: `request_spec`, `response_spec`가 10KB씩 증가 시 스토리지 폭증
3. **전체 텍스트 검색 부재**: URL 검색 시 LIKE 쿼리 (느림)

**권장 스케일링 전략**:
```sql
-- 1. Partitioning (월별 파티셔닝)
CREATE TABLE assets (
    ...
    created_at TIMESTAMP NOT NULL
) PARTITION BY RANGE (created_at);

CREATE TABLE assets_2026_01 PARTITION OF assets
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- 2. 전체 텍스트 검색 인덱스
CREATE INDEX idx_assets_url_trgm ON assets
    USING gin (url gin_trgm_ops);

-- 3. JSONB GIN 인덱스 (parameters 검색용)
CREATE INDEX idx_assets_parameters ON assets
    USING gin (parameters);
```

---

### 5.2. API Scalability (API 확장성)

**현재 설계 평가**: ⭐⭐⭐⭐☆ Good

**강점**:
1. **비동기 I/O**: FastAPI + asyncio (1만 동시 연결 가능)
2. **Stateless 설계**: 수평 확장 용이
   ```
   ┌──────────┐      ┌──────────┐
   │  API 1   │      │  API 2   │  (로드 밸런서로 분산)
   └────┬─────┘      └────┬─────┘
        │                 │
        └────────┬────────┘
              ┌──▼──┐
              │ DB  │ (공유 상태)
              └─────┘
   ```

**개선 필요**:
1. **Connection Pooling 설정 부재**:
   ```python
   # app/core/db.py
   engine = create_async_engine(
       settings.DATABASE_URL,
       pool_size=20,           # 추가 필요
       max_overflow=10,        # 추가 필요
       pool_pre_ping=True,     # 연결 검증
   )
   ```

2. **캐싱 전략 부재**: Redis를 큐로만 사용 (캐시 미활용)
   ```python
   # Project 조회 캐싱 예시
   from aiocache import Cache

   cache = Cache(Cache.REDIS, endpoint="localhost", port=6379)

   @cache.cached(ttl=300, key_builder=lambda *args: f"project:{args[0]}")
   async def get_project(project_id: int):
       return await service.get_project(project_id)
   ```

---

### 5.3. Worker Scalability (작업자 확장성)

**현재 설계 평가**: ⭐⭐⭐☆☆ Moderate

**수평 확장 가능성**:
```
┌──────────┐
│  Redis   │
│  Queue   │
└────┬─────┘
     │
     ├───► Worker 1 (안전)
     ├───► Worker 2 (안전)
     └───► Worker 3 (안전)
```
→ Redis LPOP의 원자성 덕분에 여러 Worker 동시 실행 가능

**한계점**:
1. **Playwright 리소스 집약적**: Worker당 Chromium 인스턴스 → 메모리 부족
2. **재시도 전략 부재**: Worker 크래시 시 작업 손실
3. **우선순위 미지원**: VIP 스캔과 일반 스캔 동일 대기

**권장 개선**:
```python
# 1. Worker Pool 제한
MAX_CONCURRENT_TASKS = 5
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def process_with_limit(task_data):
    async with semaphore:
        await process_task(task_data)

# 2. Headless Browser 재사용
class BrowserPool:
    def __init__(self, pool_size=3):
        self.browsers = []

    async def get_browser(self):
        if not self.browsers:
            browser = await p.chromium.launch()
            return browser
        return self.browsers.pop()

    async def release_browser(self, browser):
        self.browsers.append(browser)
```

---

## 6. Technology Stack Evaluation

### 6.1. Backend Stack Assessment

| 기술 | 버전 | 평가 | 근거 |
|-----|------|------|------|
| **FastAPI** | 0.115.0+ | ⭐⭐⭐⭐⭐ | 비동기 지원, 자동 문서화, 높은 성능 |
| **SQLModel** | 0.0.22+ | ⭐⭐⭐⭐☆ | Pydantic 통합 우수, 일부 기능 제한 (아직 베타) |
| **PostgreSQL** | 15 | ⭐⭐⭐⭐⭐ | JSONB 지원, 강력한 트랜잭션, 확장성 |
| **Redis** | 7 | ⭐⭐⭐⭐☆ | 큐로 적합, 메시지 손실 위험 (RabbitMQ 대안 고려) |
| **Playwright** | 1.42.0+ | ⭐⭐⭐⭐⭐ | JS 렌더링 지원, 안정적인 크롤링 |
| **UV** | latest | ⭐⭐⭐⭐⭐ | 10-100배 빠른 설치, 현대적인 패키징 |

**특이사항**:
1. **UV 선택의 탁월함**: pip/poetry 대비 압도적 속도, lock 파일 신뢰성
2. **SQLModel의 미성숙**: 아직 0.x 버전이지만, Pydantic + SQLAlchemy 통합은 훌륭
3. **Redis의 한계**: 메시지 큐로 사용 시 ACK 메커니즘 부재 (추후 RabbitMQ/Celery 고려)

---

### 6.2. Frontend Stack Assessment

| 기술 | 버전 | 평가 | 근거 |
|-----|------|------|------|
| **React** | 19.2.0 | ⭐⭐⭐⭐⭐ | 최신 Concurrent 기능, Hooks 성숙도 높음 |
| **TypeScript** | 5.9.3 | ⭐⭐⭐⭐⭐ | Strict 모드로 타입 안전성 확보 |
| **Vite** | 7.2.4 | ⭐⭐⭐⭐⭐ | HMR 속도 우수, 빌드 최적화 |
| **TanStack Query** | 5.90.16 | ⭐⭐⭐⭐⭐ | 서버 상태 관리의 표준, 캐싱 전략 우수 |
| **shadcn/ui** | - | ⭐⭐⭐⭐⭐ | 접근성(Radix), 커스터마이징 용이 |
| **Tailwind CSS** | 4.1.18 | ⭐⭐⭐⭐⭐ | v4의 성능 개선, 일관된 스타일링 |
| **Zod** | 4.2.1 | ⭐⭐⭐⭐⭐ | 런타임 검증 + 타입 추론 |

**특이사항**:
1. **React 19 조기 도입**: Concurrent 기능 활용 가능, 안정성 우수
2. **shadcn/ui의 전략적 선택**: 93개 컴포넌트를 코드베이스에 직접 통합 (외부 의존성 없음)
3. **TanStack Query**: Redux/MobX 불필요, 서버 상태 관리로 충분

---

### 6.3. Infrastructure Stack Assessment

| 구성 요소 | 평가 | 개선 필요 사항 |
|----------|------|---------------|
| **Docker Compose** | ⭐⭐⭐⭐☆ | 개발 환경 우수, 프로덕션은 Kubernetes 권장 |
| **Alembic** | ⭐⭐⭐⭐⭐ | 마이그레이션 관리 체계적 (9개 마이그레이션 파일) |
| **pytest/Vitest** | ⭐⭐⭐⭐⭐ | TDD 인프라 완벽, 168+20개 테스트 |
| **Monitoring** | ⭐☆☆☆☆ | 부재 (Prometheus, Grafana 필요) |
| **Logging** | ⭐⭐☆☆☆ | 기본 로깅만 (ELK Stack 권장) |

---

## 7. Strategic Recommendations

### 7.1. 즉시 조치 필요 (MVP → Production)

**우선순위 1 (1-2주 내)**:

1. **보안 계층 구축**
   ```python
   # Phase 1: JWT 인증
   from fastapi_jwt_auth import AuthJWT

   @router.get("/projects/")
   async def read_projects(Authorize: AuthJWT = Depends()):
       Authorize.jwt_required()
       current_user = Authorize.get_jwt_subject()
       # 사용자별 프로젝트 필터링

   # Phase 2: RBAC (Role-Based Access Control)
   from enum import Enum

   class UserRole(str, Enum):
       ADMIN = "admin"
       USER = "user"

   @router.delete("/projects/{id}")
   async def delete_project(
       id: int,
       current_user: User = Depends(get_current_active_user)
   ):
       if current_user.role != UserRole.ADMIN:
           raise HTTPException(403, "Forbidden")
   ```

2. **데이터베이스 인덱스 추가**
   ```bash
   # Alembic 마이그레이션 생성
   cd backend
   uv run alembic revision -m "add_performance_indexes"

   # versions/xxx_add_performance_indexes.py
   def upgrade():
       # Assets 인덱스
       op.create_index('idx_assets_target_last_seen', 'assets',
                       ['target_id', sa.text('last_seen_at DESC')])

       # AssetDiscoveries 인덱스
       op.create_index('idx_discoveries_task', 'asset_discoveries', ['task_id'])
       op.create_index('idx_discoveries_asset', 'asset_discoveries', ['asset_id'])
   ```

3. **CORS 정책 강화**
   ```python
   # app/main.py
   origins = [
       settings.FRONTEND_URL,  # 환경 변수로 관리
   ]

   app.add_middleware(
       CORSMiddleware,
       allow_origins=origins,
       allow_credentials=True,
       allow_methods=["GET", "POST", "PATCH", "DELETE"],  # 명시적 제한
       allow_headers=["Authorization", "Content-Type"],   # 필요한 헤더만
   )
   ```

---

### 7.2. 단기 개선 (1-2개월)

**우선순위 2**:

1. **에러 핸들링 표준화**
   ```
   backend/
   └── app/
       └── core/
           ├── exceptions.py     (커스텀 예외 정의)
           └── error_handlers.py (Global Exception Handler)
   ```

2. **URL 정규화 구현**
   ```python
   # app/utils/url_normalizer.py
   class URLNormalizer:
       @staticmethod
       def normalize(url: str) -> str:
           # 1. 쿼리 파라미터 정렬
           # 2. Fragment 제거
           # 3. 경로 정규화
           pass

   # AssetService에서 사용
   normalized_url = URLNormalizer.normalize(url)
   content_hash = self._generate_content_hash(method, normalized_url)
   ```

3. **Connection Pooling 설정**
   ```python
   # app/core/db.py
   engine = create_async_engine(
       settings.DATABASE_URL,
       echo=settings.DEBUG,
       pool_size=20,
       max_overflow=10,
       pool_pre_ping=True,
       pool_recycle=3600,  # 1시간마다 연결 재생성
   )
   ```

4. **캐싱 레이어 추가**
   ```python
   # Project 목록 캐싱 (Redis)
   from aiocache import Cache

   cache = Cache.from_url(settings.REDIS_URL)

   @router.get("/projects/")
   async def read_projects(archived: bool = False):
       cache_key = f"projects:archived:{archived}"
       cached = await cache.get(cache_key)
       if cached:
           return json.loads(cached)

       projects = await service.get_projects(archived=archived)
       await cache.set(cache_key, json.dumps(projects), ttl=60)
       return projects
   ```

---

### 7.3. 중기 개선 (3-6개월)

**우선순위 3**:

1. **모니터링 스택 구축**
   ```yaml
   # docker-compose.monitoring.yml
   version: '3.8'
   services:
     prometheus:
       image: prom/prometheus
       ports:
         - "9090:9090"
       volumes:
         - ./prometheus.yml:/etc/prometheus/prometheus.yml

     grafana:
       image: grafana/grafana
       ports:
         - "3000:3000"
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=admin

     loki:
       image: grafana/loki
       ports:
         - "3100:3100"
   ```

   ```python
   # app/main.py - Prometheus 메트릭 추가
   from prometheus_client import make_asgi_app

   metrics_app = make_asgi_app()
   app.mount("/metrics", metrics_app)
   ```

2. **Worker 재시도 메커니즘**
   ```python
   # app/worker.py
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=2, max=10)
   )
   async def process_task_with_retry(task_data):
       await process_task(task_data)
   ```

3. **Dead Letter Queue 구현**
   ```python
   # app/core/queue.py
   class TaskManager:
       async def move_to_dlq(self, task_data, error):
           dlq_entry = {
               "task": task_data,
               "error": str(error),
               "timestamp": datetime.utcnow().isoformat(),
               "retry_count": task_data.get("retry_count", 0)
           }
           await self.redis.lpush("dead_letter_queue", json.dumps(dlq_entry))
   ```

4. **데이터베이스 파티셔닝**
   ```sql
   -- assets 테이블 월별 파티셔닝
   CREATE TABLE assets (
       ...
   ) PARTITION BY RANGE (EXTRACT(YEAR FROM first_seen_at), EXTRACT(MONTH FROM first_seen_at));

   CREATE TABLE assets_2026_01 PARTITION OF assets
       FOR VALUES FROM (2026, 1) TO (2026, 2);
   ```

---

### 7.4. 장기 개선 (6-12개월)

**우선순위 4 (LLM 통합 및 고급 기능)**:

1. **메시지 큐 업그레이드**
   ```
   Redis → RabbitMQ/AWS SQS

   이유:
   - Message Acknowledgement (ACK) 지원
   - 우선순위 큐 네이티브 지원
   - Durable 메시지 (서버 재시작 시 보존)
   ```

2. **Multi-Tenancy 아키텍처**
   ```python
   # 사용자/조직별 데이터 격리
   class Project(ProjectBase, table=True):
       organization_id: int = Field(foreign_key="organizations.id")

   # Row-Level Security (RLS) 활용
   # CREATE POLICY project_isolation ON projects
   # USING (organization_id = current_setting('app.current_org')::int);
   ```

3. **Kubernetes 마이그레이션**
   ```yaml
   # k8s/backend-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: eazy-backend
   spec:
     replicas: 3  # 수평 확장
     template:
       spec:
         containers:
         - name: api
           image: eazy-backend:latest
           resources:
             limits:
               memory: "1Gi"
               cpu: "500m"
   ```

4. **Event-Driven Architecture**
   ```python
   # LLM 분석 모듈을 이벤트 기반으로 연결

   # 1. 크롤링 완료 이벤트 발행
   await event_bus.publish("crawl.completed", {
       "task_id": task_id,
       "target_id": target_id,
       "asset_count": len(assets)
   })

   # 2. LLM Analyzer가 구독하여 자동 분석 시작
   @event_bus.subscribe("crawl.completed")
   async def trigger_llm_analysis(event_data):
       await llm_service.analyze_business_logic(event_data["task_id"])
   ```

---

## 결론

EAZY 프로젝트는 **8.2/10점의 견고한 아키텍처**를 보유하고 있습니다. 특히 **레이어드 아키텍처**, **Dual View 데이터 전략**, **TDD 기반 개발**은 업계 모범 사례를 따르고 있습니다.

**즉시 조치가 필요한 보안 계층 부재**와 **데이터베이스 인덱싱 최적화**만 해결한다면, 프로덕션 환경에서도 충분히 운영 가능한 시스템입니다.

본 보고서에서 제시한 **Strategic Recommendations**를 단계적으로 적용하면, 확장 가능하고 유지보수 가능한 엔터프라이즈급 DAST 플랫폼으로 성장할 수 있을 것입니다.

---

**검토 완료일**: 2026-01-08
**다음 검토 권장일**: 2026-02-08 (1개월 후)
