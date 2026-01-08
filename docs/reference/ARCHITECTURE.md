# 아키텍처

[← 메인 문서로 돌아가기](../README.md)

---

## 목차

1. [시스템 구성도](#시스템-구성도)
2. [Backend Layered Architecture](#backend-layered-architecture)
3. [Frontend Atomic Design Architecture](#frontend-atomic-design-architecture)
4. [데이터 플로우](#데이터-플로우)
5. [비동기 처리 패턴](#비동기-처리-패턴)

---

## 시스템 구성도

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │ ◄─────► │   React     │ ◄─────► │   FastAPI   │
│             │  HTTP   │   Frontend  │  REST   │   Backend   │
└─────────────┘         └─────────────┘         └──────┬──────┘
                                                        │
                        ┌───────────────────────────────┼───────────────┐
                        │                               │               │
                   ┌────▼─────┐                   ┌─────▼────┐   ┌─────▼────┐
                   │PostgreSQL│                   │  Redis   │   │Playwright│
                   │   (DB)   │                   │  (Queue) │   │(Crawler) │
                   └──────────┘                   └──────────┘   └──────────┘
```

### 컴포넌트 설명

#### Browser

- 사용자가 웹 애플리케이션에 접근하는 클라이언트
- React Frontend를 렌더링
- REST API 호출 (Axios)

#### React Frontend

- 사용자 인터페이스 (UI)
- TanStack Query를 통한 서버 상태 관리
- React Router 기반 SPA (Single Page Application)
- **포트**: 5173 (개발 환경)

**상세 정보**: [TECH_STACK.md](TECH_STACK.md#frontend)

#### FastAPI Backend

- RESTful API 서버
- 비동기 처리 (AsyncIO)
- 자동 API 문서화 (Swagger UI)
- **포트**: 8000

**상세 정보**: [TECH_STACK.md](TECH_STACK.md#backend)

#### PostgreSQL

- 메인 데이터베이스
- JSONB 타입 지원
- ACID 트랜잭션
- **포트**: 5432

**상세 정보**: [db_schema.md](db_schema.md)

#### Redis

- 비동기 작업 큐 (Task Queue)
- FIFO 큐 구조
- **포트**: 6379

**상세 정보**: [비동기 처리 패턴](#비동기-처리-패턴)

#### Playwright

- 브라우저 자동화 도구
- Chromium 기반 크롤링
- JavaScript 렌더링 대응

**상세 정보**: [TECH_STACK.md](TECH_STACK.md#playwright)

---

## Backend Layered Architecture

```
┌─────────────────────────────────────────┐
│   API Layer (Controllers/Routers)       │  FastAPI Endpoints
├─────────────────────────────────────────┤
│   Service Layer (Business Logic)        │  ProjectService, CrawlerService
├─────────────────────────────────────────┤
│   Repository Layer (Data Access)        │  SQLModel ORM
├─────────────────────────────────────────┤
│   Infrastructure Layer                  │  DB, Redis, Queue
└─────────────────────────────────────────┘
```

### 레이어별 책임

#### API Layer (app/api/v1/endpoints/)

**책임**:
- HTTP 요청/응답 처리
- 데이터 유효성 검증 (Pydantic)
- 라우팅 정의
- 상태 코드 관리

**예시** (app/api/v1/endpoints/project.py):
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.db import get_db
from app.services.project_service import ProjectService

router = APIRouter()

@router.post("/projects/", response_model=ProjectRead, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    프로젝트 생성
    - 비즈니스 로직은 Service Layer에 위임
    - API Layer는 HTTP 처리만 담당
    """
    return await ProjectService.create_project(db, project)

@router.get("/projects/", response_model=list[ProjectRead])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    archived: bool = False,
    db: AsyncSession = Depends(get_db)
):
    return await ProjectService.get_projects(db, skip, limit, archived)
```

**규칙**:
- ❌ 비즈니스 로직 금지 (Service Layer에 위임)
- ❌ 직접 DB 접근 금지 (Dependency Injection 사용)
- ✅ Type Hint 필수
- ✅ HTTP 상태 코드 명시

---

#### Service Layer (app/services/)

**책임**:
- 비즈니스 로직 구현
- 트랜잭션 관리
- 도메인 규칙 적용
- 외부 서비스 호출

**예시** (app/services/project_service.py):
```python
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.project import Project

class ProjectService:
    @staticmethod
    async def create_project(
        db: AsyncSession,
        data: ProjectCreate
    ) -> Project:
        """프로젝트 생성 비즈니스 로직"""
        project = Project(**data.model_dump())
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def archive_project(
        db: AsyncSession,
        project_id: int
    ) -> None:
        """프로젝트 Archive (Soft Delete)"""
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        project.is_archived = True
        project.archived_at = datetime.utcnow()
        db.add(project)
        await db.commit()
```

**규칙**:
- ✅ 모든 비즈니스 로직은 Service Layer에 구현
- ✅ Static Method 사용 (Stateless)
- ✅ 예외 처리 (ValueError, HTTPException)
- ✅ 트랜잭션 관리 (commit, rollback)

---

#### Repository Layer (SQLModel ORM)

**책임**:
- 데이터베이스 CRUD 작업
- 쿼리 추상화
- 엔티티 매핑

**예시** (app/models/project.py):
```python
from sqlmodel import Field, SQLModel
from datetime import datetime

class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    description: str | None = None
    is_archived: bool = Field(default=False)
    archived_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**쿼리 예시**:
```python
# SELECT
result = await db.execute(select(Project).where(Project.is_archived == False))
projects = result.scalars().all()

# INSERT
project = Project(name="New Project")
db.add(project)
await db.commit()

# UPDATE
project.name = "Updated Name"
db.add(project)
await db.commit()

# DELETE (Hard Delete)
await db.delete(project)
await db.commit()
```

**상세 정보**: [db_schema.md](db_schema.md)

---

#### Infrastructure Layer (app/core/)

**책임**:
- 데이터베이스 연결 관리
- Redis 연결 관리
- 환경 설정
- 로깅

**예시** (app/core/db.py):
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

**예시** (app/core/queue.py):
```python
import redis.asyncio as redis
from app.core.config import settings

class TaskManager:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)

    async def enqueue(self, task_data: dict):
        await self.redis.rpush("tasks:queue", json.dumps(task_data))

    async def dequeue(self) -> dict | None:
        data = await self.redis.lpop("tasks:queue")
        return json.loads(data) if data else None
```

---

## Frontend Atomic Design Architecture

```
┌─────────────────────────────────────────┐
│   Pages (Templates)                     │  ProjectDetailPage, DashboardPage
├─────────────────────────────────────────┤
│   Features (Organisms/Molecules)        │  CreateProjectForm, TargetList
├─────────────────────────────────────────┤
│   UI Components (Atoms)                 │  Button, Input, Dialog (shadcn)
├─────────────────────────────────────────┤
│   State Management                      │  TanStack Query (서버 상태)
├─────────────────────────────────────────┤
│   Services & Hooks                      │  API Client, Custom Hooks
└─────────────────────────────────────────┘
```

### 레이어별 설명

#### Pages (Templates)

**역할**: 라우팅 페이지, 레이아웃 조합

**예시**:
- `ProjectsPage.tsx` - 프로젝트 허브
- `ProjectDetailPage.tsx` - 프로젝트 상세 + Target 관리
- `DashboardPage.tsx` - 대시보드

**코드 예시** (ProjectDetailPage.tsx):
```typescript
import { useParams } from 'react-router-dom';
import { useProject } from '@/hooks/useProjects';
import { useTargets } from '@/hooks/useTargets';
import TargetList from '@/components/features/target/TargetList';

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: project } = useProject(Number(projectId));
  const { data: targets } = useTargets(Number(projectId));

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold">{project?.name}</h1>
      <p className="text-muted-foreground">{project?.description}</p>

      <div className="mt-8">
        <TargetList projectId={Number(projectId)} targets={targets || []} />
      </div>
    </div>
  );
}
```

---

#### Features (Organisms/Molecules)

**역할**: 도메인 비즈니스 로직 컴포넌트

**예시**:
- `CreateProjectForm.tsx` - 프로젝트 생성 폼
- `TargetList.tsx` - Target 목록 테이블
- `DeleteProjectDialog.tsx` - 삭제 확인 다이얼로그

**Presentation & Container 패턴**:
```typescript
// TargetFormFields.tsx (Presentation - 재사용 가능)
export function TargetFormFields({ form }: { form: UseFormReturn<TargetFormValues> }) {
  return (
    <>
      <FormField name="name" control={form.control} />
      <FormField name="url" control={form.control} />
      <FormField name="scope" control={form.control} />
    </>
  );
}

// CreateTargetForm.tsx (Container - 로직 포함)
export function CreateTargetForm({ projectId }: { projectId: number }) {
  const form = useForm({ resolver: zodResolver(targetFormSchema) });
  const createTarget = useCreateTarget(projectId);

  const onSubmit = async (data: TargetFormValues) => {
    await createTarget.mutateAsync(data);
  };

  return (
    <Dialog>
      <Form {...form}>
        <TargetFormFields form={form} />
        <Button type="submit">생성</Button>
      </Form>
    </Dialog>
  );
}
```

---

#### UI Components (Atoms)

**역할**: 재사용 가능한 기본 컴포넌트

**예시**:
- `Button.tsx` - 버튼 컴포넌트
- `Dialog.tsx` - 다이얼로그 컴포넌트
- `Input.tsx` - 입력 필드
- `Table.tsx` - 테이블 컴포넌트

**특징**:
- shadcn/ui 기반 (93개 컴포넌트)
- Radix UI로 접근성 보장
- Tailwind CSS 스타일링
- 완전한 커스터마이징 가능

**상세 정보**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md#frontend-디렉토리-구조)

---

#### State Management (TanStack Query)

**역할**: 서버 상태 관리

**특징**:
- 자동 캐싱
- 백그라운드 동기화
- Optimistic Updates
- 폴링 (Polling)

**코드 예시** (hooks/useProjects.ts):
```typescript
export function useProjects(params?: { archived?: boolean }) {
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: () => projectService.getProjects(params)
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: projectService.createProject,
    onSuccess: () => {
      // 캐시 무효화 (자동 리페치)
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
    }
  });
}
```

**상세 정보**: [TECH_STACK.md](TECH_STACK.md#tanstack-query)

---

#### Services & Hooks

**역할**: API 통신 및 비즈니스 로직

**Services** (API Client):
```typescript
// services/projectService.ts
export const projectService = {
  async getProjects(params?: { archived?: boolean }): Promise<Project[]> {
    const response = await api.get('/projects/', { params });
    return response.data;
  },

  async createProject(data: ProjectCreate): Promise<Project> {
    const response = await api.post('/projects/', data);
    return response.data;
  }
};
```

**Custom Hooks** (TanStack Query 래퍼):
```typescript
// hooks/useProjects.ts
export function useProjects(params?: { archived?: boolean }) {
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: () => projectService.getProjects(params)
  });
}
```

---

## 데이터 플로우

### 스캔 트리거 예시 (전체 플로우)

```
1. User: "Scan" 버튼 클릭 (Frontend)
   ↓
