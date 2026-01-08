# 프로젝트 구조

[← 메인 문서로 돌아가기](../README.md)

---

## 목차

1. [Backend 디렉토리 구조](#backend-디렉토리-구조)
2. [Frontend 디렉토리 구조](#frontend-디렉토리-구조)
3. [파일 통계](#파일-통계)
4. [주요 파일 경로](#주요-파일-경로)

---

## Backend 디렉토리 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 애플리케이션 진입점
│   ├── worker.py                  # Redis Queue Worker (비동기 크롤링)
│   │
│   ├── core/                      # 핵심 인프라
│   │   ├── config.py              # 환경 설정 (Pydantic Settings)
│   │   ├── db.py                  # PostgreSQL AsyncEngine
│   │   ├── redis.py               # Redis 연결
│   │   └── queue.py               # TaskManager (Redis Queue 관리)
│   │
│   ├── models/                    # SQLModel 엔티티 (4개)
│   │   ├── project.py             # Project (is_archived 지원)
│   │   ├── target.py              # Target (scope 지원)
│   │   ├── task.py                # Task (PENDING/RUNNING/COMPLETED/FAILED)
│   │   └── asset.py               # Asset, AssetDiscovery (공격 표면)
│   │
│   ├── services/                  # 비즈니스 로직 레이어 (5개)
│   │   ├── project_service.py     # Project CRUD
│   │   ├── target_service.py      # Target CRUD
│   │   ├── task_service.py        # Task 생성 및 큐 관리
│   │   ├── crawler_service.py     # Playwright 크롤러
│   │   └── asset_service.py       # Asset 중복 제거 및 이력 관리
│   │
│   └── api/v1/endpoints/          # RESTful API (2개)
│       ├── project.py             # Project + Target CRUD
│       └── task.py                # Task 트리거 & 조회
│
├── tests/                         # Pytest 테스트 스위트 (11개)
│   ├── api/                       # API 엔드포인트 테스트
│   ├── core/                      # 인프라 테스트
│   ├── services/                  # 서비스 레이어 테스트
│   └── integration/               # 통합 테스트
│
├── alembic/                       # DB 마이그레이션
│   ├── versions/                  # 8개 마이그레이션 파일
│   └── env.py
│
├── docker/
│   └── docker-compose.yml         # PostgreSQL + Redis
│
├── pyproject.toml                 # UV 의존성 관리
└── alembic.ini                    # Alembic 설정
```

### Backend 파일 통계

- Python 파일: 19개
- 테스트 파일: 11개
- 마이그레이션: 8개

---

### 주요 Backend 파일 설명

#### app/main.py

FastAPI 애플리케이션 진입점

**주요 내용**:
- FastAPI 앱 초기화
- CORS 미들웨어 설정
- 라우터 등록 (Project, Task)
- 헬스 체크 엔드포인트

**코드 예시**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import project, task

app = FastAPI(title="EAZY API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(project.router, prefix="/api/v1", tags=["projects"])
app.include_router(task.router, prefix="/api/v1", tags=["tasks"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

#### app/worker.py

Redis Queue Worker (비동기 크롤링 작업 처리)

**주요 내용**:
- Redis Queue에서 작업 Dequeue
- CrawlerService 호출
- Task 상태 업데이트

**코드 예시**:
```python
import asyncio
from app.core.queue import TaskManager
from app.services.crawler_service import CrawlerService

async def worker_loop():
    task_manager = TaskManager()

    while True:
        task = await task_manager.dequeue()
        if task:
            await CrawlerService.crawl(task)
        else:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(worker_loop())
```

---

#### app/core/config.py

환경 설정 (Pydantic Settings)

**주요 내용**:
- 환경 변수 로드 (.env 파일)
- PostgreSQL 연결 정보
- Redis 연결 정보
- 보안 설정 (SECRET_KEY)

**코드 예시**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    REDIS_URL: str

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

#### app/services/crawler_service.py

Playwright 기반 크롤링 서비스

**주요 내용**:
- Chromium 브라우저 런칭
- JavaScript 렌더링 대기
- Link 추출 (`<a href>`)
- 중복 제거

**코드 예시**:
```python
from playwright.async_api import async_playwright

class CrawlerService:
    @staticmethod
    async def crawl(target_url: str) -> list[str]:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto(target_url, wait_until="networkidle")

            # Link 추출
            links = await page.eval_on_selector_all(
                'a[href]',
                'elements => elements.map(e => e.href)'
            )

            await browser.close()
            return list(set(links))  # 중복 제거
```

**상세 정보**: [ARCHITECTURE.md](ARCHITECTURE.md#데이터-플로우-스캔-트리거-예시)

---

#### app/services/asset_service.py

Asset 중복 제거 및 이력 관리

**주요 내용**:
- content_hash 생성 (SHA256 of "METHOD:URL")
- 중복 제거 (Upsert)
- AssetDiscovery 이력 생성

**코드 예시**:
```python
import hashlib
from sqlmodel import select
from app.models.asset import Asset, AssetDiscovery

class AssetService:
    @staticmethod
    async def process_asset(db, task_id, target_id, url, method="GET"):
        # content_hash 생성
        content = f"{method}:{url}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # 기존 Asset 조회
        result = await db.execute(
            select(Asset).where(Asset.content_hash == content_hash)
        )
        existing_asset = result.scalar_one_or_none()

        if existing_asset:
            # 기존 Asset 업데이트 (last_seen_at)
            existing_asset.last_seen_at = datetime.utcnow()
            db.add(existing_asset)
            asset_id = existing_asset.id
        else:
            # 신규 Asset 생성
            new_asset = Asset(
                target_id=target_id,
                content_hash=content_hash,
                type="URL",
                source="HTML",
                method=method,
                url=url,
                path=urlparse(url).path,
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow()
            )
            db.add(new_asset)
            await db.commit()
            await db.refresh(new_asset)
            asset_id = new_asset.id

        # AssetDiscovery 이력 생성
        discovery = AssetDiscovery(
            task_id=task_id,
            asset_id=asset_id,
            discovered_at=datetime.utcnow()
        )
        db.add(discovery)
        await db.commit()
```

**상세 정보**: [db_schema.md](db_schema.md#assets-공격-표면)

---

## Frontend 디렉토리 구조

```
frontend/src/
├── components/
│   ├── ui/                        # 93개 shadcn/ui 컴포넌트 (Radix UI 기반)
│   │   ├── button.tsx             # Button, ButtonGroup
│   │   ├── dialog.tsx             # Dialog, Alert Dialog
│   │   ├── form.tsx               # Form 컴포넌트
│   │   ├── input.tsx, textarea.tsx
│   │   ├── table.tsx              # Table (TanStack Table)
│   │   ├── card.tsx, badge.tsx
│   │   └── ... (총 93개)
│   │
│   ├── features/                  # 도메인 컴포넌트
│   │   ├── project/               # 9개 컴포넌트
│   │   │   ├── CreateProjectForm.tsx
│   │   │   ├── EditProjectForm.tsx
│   │   │   ├── DeleteProjectDialog.tsx
│   │   │   ├── ArchivedDialog.tsx
│   │   │   ├── RestoreDialog.tsx
│   │   │   ├── PermanentDeleteDialog.tsx
│   │   │   ├── ProjectFormFields.tsx
│   │   │   ├── ActiveProjectItem.tsx
│   │   │   └── ArchivedProjectItem.tsx
│   │   │
│   │   └── target/                # 5개 컴포넌트
│   │       ├── TargetList.tsx     # Target 목록 테이블
│   │       ├── CreateTargetForm.tsx
│   │       ├── EditTargetForm.tsx
│   │       ├── DeleteTargetDialog.tsx
│   │       └── TargetFormFields.tsx
│   │
│   ├── layout/                    # 3개 레이아웃 컴포넌트
│   │   ├── MainLayout.tsx         # 전체 레이아웃 (Grid)
│   │   ├── Header.tsx             # 상단 헤더
│   │   └── Sidebar.tsx            # 동적 사이드바 (422줄)
│   │
│   └── theme/                     # 2개 테마 컴포넌트
│       ├── theme-provider.tsx
│       └── theme-toggle.tsx
│
├── pages/                         # 5개 페이지 컴포넌트
│   ├── ProjectsPage.tsx           # 프로젝트 허브
│   ├── ActiveProjectsListPage.tsx # 활성 프로젝트 목록
│   ├── ArchivedProjectsPage.tsx   # 아카이브 프로젝트 목록
│   ├── ProjectDetailPage.tsx      # 프로젝트 상세 + Target 관리
│   └── DashboardPage.tsx          # 대시보드 (placeholder)
│
├── hooks/                         # Custom Hooks (4개)
│   ├── useProjects.ts             # 7개 export (CRUD + 일괄 삭제)
│   ├── useTargets.ts              # 6개 export (CRUD + 스캔 트리거)
│   ├── useTasks.ts                # Task 상태 폴링 (5초 간격)
│   └── use-mobile.tsx             # 모바일 감지
│
├── services/                      # API 클라이언트 (3개)
│   ├── projectService.ts          # 17개 테스트 통과
│   ├── targetService.ts           # 15개 테스트 통과
│   └── taskService.ts             # 4개 테스트 통과
│
├── types/                         # TypeScript 타입 정의 (3개)
│   ├── project.ts
│   ├── target.ts
│   └── task.ts
│
├── schemas/                       # Zod 스키마 (2개)
│   ├── projectSchema.ts
│   └── targetSchema.ts
│
├── lib/                           # 유틸리티
│   ├── api.ts                     # Axios 설정 및 래퍼
│   └── utils.ts                   # cn (clsx + tailwind-merge)
│
├── utils/
│   └── date.ts                    # 날짜 포맷팅 (date-fns)
│
├── config/
│   └── nav.ts                     # 네비게이션 설정
│
├── App.tsx                        # 라우팅 설정
├── main.tsx                       # React 진입점
└── index.css                      # TailwindCSS v4 설정
```

### Frontend 파일 통계

- TypeScript 파일: 151개
- 테스트 파일: 16개 (168개 테스트 통과)
- UI 컴포넌트: 93개 (shadcn/ui)
- Storybook Stories: 47개

---

### 주요 Frontend 파일 설명

#### src/App.tsx

라우팅 설정 (React Router v7)

**주요 내용**:
- 라우트 정의
- MainLayout 래핑
- 404 페이지

**코드 예시**:
```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import ProjectsPage from './pages/ProjectsPage';
import ProjectDetailPage from './pages/ProjectDetailPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<ProjectsPage />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

---

#### src/components/layout/Sidebar.tsx

동적 사이드바 (422줄)

**주요 내용**:
- 프로젝트 목록 표시 (체크박스 다중 선택)
- 일괄 작업 (Archive, Restore, Delete)
- 네비게이션 링크
- 테마 토글

**특징**:
- TanStack Query로 실시간 데이터 동기화
- Optimistic Updates
- 접기/펼치기 애니메이션
- 모바일 반응형

**상세 정보**: [ARCHITECTURE.md](ARCHITECTURE.md#frontend-atomic-design-architecture)

---

#### src/hooks/useProjects.ts

프로젝트 관련 TanStack Query Hooks (7개)

**Export 목록**:
1. `useProjects()` - 목록 조회
2. `useProject(id)` - 단일 조회
3. `useCreateProject()` - 생성
4. `useUpdateProject()` - 수정
5. `useDeleteProject()` - Archive
6. `useRestoreProject()` - Restore
7. `useBulkDeleteProjects()` - 일괄 삭제

**코드 예시**:
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
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
    }
  });
}
```

---

#### src/services/projectService.ts

프로젝트 API 클라이언트

**주요 내용**:
- CRUD 함수
- Axios 기반 HTTP 요청
- 에러 핸들링

**테스트 통과**: 17개

**코드 예시**:
```typescript
import api from '@/lib/api';
import { Project, ProjectCreate, ProjectUpdate } from '@/types/project';

export const projectService = {
  async getProjects(params?: { archived?: boolean }): Promise<Project[]> {
    const response = await api.get('/projects/', { params });
    return response.data;
  },

  async createProject(data: ProjectCreate): Promise<Project> {
    const response = await api.post('/projects/', data);
    return response.data;
  },

  async updateProject(id: number, data: ProjectUpdate): Promise<Project> {
    const response = await api.patch(`/projects/${id}`, data);
    return response.data;
  },

  async deleteProject(id: number, permanent?: boolean): Promise<void> {
    await api.delete(`/projects/${id}`, { params: { permanent } });
  }
};
```

---

#### src/pages/ProjectDetailPage.tsx

프로젝트 상세 페이지 (Target 관리 통합)

**주요 내용**:
- 프로젝트 메타데이터 표시
- TargetList 컴포넌트 통합
- 스캔 트리거 버튼
- Task 상태 폴링

**테스트 통과**: 28개

**코드 예시**:
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

## 파일 통계

### Backend

| 카테고리 | 개수 |
|---------|------|
| Python 소스 파일 | 19개 |
| 테스트 파일 | 11개 |
| 마이그레이션 파일 | 8개 |
| 설정 파일 | 3개 (pyproject.toml, alembic.ini, docker-compose.yml) |

### Frontend

| 카테고리 | 개수 |
|---------|------|
| TypeScript 소스 파일 | 151개 |
| 테스트 파일 | 16개 |
| Storybook Stories | 47개 |
| UI 컴포넌트 (shadcn) | 93개 |
| 도메인 컴포넌트 (features) | 14개 |
| 페이지 컴포넌트 | 5개 |
| Custom Hooks | 4개 |

### 테스트 통계

| 영역 | 파일 수 | 테스트 수 | 상태 |
|-----|--------|---------|------|
| Frontend | 16개 | 168개 | 모두 통과 |
| Backend | 11개 | 다수 | 모두 통과 |

---

## 주요 파일 경로

### 문서

- `/Users/lrtk/Documents/Project/EAZY/README.md` - 프로젝트 개요
- `/Users/lrtk/Documents/Project/EAZY/docs/README.md` - 문서 메인 인덱스
- `/Users/lrtk/Documents/Project/EAZY/docs/QUICK_START.md` - 빠른 시작 가이드
- `/Users/lrtk/Documents/Project/EAZY/docs/PRD.md` - 제품 요구사항 정의서
- `/Users/lrtk/Documents/Project/EAZY/docs/db_schema.md` - 데이터베이스 스키마
- `/Users/lrtk/Documents/Project/EAZY/docs/api_spec.md` - API 명세
- `/Users/lrtk/Documents/Project/EAZY/docs/coding_convention.md` - 코딩 컨벤션
- `/Users/lrtk/Documents/Project/EAZY/docs/plans/PLAN_MVP_Backend.md` - 백엔드 MVP 계획
- `/Users/lrtk/Documents/Project/EAZY/docs/plans/frontend/INDEX.md` - 프론트엔드 MVP 메인 인덱스
- `/Users/lrtk/Documents/Project/EAZY/docs/plans/frontend/PHASE5_CURRENT.md` - 현재 진행 중인 Phase

### Backend 핵심

- `/Users/lrtk/Documents/Project/EAZY/backend/app/main.py` - FastAPI 앱
- `/Users/lrtk/Documents/Project/EAZY/backend/app/worker.py` - Redis Worker
- `/Users/lrtk/Documents/Project/EAZY/backend/app/services/crawler_service.py` - Playwright 크롤러
- `/Users/lrtk/Documents/Project/EAZY/backend/app/services/asset_service.py` - Asset 처리
- `/Users/lrtk/Documents/Project/EAZY/backend/app/core/config.py` - 환경 설정
- `/Users/lrtk/Documents/Project/EAZY/backend/app/core/db.py` - DB 연결
- `/Users/lrtk/Documents/Project/EAZY/backend/app/core/queue.py` - Task Queue
- `/Users/lrtk/Documents/Project/EAZY/backend/app/models/project.py` - Project 모델
- `/Users/lrtk/Documents/Project/EAZY/backend/app/models/target.py` - Target 모델
- `/Users/lrtk/Documents/Project/EAZY/backend/app/models/task.py` - Task 모델
- `/Users/lrtk/Documents/Project/EAZY/backend/app/models/asset.py` - Asset 모델
- `/Users/lrtk/Documents/Project/EAZY/backend/pyproject.toml` - UV 의존성
- `/Users/lrtk/Documents/Project/EAZY/backend/alembic.ini` - Alembic 설정
- `/Users/lrtk/Documents/Project/EAZY/backend/docker/docker-compose.yml` - PostgreSQL + Redis

### Frontend 핵심

- `/Users/lrtk/Documents/Project/EAZY/frontend/src/App.tsx` - 라우팅
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/main.tsx` - React 진입점
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/pages/ProjectsPage.tsx` - 프로젝트 허브
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/pages/ProjectDetailPage.tsx` - 프로젝트 상세
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/pages/ActiveProjectsListPage.tsx` - 활성 프로젝트 목록
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/pages/ArchivedProjectsPage.tsx` - 아카이브 목록
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/components/layout/MainLayout.tsx` - 메인 레이아웃
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/components/layout/Sidebar.tsx` - 사이드바
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/hooks/useProjects.ts` - 프로젝트 Query 훅
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/hooks/useTargets.ts` - Target Query 훅
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/hooks/useTasks.ts` - Task Query 훅
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/services/projectService.ts` - 프로젝트 API 클라이언트
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/services/targetService.ts` - Target API 클라이언트
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/services/taskService.ts` - Task API 클라이언트
- `/Users/lrtk/Documents/Project/EAZY/frontend/package.json` - npm 의존성
- `/Users/lrtk/Documents/Project/EAZY/frontend/vite.config.ts` - Vite 설정
- `/Users/lrtk/Documents/Project/EAZY/frontend/tsconfig.json` - TypeScript 설정

### Claude 에이전트

- `/Users/lrtk/Documents/Project/EAZY/.claude/settings.local.json` - 에이전트 설정
- `/Users/lrtk/Documents/Project/EAZY/.claude/agents/` - 17개 전문 에이전트

---

**다음 문서**: [ARCHITECTURE.md](ARCHITECTURE.md)

[← 메인 문서로 돌아가기](../README.md)
