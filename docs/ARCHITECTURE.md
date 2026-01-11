# EAZY 아키텍처

[← 메인 문서로 돌아가기](./README.md)

**최종 업데이트**: 2026-01-11

---

## 목차

1. [기술 스택](#기술-스택)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [프로젝트 구조](#프로젝트-구조)
4. [데이터 플로우](#데이터-플로우)
5. [비동기 처리 패턴](#비동기-처리-패턴)

---

## 기술 스택

### Backend

| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.12+ | 백엔드 언어 |
| UV | latest | Rust 기반 고속 패키지 매니저 |
| FastAPI | 0.115+ | 비동기 웹 프레임워크 |
| SQLModel | 0.0.22+ | ORM (Pydantic + SQLAlchemy) |
| PostgreSQL | 15 | 메인 DB (JSONB 지원) |
| Redis | 7 | 비동기 작업 큐 |
| Playwright | 1.42+ | 브라우저 자동화 (크롤링) |
| Alembic | 1.13+ | DB 마이그레이션 |
| Pytest | 8.1+ | 테스트 프레임워크 |

### Frontend

| 기술 | 버전 | 용도 |
|------|------|------|
| React | 19.2+ | UI 라이브러리 |
| TypeScript | 5.9+ | 정적 타입 언어 |
| Vite | 7.2+ | 빌드 도구 |
| shadcn/ui | - | UI 컴포넌트 (Radix UI 기반) |
| TailwindCSS | 4.1+ | 유틸리티 CSS |
| TanStack Query | 5.90+ | 서버 상태 관리 |
| React Router | 7.11+ | 클라이언트 라우팅 |
| React Hook Form | 7.69+ | 폼 상태 관리 |
| Zod | 4.2+ | 스키마 유효성 검증 |
| Vitest | 4.0+ | 테스트 러너 |
| Storybook | 10.1+ | 컴포넌트 개발 환경 |

---

## 시스템 아키텍처

### 시스템 구성도

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │ ◄─────► │   React     │ ◄─────► │   FastAPI   │
│             │  HTTP   │   :5173     │  REST   │   :8000     │
└─────────────┘         └─────────────┘         └──────┬──────┘
                                                       │
                       ┌───────────────────────────────┼───────────────┐
                       │                               │               │
                  ┌────▼─────┐                   ┌─────▼────┐   ┌─────▼────┐
                  │PostgreSQL│                   │  Redis   │   │Playwright│
                  │  :5432   │                   │  :6379   │   │(Crawler) │
                  └──────────┘                   └──────────┘   └──────────┘
```

### Backend Layered Architecture

```
┌─────────────────────────────────────────┐
│   API Layer (app/api/v1/endpoints/)     │  FastAPI 라우터
├─────────────────────────────────────────┤
│   Service Layer (app/services/)         │  비즈니스 로직
├─────────────────────────────────────────┤
│   Repository Layer (app/models/)        │  SQLModel ORM
├─────────────────────────────────────────┤
│   Infrastructure Layer (app/core/)      │  DB, Redis, Queue
└─────────────────────────────────────────┘
```

**레이어별 책임**:

| 레이어 | 책임 | 규칙 |
|--------|------|------|
| API | HTTP 요청/응답, 라우팅 | 비즈니스 로직 금지, Service에 위임 |
| Service | 비즈니스 로직, 트랜잭션 | Static Method, 예외 처리 |
| Repository | DB CRUD, 쿼리 추상화 | SQLModel 엔티티 정의 |
| Infrastructure | DB/Redis 연결, 환경 설정 | 설정 관리, 로깅 |

### Frontend Atomic Design Architecture

```
┌─────────────────────────────────────────┐
│   Pages (src/pages/)                    │  라우팅 페이지
├─────────────────────────────────────────┤
│   Features (src/components/features/)   │  도메인 컴포넌트
├─────────────────────────────────────────┤
│   UI Components (src/components/ui/)    │  shadcn/ui 93개
├─────────────────────────────────────────┤
│   State (TanStack Query)                │  서버 상태 관리
├─────────────────────────────────────────┤
│   Services & Hooks                      │  API 클라이언트
└─────────────────────────────────────────┘
```

---

## 프로젝트 구조

### Backend

```
backend/
├── app/
│   ├── main.py                    # FastAPI 진입점
│   ├── worker.py                  # Redis Queue Worker
│   ├── core/                      # 인프라 (config, db, redis, queue)
│   ├── models/                    # SQLModel 엔티티 (4개)
│   ├── services/                  # 비즈니스 로직 (5개)
│   └── api/v1/endpoints/          # REST API (2개)
├── tests/                         # Pytest 테스트
├── alembic/                       # DB 마이그레이션 (8개)
├── docker/docker-compose.yml      # PostgreSQL + Redis
└── pyproject.toml                 # UV 의존성
```

**주요 파일**:
- `app/main.py` - FastAPI 앱, CORS, 라우터 등록
- `app/worker.py` - Redis Queue 작업 처리
- `app/services/crawler_service.py` - Playwright 크롤링
- `app/services/asset_service.py` - Asset 중복 제거

### Frontend

```
frontend/src/
├── components/
│   ├── ui/                        # shadcn/ui (93개)
│   ├── features/                  # 도메인 컴포넌트 (14개)
│   │   ├── project/               # 9개
│   │   └── target/                # 5개
│   └── layout/                    # MainLayout, Sidebar, Header
├── pages/                         # 5개 페이지
├── hooks/                         # 4개 Custom Hooks
├── services/                      # API 클라이언트 (3개)
├── types/                         # TypeScript 타입 (3개)
├── schemas/                       # Zod 스키마 (2개)
├── lib/                           # api.ts, utils.ts
├── App.tsx                        # 라우팅
└── main.tsx                       # React 진입점
```

**주요 파일**:
- `hooks/useProjects.ts` - 7개 Query Hooks
- `hooks/useTargets.ts` - 6개 Query Hooks
- `hooks/useTasks.ts` - Task 상태 폴링 (5초)

### 통계

| 영역 | 소스 파일 | 테스트 | 기타 |
|------|----------|--------|------|
| Backend | 19개 | 11개 | 8개 마이그레이션 |
| Frontend | 151개 | 16개 (168 tests) | 47 Stories |

---

## 데이터 플로우

### 스캔 트리거 (전체 플로우)

```
1. User: "Scan" 버튼 클릭
   ↓
2. Frontend: POST /projects/{pid}/targets/{tid}/scan
   ↓
3. API Layer: Task 생성 (status: PENDING)
   ↓
4. Service Layer: TaskManager.enqueue() → Redis RPUSH
   ↓
5. API: 202 Accepted 반환 (task_id)
   ↓
6. Frontend: useTaskStatus() 폴링 시작 (5초)
   ↓
7. Worker: TaskManager.dequeue() → Redis LPOP
   ↓
8. Worker: Task 상태 업데이트 (RUNNING)
   ↓
9. CrawlerService.crawl() → Playwright
   ↓
10. AssetService.process_asset() → 중복 제거 (content_hash)
    ↓
11. Task 상태 업데이트 (COMPLETED)
    ↓
12. Frontend: 폴링 감지 → UI 업데이트
```

### 다이어그램

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ (1) Click "Scan"
       ▼
┌─────────────┐
│   React     │
└──────┬──────┘
       │ (2) POST /scan
       ▼
┌─────────────┐
│  FastAPI    │ ───────────► ┌──────────┐
│  API Layer  │              │PostgreSQL│
└──────┬──────┘              └──────────┘
       │
       ▼
┌─────────────┐
│  Service    │ ───────────► ┌──────────┐
│   Layer     │              │  Redis   │
└─────────────┘              └─────┬────┘
                                   │ Dequeue
                                   ▼
                             ┌─────────────┐
                             │   Worker    │
                             └──────┬──────┘
                                    │ Crawl
                                    ▼
                             ┌─────────────┐
                             │ Playwright  │
                             └──────┬──────┘
                                    │ Save
                                    ▼
                             ┌─────────────┐
                             │ PostgreSQL  │
                             └─────────────┘
```

---

## 비동기 처리 패턴

### Backend: Redis Queue + Worker (ARQ 패턴)

**구조**:
```
FastAPI (Enqueue) → Redis Queue → Worker (Dequeue)
```

**TaskManager** (app/core/queue.py):
```python
class TaskManager:
    async def enqueue(self, task_data: dict):
        await self.redis.rpush("tasks:queue", json.dumps(task_data))

    async def dequeue(self) -> dict | None:
        data = await self.redis.lpop("tasks:queue")
        return json.loads(data) if data else None
```

**Worker** (app/worker.py):
```python
async def worker_loop():
    while True:
        task = await task_manager.dequeue()
        if task:
            await TaskService.update_status(task_id, "RUNNING")
            links = await CrawlerService.crawl(task['target_url'])
            await TaskService.update_status(task_id, "COMPLETED")
        else:
            await asyncio.sleep(1)
```

**실행**:
```bash
# API 서버
uv run uvicorn app.main:app --reload

# Worker (별도 터미널)
uv run python -m app.worker
```

### Frontend: TanStack Query Polling

**Task 상태 폴링** (hooks/useTasks.ts):
```typescript
export function useTaskStatus(taskId: number) {
  return useQuery({
    queryKey: taskKeys.detail(taskId),
    queryFn: () => taskService.getTaskStatus(taskId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 5000;
      // COMPLETED/FAILED 시 폴링 중지
      if (data.status === 'COMPLETED' || data.status === 'FAILED') {
        return false;
      }
      return 5000; // 5초 간격
    }
  });
}
```

### 비동기 처리 장점

| Backend | Frontend |
|---------|----------|
| 즉시 202 Accepted 반환 | 실시간 상태 추적 |
| 크롤링은 별도 프로세스 | 완료 시 폴링 자동 중지 |
| Worker 스케일링 가능 | UX 향상 |
| Worker 크래시 시 API 영향 없음 | 네트워크 절약 |

---

## 참고 자료

- [QUICK_START.md](./QUICK_START.md) - 5분 설정 가이드
- [API_SPEC.md](./reference/api_spec.md) - REST API 명세
- [DB_SCHEMA.md](./reference/db_schema.md) - 데이터베이스 설계
- [DEVELOPMENT.md](./DEVELOPMENT.md) - 개발 가이드
- [CODING_CONVENTION.md](./reference/coding_convention.md) - 코딩 규약

---

[← 메인 문서로 돌아가기](./README.md)