2. useTriggerScan.mutate() → POST /projects/{pid}/targets/{tid}/scan
   ↓
3. API Layer: create_scan_task() → TargetService.trigger_scan()
   ↓
4. Service Layer:
   - Task 생성 (DB, status: PENDING)
   - TaskManager.enqueue() → Redis Queue RPUSH
   ↓
5. API Layer: 202 Accepted 반환 (task_id 포함)
   ↓
6. Frontend: useTaskStatus() 폴링 시작 (5초 간격)
   ↓
7. Worker: TaskManager.dequeue() → Redis Queue LPOP
   ↓
8. Worker: Task 상태 업데이트 (status: RUNNING)
   ↓
9. CrawlerService.crawl()
   - Playwright Browser Launch
   - page.goto(url, wait_until="networkidle")
   - Link 추출 (<a href>)
   - Set으로 중복 제거
   ↓
10. AssetService.process_asset() (각 Link별로)
    - content_hash 생성 (SHA256 of "METHOD:URL")
    - 기존 Asset 존재 확인 (content_hash UNIQUE)
    - 존재 시: last_seen_at 업데이트
    - 미존재 시: 신규 Asset 생성
    - AssetDiscovery 이력 레코드 생성
   ↓
11. Task 상태 업데이트 (status: COMPLETED, result JSON 저장)
    ↓
