# 기술 스택

[← 메인 문서로 돌아가기](../README.md)

---

## 목차

1. [Backend](#backend)
2. [Frontend](#frontend)
3. [인프라](#인프라)
4. [UV 패키지 매니저](#uv-패키지-매니저)

---

## Backend

### 핵심 기술

| 기술 | 버전 | 용도 |
|------|------|------|
| **Python** | 3.12.10 | 백엔드 언어 |
| **UV** | latest | 고속 Python 패키지 매니저 (Rust 기반, pip/poetry 대체) |
| **FastAPI** | 0.115.0+ | 웹 프레임워크 (비동기 지원, 자동 문서화) |
| **SQLModel** | 0.0.22+ | ORM (Pydantic + SQLAlchemy 통합) |
| **PostgreSQL** | 15 (Alpine) | 메인 데이터베이스 (JSONB 지원) |
| **Redis** | 7 (Alpine) | 비동기 작업 큐 (Task Queue) |
| **Playwright** | 1.42.0+ | 브라우저 자동화 (크롤링) |
| **HTTPX** | 0.27.0+ | 비동기 HTTP 클라이언트 |
| **Alembic** | 1.13.0+ | 데이터베이스 마이그레이션 |
| **Pytest** | 8.1.0+ | 테스트 프레임워크 |

### 주요 라이브러리 설명

#### FastAPI

**특징**:
- ASGI 기반 고성능 웹 프레임워크
- 자동 OpenAPI(Swagger) 문서 생성
- Type Hint 기반 데이터 유효성 검증
- Pydantic 통합

**사용 예시**:
```python
from fastapi import FastAPI, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

app = FastAPI()

@app.post("/api/v1/projects/", response_model=ProjectRead)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    return await ProjectService.create_project(db, project)
```

**문서 자동 생성**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

#### SQLModel

**특징**:
- Pydantic + SQLAlchemy 통합
- Type Hint 기반 ORM
- 비동기 지원 (AsyncSession)
- 데이터 유효성 검증 내장

**사용 예시**:
```python
from sqlmodel import Field, SQLModel

class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    description: str | None = None
    is_archived: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

#### PostgreSQL

**선택 이유**:
- JSONB 타입 지원 (유연한 데이터 저장)
- 고급 인덱싱 (GIN, BTREE)
- ACID 트랜잭션
- 확장성 (수평/수직 스케일링)

**주요 기능 사용**:
```sql
-- JSONB 필드 (request_spec, response_spec, parameters)
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    request_spec JSONB,
    response_spec JSONB,
    parameters JSONB
);

-- GIN 인덱스 (JSONB 검색 최적화)
CREATE INDEX idx_asset_params ON assets USING GIN (parameters);
```

---

#### Redis

**용도**:
- 비동기 작업 큐 (Task Queue)
- 캐싱 (추후 확장)

**큐 구조**:
```
LPUSH tasks:queue '{"task_id": 123, "type": "CRAWL"}'  # 작업 추가
RPOP tasks:queue  # Worker가 작업 가져오기
```

**상세 정보**: [ARCHITECTURE.md](ARCHITECTURE.md#비동기-처리-패턴)

---

#### Playwright

**특징**:
- Chromium, Firefox, WebKit 지원
- JavaScript 렌더링 대응
- 네트워크 인터셉트 가능
- 스크린샷/PDF 생성

**사용 예시**:
```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.goto("https://example.com", wait_until="networkidle")

    # Link 추출
    links = await page.eval_on_selector_all(
        'a[href]',
        'elements => elements.map(e => e.href)'
    )
```

---

#### Alembic

**용도**: 데이터베이스 마이그레이션 관리

**주요 명령어**:
```bash
# 마이그레이션 생성
uv run alembic revision --autogenerate -m "add scope to targets"

# 마이그레이션 적용
uv run alembic upgrade head

# 롤백
uv run alembic downgrade -1

# 히스토리 확인
uv run alembic history
```

**현재 마이그레이션**: 8개 (Project → Target → Task → Asset)

---

#### Pytest

**특징**:
- 픽스처(Fixture) 시스템
- 비동기 테스트 지원 (pytest-asyncio)
- 커버리지 측정 (pytest-cov)
- Mock 지원

**테스트 구조**:
```
tests/
├── conftest.py              # 공통 Fixtures
├── api/                     # API 테스트
├── services/                # 서비스 레이어 테스트
└── integration/             # 통합 테스트
```

**상세 정보**: [../development/TESTING.md](../development/TESTING.md)

---

## Frontend

### 핵심 기술

| 기술 | 버전 | 용도 |
|------|------|------|
| **React** | 19.2.0 | UI 라이브러리 |
| **TypeScript** | 5.9.3 | 정적 타입 언어 |
| **Vite** | 7.2.4 | 빌드 도구 (빠른 HMR) |
| **shadcn/ui** | - | 복사-붙여넣기 UI 컴포넌트 (Radix UI 기반) |
| **TailwindCSS** | 4.1.18 | 유틸리티 우선 CSS 프레임워크 |
| **TanStack Query** | 5.90.16 | 서버 상태 관리 (캐싱, 폴링) |
| **React Router** | 7.11.0 | 클라이언트 라우팅 |
| **React Hook Form** | 7.69.0 | 폼 상태 관리 |
| **Zod** | 4.2.1 | 스키마 유효성 검증 |
| **Axios** | 1.13.2 | HTTP 클라이언트 |
| **Lucide React** | 0.562.0 | 아이콘 라이브러리 |
| **Vitest** | 4.0.16 | 테스트 러너 (TDD) |
| **Storybook** | 10.1.10 | 컴포넌트 개발 환경 |

### 주요 라이브러리 설명

#### React 19

**선택 이유**:
- 최신 Concurrent Features
- Suspense for Data Fetching
- Server Components 준비
- 향상된 성능

**주요 Hook 사용**:
```typescript
import { useState, useEffect, useMemo } from 'react';

function ProjectList() {
  const [filter, setFilter] = useState('active');
  const projects = useProjects({ archived: filter === 'archived' });

  return (
    <div>
      {projects.data?.map(project => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
```

---

#### TypeScript Strict Mode

**설정** (tsconfig.json):
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true
  }
}
```

**타입 안전성**:
```typescript
// ✅ Good
function getProject(id: number): Promise<Project> {
  return projectService.getProject(id);
}

// ❌ Bad
function getProject(id) {
  return projectService.getProject(id);
}
```

---

#### Vite

**특징**:
- ES Modules 기반 빠른 HMR
- Rollup 기반 프로덕션 빌드
- TypeScript 내장 지원
- 플러그인 생태계

**설정** (vite.config.ts):
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
});
```

---

#### shadcn/ui

**개념**: 복사-붙여넣기 컴포넌트 라이브러리

**특징**:
- Radix UI 기반 (접근성 보장)
- Tailwind CSS 스타일링
- 코드 소유권 (npm 패키지 없음)
- 완전한 커스터마이징

**컴포넌트 추가**:
```bash
npx shadcn@latest add button
npx shadcn@latest add dialog
npx shadcn@latest add form
```

**현재 설치된 컴포넌트**: 93개

**상세 정보**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md#frontend-디렉토리-구조)

---

#### TailwindCSS v4

**특징**:
- 유틸리티 우선 CSS
- JIT (Just-In-Time) 컴파일
- 작은 번들 크기
- CSS Variables 기반

**설정** (index.css):
```css
@import "tailwindcss";

@theme {
  --color-primary: #3b82f6;
  --color-secondary: #10b981;
}
```

**사용 예시**:
```tsx
<div className="flex items-center justify-between p-4 bg-primary text-white rounded-lg">
  <h1 className="text-2xl font-bold">EAZY</h1>
</div>
```

---

#### TanStack Query

**용도**: 서버 상태 관리 (React Query v5)

**특징**:
- 자동 캐싱
- 백그라운드 동기화
- Optimistic Updates
- 폴링 (Polling)

**사용 예시**:
```typescript
// hooks/useProjects.ts
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

**폴링 예시** (Task 상태 추적):
```typescript
const { data: task } = useQuery({
  queryKey: taskKeys.detail(taskId),
  queryFn: () => taskService.getTaskStatus(taskId),
  refetchInterval: (query) => {
    const data = query.state.data;
    if (!data) return 5000;
    if (data.status === 'COMPLETED' || data.status === 'FAILED') {
      return false; // 폴링 중지
    }
    return 5000; // 5초 간격
  }
});
```

---

#### React Hook Form + Zod

**통합**: 폼 상태 관리 + 유효성 검증

**사용 예시**:
```typescript
// schemas/projectSchema.ts
import { z } from 'zod';

export const projectFormSchema = z.object({
  name: z.string().min(1, "프로젝트 이름은 필수입니다").max(255),
  description: z.string().optional()
});

export type ProjectFormValues = z.infer<typeof projectFormSchema>;

// components/CreateProjectForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

function CreateProjectForm() {
  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectFormSchema),
    defaultValues: { name: '', description: '' }
  });

  const onSubmit = async (data: ProjectFormValues) => {
    await createProject.mutateAsync(data);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField name="name" control={form.control} />
        <FormField name="description" control={form.control} />
        <Button type="submit">생성</Button>
      </form>
    </Form>
  );
}
```

---

#### Vitest

**특징**:
- Vite 기반 테스트 러너
- Jest 호환 API
- 빠른 실행 속도
- UI 모드 지원

**설정** (vitest.config.ts):
```typescript
export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './vitest.setup.ts'
  }
});
```

**테스트 통계**:
- 총 테스트 파일: 16개
- 총 테스트 케이스: 168개
- 통과율: 100%

**상세 정보**: [../development/TESTING.md](../development/TESTING.md)

---

#### Storybook

**용도**: 컴포넌트 개발 환경

**특징**:
- 독립적인 컴포넌트 개발
- 다양한 상태 시각화
- 인터랙티브 문서
- 시각적 회귀 테스트

**현재 Stories**: 47개

**실행**:
```bash
npm run storybook
# → http://localhost:6006
```

---

## 인프라

### Docker Compose

**용도**: PostgreSQL + Redis 컨테이너 관리

**파일 경로**: `backend/docker/docker-compose.yml`

**서비스 구성**:
```yaml
services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: eazy_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

**실행**:
```bash
cd backend/docker
docker compose up -d

# 확인
docker ps
# → eazy-postgres (5432)
# → eazy-redis (6379)

# 로그 확인
docker compose logs -f postgres
docker compose logs -f redis

# 중지
docker compose down

# 볼륨 삭제 (데이터 초기화)
docker compose down -v
```

---

### UV (고속 패키지 매니저)

**용도**: Backend Python 패키지 관리

**특징**:
- Rust 기반으로 **10-100배 빠른 설치 속도**
- pyproject.toml 기반 의존성 관리
- 자동 가상환경 생성 및 관리
- Lock 파일을 통한 재현 가능한 빌드

**설치**:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Homebrew (macOS)
brew install uv
```

**주요 명령어**:
```bash
# 의존성 설치
uv sync

# 패키지 추가
uv add <package-name>
uv add --dev <dev-package>

# 패키지 제거
uv remove <package-name>

# Python 실행 (venv 내에서)
uv run python script.py

# 서버 실행
uv run uvicorn app.main:app --reload

# 테스트 실행
uv run pytest

# Lock 파일 생성 (자동)
uv lock
```

**상세 정보**: [UV 패키지 매니저](#uv-패키지-매니저)

---

### npm (Frontend 패키지 매니저)

**용도**: Frontend 패키지 관리

**주요 명령어**:
```bash
# 의존성 설치
npm install

# 개발 서버
npm run dev

# 테스트
npm run test

# 빌드
npm run build

# Storybook
npm run storybook
```

---

## UV 패키지 매니저

### 개념

**UV (Rust 기반 고속 Python 패키지 매니저)**는 pip, poetry, pipenv를 대체하는 차세대 도구입니다.

### 특징

#### 1. 극도로 빠른 속도

**벤치마크**:
```
의존성 100개 설치 시간:
- pip: 60초
- poetry: 45초
- UV: 2초 (30배 빠름)
```

Rust로 작성되어 병렬 다운로드 및 설치를 수행합니다.

---

#### 2. pyproject.toml 기반 관리

**파일 구조**:
```toml
[project]
name = "eazy-backend"
version = "0.1.0"
requires-python = ">=3.12"

dependencies = [
    "fastapi>=0.115.0",
    "sqlmodel>=0.0.22",
    "playwright>=1.42.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.1.0",
    "pytest-asyncio>=0.23.0",
    "black>=24.3.0",
]
```

---

#### 3. 자동 가상환경 관리

UV는 프로젝트별로 `.venv` 디렉토리를 자동 생성합니다.

```bash
# 가상환경 생성 (자동)
uv sync

# venv 경로 확인
uv venv --path
# → /Users/lrtk/Documents/Project/EAZY/backend/.venv

# venv 활성화 (선택 사항)
source .venv/bin/activate
```

---

#### 4. Lock 파일을 통한 재현 가능한 빌드

**uv.lock** 파일이 자동 생성되어 정확한 버전을 기록합니다.

```toml
[[package]]
name = "fastapi"
version = "0.115.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    "pydantic>=1.6.2",
    "starlette>=0.27.0",
]
```

이를 통해 팀원 간 동일한 환경을 보장합니다.

---

### 주요 명령어

#### 의존성 설치

```bash
# pyproject.toml 기반 설치
uv sync

# 특정 패키지 추가
uv add httpx

# 개발 의존성 추가
uv add --dev pytest

# 특정 버전 설치
uv add "fastapi>=0.115.0"
```

---

#### 패키지 제거

```bash
uv remove httpx
```

---

#### Python 실행

```bash
# venv 내에서 Python 실행
uv run python script.py

# 서버 실행
uv run uvicorn app.main:app --reload

# Worker 실행
uv run python -m app.worker

# 테스트
uv run pytest

# mypy 타입 체크
uv run mypy .
```

---

#### 패키지 정보 확인

```bash
# 설치된 패키지 목록
uv pip list

# 패키지 의존성 트리
uv pip show fastapi
```

---

### 마이그레이션 가이드 (pip → UV)

**기존 pip 워크플로우**:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python script.py
```

**UV 워크플로우**:
```bash
uv sync
uv run python script.py
```

**requirements.txt → pyproject.toml 변환**:
```bash
# requirements.txt 파일을 pyproject.toml로 변환
uv pip compile requirements.txt -o pyproject.toml
```

---

### 프로젝트에서의 UV 사용

#### 필수 규칙

**EAZY 프로젝트에서는 UV 사용이 필수입니다.**

1. ❌ `pip install` 사용 금지 → ✅ `uv add <package>`
2. ❌ `python script.py` 실행 금지 → ✅ `uv run python script.py`
3. ❌ `pytest` 직접 실행 금지 → ✅ `uv run pytest`

#### 이유

- 일관된 개발 환경 보장
- 빠른 의존성 설치
- Lock 파일을 통한 재현 가능한 빌드

---

### 참고 자료

- 공식 문서: https://github.com/astral-sh/uv
- 벤치마크: https://github.com/astral-sh/uv#performance
- 마이그레이션 가이드: https://docs.astral.sh/uv/guides/migrate-from-pip/

---

**다음 문서**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

[← 메인 문서로 돌아가기](../README.md)
