# 테스팅 전략 (Testing Strategy)

[← 메인 문서로 돌아가기](../README.md)

**작성일**: 2026-01-09
**대상 독자**: 모든 개발자 (Backend, Frontend)

---

## 목차

- [TDD 엄격 준수](#tdd-엄격-준수)
- [Backend 테스트](#backend-테스트)
  - [프레임워크](#backend-프레임워크)
  - [테스트 구조](#backend-테스트-구조)
  - [Fixtures](#backend-fixtures)
  - [테스트 예시](#backend-테스트-예시)
  - [Mocking 전략](#backend-mocking-전략)
  - [실행 방법](#backend-실행-방법)
- [Frontend 테스트](#frontend-테스트)
  - [프레임워크](#frontend-프레임워크)
  - [테스트 구조](#frontend-테스트-구조)
  - [테스트 통계](#frontend-테스트-통계)
  - [테스트 예시](#frontend-테스트-예시)
  - [Mock 설정](#frontend-mock-설정)
  - [실행 방법](#frontend-실행-방법)
- [Storybook 통합 테스트](#storybook-통합-테스트)
- [Coverage 목표](#coverage-목표)
- [테스트 작성 가이드라인](#테스트-작성-가이드라인)

---

## TDD 엄격 준수

EAZY 프로젝트는 **Test-Driven Development (TDD)**를 엄격히 준수합니다.

### RED → GREEN → REFACTOR 사이클

```
1. RED: 테스트 작성 (실패)
2. GREEN: 최소한의 코드로 테스트 통과
3. REFACTOR: 코드 개선 (테스트는 여전히 통과)
```

상세한 TDD 가이드는 [TDD_GUIDE.md](./TDD_GUIDE.md)를 참고하세요.

---

## Backend 테스트

### Backend 프레임워크

| 도구 | 용도 |
|------|------|
| **Pytest** | 테스트 러너 (단위 테스트, 통합 테스트) |
| **Pytest-asyncio** | 비동기 테스트 지원 |
| **Pytest-cov** | 코드 커버리지 측정 |
| **HTTPX** | FastAPI 테스트 클라이언트 |
| **unittest.mock** | Mocking 라이브러리 |

### Backend 테스트 구조

```
backend/tests/
├── conftest.py                  # Pytest Fixtures (공통 설정)
│
├── api/                         # API 엔드포인트 테스트
│   ├── test_health.py           # 헬스체크 API
│   ├── test_projects.py         # Project CRUD (8개 테스트)
│   ├── test_targets.py          # Target CRUD
│   ├── test_targets_mgmt.py     # Target 관리
│   └── test_tasks.py            # Task API (3개 테스트)
│
├── core/                        # 인프라 테스트
│   ├── test_task_manager.py     # Redis Queue 테스트
│   └── test_worker.py           # Worker 로직 테스트
│
├── services/                    # 서비스 레이어 테스트
│   ├── test_crawler.py          # Crawler 단위 테스트 (Mock)
│   └── test_asset_service.py    # Asset 처리 로직
│
└── integration/                 # 통합 테스트
    └── test_full_flow.py        # 전체 스캔 플로우 통합 테스트
```

**총 테스트 파일**: 11개

### Backend Fixtures

```python
# tests/conftest.py

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db
from app.models.project import Project
from app.models.target import Target
from app.models.task import Task
from app.models.asset import Asset, AssetDiscovery


@pytest.fixture
async def db_session() -> AsyncSession:
    """
    테스트용 DB 세션 Fixture

    특징:
    - 각 테스트마다 독립적인 트랜잭션
    - 테스트 종료 후 자동 롤백
    - 테이블 정리 (CASCADE DELETE)
    """
    # 테스트용 DB 엔진 생성
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost/eazy_test_db",
        echo=False
    )

    # 세션 팩토리
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 테스트 시작 전: 테이블 정리
        await session.execute("DELETE FROM asset_discoveries")
        await session.execute("DELETE FROM assets")
        await session.execute("DELETE FROM tasks")
        await session.execute("DELETE FROM targets")
        await session.execute("DELETE FROM projects")
        await session.commit()

        yield session

        # 테스트 종료 후: 롤백
        await session.rollback()


@pytest.fixture
async def redis_client():
    """
    테스트용 Redis 클라이언트 Fixture

    특징:
    - 테스트용 Redis DB (DB 1)
    - 테스트 종료 후 FLUSHDB
    """
    import redis.asyncio as redis

    client = await redis.from_url(
        "redis://localhost:6379/1",  # 테스트용 DB 1
        encoding="utf-8",
        decode_responses=True
    )

    yield client

    # 테스트 종료 후: Redis 정리
    await client.flushdb()
    await client.close()


@pytest.fixture
async def client(db_session, redis_client) -> AsyncClient:
    """
    FastAPI 테스트 클라이언트 Fixture

    특징:
    - dependency_overrides로 DB/Redis 주입
    - 비동기 HTTP 클라이언트
    """
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

### Backend 테스트 예시

#### 1. API 엔드포인트 테스트

```python
# tests/api/test_projects.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    """프로젝트 생성 API 테스트"""
    response = await client.post("/api/v1/projects/", json={
        "name": "Test Project",
        "description": "Test Description"
    })

    # 응답 검증
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "Test Description"
    assert data["is_archived"] is False
    assert data["archived_at"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_archive_project(client: AsyncClient, db_session):
    """프로젝트 Archive (Soft Delete) 테스트"""
    # Given: 프로젝트 생성
    create_response = await client.post("/api/v1/projects/", json={
        "name": "Project to Archive",
        "description": "Will be archived"
    })
    project_id = create_response.json()["id"]

    # When: Archive 요청
    delete_response = await client.delete(f"/api/v1/projects/{project_id}")

    # Then: 204 No Content
    assert delete_response.status_code == 204

    # DB 확인: is_archived=True
    get_response = await client.get(f"/api/v1/projects/{project_id}")
    archived_project = get_response.json()
    assert archived_project["is_archived"] is True
    assert archived_project["archived_at"] is not None


@pytest.mark.asyncio
async def test_list_projects_with_archived_filter(client: AsyncClient):
    """아카이브 필터 테스트"""
    # Given: 활성 프로젝트 2개, 아카이브 프로젝트 1개 생성
    await client.post("/api/v1/projects/", json={"name": "Active 1"})
    await client.post("/api/v1/projects/", json={"name": "Active 2"})

    archived_response = await client.post("/api/v1/projects/", json={"name": "Archived"})
    archived_id = archived_response.json()["id"]
    await client.delete(f"/api/v1/projects/{archived_id}")

    # When: archived=false 필터
    active_response = await client.get("/api/v1/projects/?archived=false")
    active_projects = active_response.json()

    # Then: 활성 프로젝트만 반환
    assert len(active_projects) == 2
    assert all(p["is_archived"] is False for p in active_projects)

    # When: archived=true 필터
    archived_response = await client.get("/api/v1/projects/?archived=true")
    archived_projects = archived_response.json()

    # Then: 아카이브 프로젝트만 반환
    assert len(archived_projects) == 1
    assert all(p["is_archived"] is True for p in archived_projects)
```

#### 2. 서비스 레이어 테스트

```python
# tests/services/test_asset_service.py

import pytest
from app.services.asset_service import AssetService
from app.models.asset import Asset, AssetDiscovery


@pytest.mark.asyncio
async def test_process_asset_creates_new_asset(db_session):
    """신규 Asset 생성 테스트"""
    # Given: Asset 데이터
    asset_data = {
        "target_id": 1,
        "type": "URL",
        "source": "HTML",
        "method": "GET",
        "url": "https://example.com/page1",
        "path": "/page1"
    }

    # When: Asset 처리
    asset = await AssetService.process_asset(db_session, task_id=1, **asset_data)

    # Then: 신규 Asset 생성
    assert asset.id is not None
    assert asset.url == "https://example.com/page1"
    assert asset.content_hash is not None

    # AssetDiscovery 레코드 생성 확인
    discovery = await db_session.execute(
        select(AssetDiscovery).where(AssetDiscovery.asset_id == asset.id)
    )
    assert discovery.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_process_asset_updates_existing_asset(db_session):
    """기존 Asset 업데이트 테스트 (중복 제거)"""
    # Given: 기존 Asset
    asset_data = {
        "target_id": 1,
        "type": "URL",
        "source": "HTML",
        "method": "GET",
        "url": "https://example.com/page1",
        "path": "/page1"
    }
    existing_asset = await AssetService.process_asset(
        db_session, task_id=1, **asset_data
    )
    original_first_seen = existing_asset.first_seen_at

    # When: 동일한 Asset 재처리 (다른 Task)
    updated_asset = await AssetService.process_asset(
        db_session, task_id=2, **asset_data
    )

    # Then: ID는 동일 (UPSERT), last_seen_at만 업데이트
    assert updated_asset.id == existing_asset.id
    assert updated_asset.first_seen_at == original_first_seen
    assert updated_asset.last_seen_at > original_first_seen
    assert updated_asset.last_task_id == 2
```

### Backend Mocking 전략

#### 1. Playwright Crawler Mocking

```python
# tests/services/test_crawler.py

import pytest
from unittest.mock import AsyncMock, patch
from app.services.crawler_service import CrawlerService


@pytest.mark.asyncio
async def test_crawl_extracts_links():
    """크롤러 링크 추출 테스트 (Playwright Mock)"""
    # Mock Playwright Browser
    with patch("app.services.crawler_service.async_playwright") as mock_playwright:
        mock_browser = AsyncMock()
        mock_page = AsyncMock()

        # Mock page.goto()
        mock_page.goto = AsyncMock()

        # Mock locator (링크 추출)
        mock_links = AsyncMock()
        mock_links.all_text_contents = AsyncMock(return_value=[
            "https://example.com/page1",
            "https://example.com/page2",
            "/relative-path"
        ])
        mock_page.locator = AsyncMock(return_value=mock_links)

        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(
            return_value=mock_browser
        )

        # When: Crawl 실행
        links = await CrawlerService.crawl("https://example.com")

        # Then: 링크 추출 확인
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
        assert len(links) >= 2
```

#### 2. Redis Queue Mocking

```python
# tests/core/test_task_manager.py

import pytest
from unittest.mock import AsyncMock, patch
from app.core.queue import TaskManager


@pytest.mark.asyncio
async def test_enqueue_task():
    """Task Enqueue 테스트 (Redis Mock)"""
    with patch("app.core.queue.redis.asyncio.from_url") as mock_redis:
        mock_client = AsyncMock()
        mock_client.rpush = AsyncMock(return_value=1)
        mock_redis.return_value = mock_client

        # Given: TaskManager
        task_manager = TaskManager()

        # When: Task Enqueue
        task_data = {"task_id": 1, "type": "CRAWL", "target_id": 1}
        await task_manager.enqueue(task_data)

        # Then: Redis RPUSH 호출 확인
        mock_client.rpush.assert_called_once()
```

### Backend 실행 방법

```bash
# 1. 전체 테스트 실행
cd backend
uv run pytest

# 2. 특정 파일 실행
uv run pytest tests/api/test_projects.py

# 3. 특정 테스트 실행
uv run pytest tests/api/test_projects.py::test_create_project

# 4. Verbose 모드 (-v)
uv run pytest -v

# 5. 실패한 테스트만 재실행 (--lf)
uv run pytest --lf

# 6. 마지막 실패 테스트부터 실행 (--ff)
uv run pytest --ff

# 7. 커버리지 측정
uv run pytest --cov=app --cov-report=html

# 8. 커버리지 리포트 확인
open htmlcov/index.html  # macOS
```

**주요 옵션**:
- `-v`: Verbose (상세 출력)
- `-s`: 표준 출력 표시 (print 디버깅)
- `-k <pattern>`: 패턴 매칭 테스트만 실행 (예: `-k "archive"`)
- `--lf`: Last Failed (실패한 테스트만)
- `--ff`: Failed First (실패한 테스트부터)
- `--cov=<module>`: 커버리지 측정

---

## Frontend 테스트

### Frontend 프레임워크

| 도구 | 용도 |
|------|------|
| **Vitest** | 테스트 러너 (Vite 기반, 빠른 실행) |
| **React Testing Library** | React 컴포넌트 테스트 (사용자 관점) |
| **@testing-library/user-event** | 사용자 인터랙션 시뮬레이션 |
| **@testing-library/jest-dom** | DOM 매처 (toBeInTheDocument 등) |
| **Mock Service Worker (MSW)** | API Mocking |

### Frontend 테스트 구조

```
frontend/src/
├── components/
│   ├── features/
│   │   ├── project/
│   │   │   ├── CreateProjectForm.test.tsx
│   │   │   ├── EditProjectForm.test.tsx
│   │   │   ├── DeleteProjectDialog.test.tsx
│   │   │   ├── ArchivedDialog.test.tsx
│   │   │   ├── RestoreDialog.test.tsx
│   │   │   └── PermanentDeleteDialog.test.tsx
│   │   └── target/
│   │       ├── CreateTargetForm.test.tsx
│   │       ├── EditTargetForm.test.tsx
│   │       ├── TargetList.test.tsx
│   │       └── DeleteTargetDialog.test.tsx
│   └── layout/
│       └── Sidebar.test.tsx
│
├── pages/
│   └── ProjectDetailPage.test.tsx
│
├── services/
│   ├── projectService.test.ts
│   ├── targetService.test.ts
│   └── taskService.test.ts
│
├── schemas/
│   └── targetSchema.test.ts
│
└── lib/
    └── api.test.ts
```

**총 테스트 파일**: 16개

### Frontend 테스트 통계

| 카테고리 | 파일 수 | 테스트 수 | 상태 |
|---------|--------|---------|------|
| **Component** | 10개 | 120+ | ✅ 통과 |
| **Service** | 3개 | 36개 | ✅ 통과 |
| **Schema** | 1개 | 6개 | ✅ 통과 |
| **API** | 1개 | 6개 | ✅ 통과 |
| **Total** | **16개** | **168개** | **✅ 168/168** |

### Frontend 테스트 예시

#### 1. 컴포넌트 테스트 (Form)

```typescript
// src/components/features/project/CreateProjectForm.test.tsx

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { CreateProjectForm } from './CreateProjectForm';
import * as projectService from '@/services/projectService';


// Mock projectService
vi.mock('@/services/projectService');


describe('CreateProjectForm', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    });
    vi.clearAllMocks();
  });

  function renderWithProviders(ui: React.ReactElement) {
    return render(
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    );
  }

  it('should create project successfully', async () => {
    // Mock API
    const mockCreate = vi.fn().mockResolvedValue({
      id: 1,
      name: 'New Project',
      description: 'Test Description',
      is_archived: false,
      archived_at: null,
      created_at: '2026-01-09T00:00:00Z',
      updated_at: '2026-01-09T00:00:00Z'
    });
    vi.spyOn(projectService, 'createProject').mockImplementation(mockCreate);

    const user = userEvent.setup();
    renderWithProviders(<CreateProjectForm />);

    // Dialog 열기
    const trigger = screen.getByRole('button', { name: /create project/i });
    await user.click(trigger);

    // 폼 입력
    const nameInput = screen.getByLabelText(/name/i);
    await user.type(nameInput, 'New Project');

    const descInput = screen.getByLabelText(/description/i);
    await user.type(descInput, 'Test Description');

    // Submit
    const submitBtn = screen.getByRole('button', { name: /create/i });
    await user.click(submitBtn);

    // API 호출 확인
    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith({
        name: 'New Project',
        description: 'Test Description'
      });
    });
  });

  it('should show validation error for empty name', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CreateProjectForm />);

    // Dialog 열기
    const trigger = screen.getByRole('button', { name: /create project/i });
    await user.click(trigger);

    // 빈 폼 Submit
    const submitBtn = screen.getByRole('button', { name: /create/i });
    await user.click(submitBtn);

    // 유효성 검증 에러 확인
    await waitFor(() => {
      const errorMessage = screen.getByText(/name is required/i);
      expect(errorMessage).toBeInTheDocument();
    });
  });

  it('should reset form after successful creation', async () => {
    const mockCreate = vi.fn().mockResolvedValue({
      id: 1,
      name: 'New Project',
      description: '',
      is_archived: false,
      archived_at: null,
      created_at: '2026-01-09T00:00:00Z',
      updated_at: '2026-01-09T00:00:00Z'
    });
    vi.spyOn(projectService, 'createProject').mockImplementation(mockCreate);

    const user = userEvent.setup();
    renderWithProviders(<CreateProjectForm />);

    // Dialog 열기
    const trigger = screen.getByRole('button', { name: /create project/i });
    await user.click(trigger);

    // 폼 입력
    const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
    await user.type(nameInput, 'New Project');

    // Submit
    const submitBtn = screen.getByRole('button', { name: /create/i });
    await user.click(submitBtn);

    // 폼 리셋 확인
    await waitFor(() => {
      // Dialog가 닫혔으므로 input이 DOM에 없음
      expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument();
    });
  });
});
```

#### 2. 서비스 레이어 테스트

```typescript
// src/services/projectService.test.ts

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

import {
  createProject,
  getProjects,
  getProject,
  updateProject,
  deleteProject
} from './projectService';


// MSW 서버 설정
const server = setupServer();

beforeEach(() => server.listen());
afterEach(() => server.resetHandlers());
afterEach(() => server.close());


describe('projectService', () => {
  describe('createProject', () => {
    it('should create a project successfully', async () => {
      // Mock API 응답
      server.use(
        http.post('http://localhost:8000/api/v1/projects/', () => {
          return HttpResponse.json({
            id: 1,
            name: 'Test Project',
            description: 'Test Description',
            is_archived: false,
            archived_at: null,
            created_at: '2026-01-09T00:00:00Z',
            updated_at: '2026-01-09T00:00:00Z'
          }, { status: 201 });
        })
      );

      // When
      const result = await createProject({
        name: 'Test Project',
        description: 'Test Description'
      });

      // Then
      expect(result).toEqual({
        id: 1,
        name: 'Test Project',
        description: 'Test Description',
        is_archived: false,
        archived_at: null,
        created_at: '2026-01-09T00:00:00Z',
        updated_at: '2026-01-09T00:00:00Z'
      });
    });

    it('should handle API error', async () => {
      // Mock API 에러
      server.use(
        http.post('http://localhost:8000/api/v1/projects/', () => {
          return HttpResponse.json(
            { detail: 'Internal Server Error' },
            { status: 500 }
          );
        })
      );

      // When & Then
      await expect(
        createProject({ name: 'Test', description: '' })
      ).rejects.toThrow();
    });
  });

  describe('getProjects', () => {
    it('should fetch projects with archived filter', async () => {
      // Mock API 응답
      server.use(
        http.get('http://localhost:8000/api/v1/projects/', ({ request }) => {
          const url = new URL(request.url);
          const archived = url.searchParams.get('archived');

          if (archived === 'false') {
            return HttpResponse.json([
              { id: 1, name: 'Active Project', is_archived: false }
            ]);
          } else {
            return HttpResponse.json([
              { id: 2, name: 'Archived Project', is_archived: true }
            ]);
          }
        })
      );

      // When: archived=false
      const activeProjects = await getProjects({ archived: false });
      expect(activeProjects).toHaveLength(1);
      expect(activeProjects[0].is_archived).toBe(false);

      // When: archived=true
      const archivedProjects = await getProjects({ archived: true });
      expect(archivedProjects).toHaveLength(1);
      expect(archivedProjects[0].is_archived).toBe(true);
    });
  });
});
```

#### 3. Schema 유효성 검증 테스트

```typescript
// src/schemas/targetSchema.test.ts

import { describe, it, expect } from 'vitest';
import { targetFormSchema } from './targetSchema';


describe('targetFormSchema', () => {
  it('should validate valid target data', () => {
    const validData = {
      name: 'Test Target',
      url: 'https://example.com',
      scope: 'DOMAIN',
      description: 'Test Description'
    };

    const result = targetFormSchema.safeParse(validData);
    expect(result.success).toBe(true);
  });

  it('should reject invalid URL', () => {
    const invalidData = {
      name: 'Test Target',
      url: 'not-a-url',
      scope: 'DOMAIN',
      description: ''
    };

    const result = targetFormSchema.safeParse(invalidData);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('Invalid URL');
    }
  });

  it('should reject empty name', () => {
    const invalidData = {
      name: '',
      url: 'https://example.com',
      scope: 'DOMAIN',
      description: ''
    };

    const result = targetFormSchema.safeParse(invalidData);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toContain('Name is required');
    }
  });

  it('should reject invalid scope', () => {
    const invalidData = {
      name: 'Test Target',
      url: 'https://example.com',
      scope: 'INVALID_SCOPE',
      description: ''
    };

    const result = targetFormSchema.safeParse(invalidData);
    expect(result.success).toBe(false);
  });
});
```

### Frontend Mock 설정

```typescript
// vitest.setup.ts

import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';


// 각 테스트 후 정리
afterEach(() => {
  cleanup();
});


// ResizeObserver Mock (ScrollArea 컴포넌트용)
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));


// IntersectionObserver Mock
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));


// matchMedia Mock (Dark Mode 테스트용)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  }))
});
```

### Frontend 실행 방법

```bash
# 1. 전체 테스트 실행
cd frontend
npm run test

# 2. Watch 모드 (파일 변경 감지)
npm run test:watch

# 3. 특정 파일 실행
npm run test CreateProjectForm.test.tsx

# 4. UI 모드 (브라우저에서 테스트 실행)
npm run test:ui

# 5. 커버리지 측정
npm run test:coverage

# 6. 커버리지 리포트 확인
open coverage/index.html  # macOS
```

**주요 옵션**:
- `--run`: 단일 실행 (Watch 모드 비활성화)
- `--ui`: 브라우저 UI 모드
- `--coverage`: 커버리지 측정
- `--reporter=verbose`: 상세 출력

---

## Storybook 통합 테스트

EAZY 프로젝트는 **Storybook**을 통해 UI 컴포넌트를 독립적으로 개발하고 테스트합니다.

### Storybook 통계

- **총 Stories**: 47개
- **커버리지**: 모든 UI 컴포넌트 (93개)

### 실행 방법

```bash
cd frontend

# 1. Storybook 개발 서버
npm run storybook
# → http://localhost:6006

# 2. Storybook 빌드
npm run build-storybook

# 3. Storybook 테스트 (Vitest 통합)
npm run test:storybook

# 4. Playwright 브라우저 테스트 (E2E)
npm run test:storybook:e2e
```

### Chromatic 연동 (시각적 회귀 테스트)

Chromatic을 연동하면 **자동 시각적 회귀 테스트**가 가능합니다.

```bash
# Chromatic 배포
npx chromatic --project-token=<YOUR_TOKEN>
```

---

## Coverage 목표

EAZY 프로젝트의 코드 커버리지 목표는 다음과 같습니다:

| 영역 | 목표 | 현재 상태 |
|------|------|-----------|
| **Backend** | ≥80% | ✅ 80%+ |
| **Frontend** | ≥80% | ✅ 80%+ |
| **주요 기능** | 100% | ✅ 100% (TDD 적용) |

### 커버리지 확인

```bash
# Backend
cd backend
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend
npm run test:coverage
open coverage/index.html
```

---

## 테스트 작성 가이드라인

### 1. 테스트 네이밍

```python
# Good: 명확한 테스트 이름
def test_create_project_returns_201_with_valid_data():
    pass

def test_archive_project_sets_is_archived_to_true():
    pass

# Bad: 모호한 테스트 이름
def test_project():
    pass

def test_case_1():
    pass
```

### 2. AAA 패턴 (Arrange, Act, Assert)

```python
async def test_create_project(client):
    # Arrange: 테스트 데이터 준비
    project_data = {
        "name": "Test Project",
        "description": "Test Description"
    }

    # Act: 실제 동작 수행
    response = await client.post("/api/v1/projects/", json=project_data)

    # Assert: 결과 검증
    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"
```

### 3. 한 테스트에 하나의 검증

```python
# Good: 단일 책임
async def test_create_project_returns_201():
    response = await client.post("/api/v1/projects/", json={...})
    assert response.status_code == 201

async def test_create_project_returns_project_data():
    response = await client.post("/api/v1/projects/", json={...})
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["is_archived"] is False

# Bad: 여러 책임
async def test_create_project():
    response = await client.post("/api/v1/projects/", json={...})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"
    # ... (너무 많은 검증)
```

### 4. 테스트 격리

- 각 테스트는 **독립적**이어야 합니다.
- 테스트 간 순서 의존성이 없어야 합니다.
- Fixture를 활용하여 테스트 데이터를 격리합니다.

### 5. Mock 사용 최소화

- **통합 테스트**를 우선합니다.
- 외부 의존성(Network, Browser)만 Mock합니다.
- Mock이 너무 많으면 테스트 신뢰도가 낮아집니다.

---

## 참고 자료

- [TDD Guide (TDD_GUIDE.md)](./TDD_GUIDE.md) - TDD 방법론
- [Backend Development Guide (BACKEND_DEVELOPMENT.md)](./BACKEND_DEVELOPMENT.md) - Backend 개발 가이드
- [Frontend Development Guide (FRONTEND_DEVELOPMENT.md)](./FRONTEND_DEVELOPMENT.md) - Frontend 개발 가이드
- [Pytest 공식 문서](https://docs.pytest.org/)
- [Vitest 공식 문서](https://vitest.dev/)
- [React Testing Library 공식 문서](https://testing-library.com/react)

---

**다음 문서**: [Git Workflow (GIT_WORKFLOW.md)](./GIT_WORKFLOW.md)