12. Frontend: useTaskStatus() 폴링 감지
    - Task 상태 COMPLETED 확인
    - 폴링 중지
    - UI 업데이트 (ScanStatusBadge: 녹색)
```

### 데이터 플로우 다이어그램

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
│  FastAPI    │ ───(4)───► ┌──────────┐
│  API Layer  │            │PostgreSQL│
└──────┬──────┘            │ (Task)   │
       │ (3)               └──────────┘
       ▼
┌─────────────┐
│  Service    │ ───(5)───► ┌──────────┐
│   Layer     │            │  Redis   │
└─────────────┘            │  Queue   │
                           └─────┬────┘
                                 │ (6) Dequeue
                                 ▼
                           ┌─────────────┐
                           │   Worker    │
                           └──────┬──────┘
                                  │ (7) Crawl
                                  ▼
                           ┌─────────────┐
                           │ Playwright  │
                           └──────┬──────┘
                                  │ (8) Links
                                  ▼
                           ┌─────────────┐
                           │AssetService │
                           └──────┬──────┘
                                  │ (9) Save
                                  ▼
                           ┌─────────────┐
                           │PostgreSQL   │
                           │ (Assets)    │
                           └─────────────┘
```

---

## 비동기 처리 패턴

### Backend: Redis Queue + Worker Process (ARQ 패턴)

#### 개념

**ARQ (Async Redis Queue) 패턴**:
- API 서버와 크롤링 작업 분리
- Worker는 독립 프로세스로 실행
- Redis FIFO Queue로 작업 관리

#### 아키텍처

```
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│   FastAPI     │         │     Redis     │         │    Worker     │
│   API Server  │         │     Queue     │         │   Process     │
└───────┬───────┘         └───────┬───────┘         └───────┬───────┘
        │                         │                         │
        │ (1) Enqueue Task        │                         │
        ├────────────────────────►│                         │
        │                         │                         │
        │                         │ (2) Dequeue Task        │
        │                         │◄────────────────────────┤
        │                         │                         │
        │                         │                         │ (3) Crawl
        │                         │                         │
        │ (4) Update Status       │                         │
        │◄────────────────────────┴─────────────────────────┤
```

#### 구현 코드

**TaskManager** (app/core/queue.py):
```python
import redis.asyncio as redis
import json
from app.core.config import settings

class TaskManager:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)

    async def enqueue(self, task_data: dict):
        """작업을 큐에 추가 (RPUSH)"""
        await self.redis.rpush(
            "tasks:queue",
            json.dumps(task_data)
        )

    async def dequeue(self) -> dict | None:
        """큐에서 작업 가져오기 (LPOP)"""
        data = await self.redis.lpop("tasks:queue")
        return json.loads(data) if data else None
```

**Worker** (app/worker.py):
```python
import asyncio
from app.core.queue import TaskManager
from app.services.crawler_service import CrawlerService
from app.services.task_service import TaskService

async def worker_loop():
    task_manager = TaskManager()

    while True:
        # 큐에서 작업 가져오기
        task_data = await task_manager.dequeue()

        if task_data:
            task_id = task_data['task_id']

            # Task 상태 업데이트 (RUNNING)
            await TaskService.update_task_status(task_id, "RUNNING")

            try:
                # 크롤링 수행
                links = await CrawlerService.crawl(task_data['target_url'])

                # Asset 저장
                for link in links:
                    await AssetService.process_asset(
                        task_id=task_id,
                        target_id=task_data['target_id'],
                        url=link
                    )

                # Task 상태 업데이트 (COMPLETED)
                await TaskService.update_task_status(
                    task_id,
                    "COMPLETED",
                    result={"found_links": len(links)}
                )

            except Exception as e:
                # Task 상태 업데이트 (FAILED)
                await TaskService.update_task_status(
                    task_id,
                    "FAILED",
                    result={"error": str(e)}
                )

        else:
            # 큐가 비어있으면 1초 대기
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(worker_loop())
```

#### 실행 방법

```bash
# 터미널 1: API 서버
cd backend
uv run uvicorn app.main:app --reload

# 터미널 2: Worker
cd backend
uv run python -m app.worker
```

---

### Frontend: TanStack Query Polling

#### 개념

**Polling**: 주기적으로 서버에 요청을 보내 상태 변화를 감지

**사용 사례**:
- Task 상태 추적 (PENDING → RUNNING → COMPLETED)
- 실시간 업데이트 (프로젝트 목록)

#### 구현 코드

**Task 상태 폴링** (hooks/useTasks.ts):
```typescript
export function useTaskStatus(taskId: number) {
  return useQuery({
    queryKey: taskKeys.detail(taskId),
    queryFn: () => taskService.getTaskStatus(taskId),
    refetchInterval: (query) => {
      const data = query.state.data;

      // 데이터 없으면 5초 간격
      if (!data) return 5000;

      // COMPLETED 또는 FAILED 시 폴링 중지
      if (data.status === 'COMPLETED' || data.status === 'FAILED') {
        return false;
      }

      // PENDING 또는 RUNNING 시 5초 간격
      return 5000;
    }
  });
}
```

**UI 컴포넌트** (components/features/target/ScanStatusBadge.tsx):
```typescript
import { useTaskStatus } from '@/hooks/useTasks';
import { Badge } from '@/components/ui/badge';

export function ScanStatusBadge({ taskId }: { taskId: number }) {
  const { data: task } = useTaskStatus(taskId);

  if (!task) return null;

  const statusColor = {
    PENDING: 'bg-gray-500',
    RUNNING: 'bg-blue-500 animate-pulse',
    COMPLETED: 'bg-green-500',
    FAILED: 'bg-red-500'
  }[task.status];

  return (
    <Badge className={statusColor}>
      {task.status}
    </Badge>
  );
}
```

#### 폴링 중지 조건

- Task 상태가 `COMPLETED` 또는 `FAILED`로 변경되면 자동 중지
- 컴포넌트 언마운트 시 자동 중지
- 사용자가 페이지를 벗어나면 자동 중지

---

### 비동기 처리 장점

#### Backend

1. **응답 속도 향상**: API는 즉시 202 Accepted 반환
2. **서버 리소스 절약**: 크롤링 작업은 별도 프로세스에서 처리
3. **확장성**: Worker 프로세스를 여러 개 실행 가능
4. **안정성**: Worker 크래시 시 API 서버는 영향 없음

#### Frontend

1. **실시간 업데이트**: 폴링으로 Task 상태 추적
2. **UX 향상**: 진행 상황을 사용자에게 표시
3. **자동 중지**: 완료 시 폴링 자동 중지 (네트워크 절약)

---

**다음 문서**: [AGENT_SYSTEM.md](AGENT_SYSTEM.md)

[← 메인 문서로 돌아가기](../README.md)
