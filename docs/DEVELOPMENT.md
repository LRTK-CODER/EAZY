# EAZY 개발 가이드

[← 메인 문서로 돌아가기](./README.md)

**최종 업데이트**: 2026-01-11

---

## 목차

1. [개발 환경 설정](#개발-환경-설정)
2. [TDD 필수 규칙](#tdd-필수-규칙)
3. [Backend 개발](#backend-개발)
4. [Frontend 개발](#frontend-개발)
5. [테스트 전략](#테스트-전략)
6. [Git 워크플로우](#git-워크플로우)
7. [배포](#배포)

---

## 개발 환경 설정

### Prerequisites

| 도구 | 버전 | 설치 |
|------|------|------|
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) |
| Python | 3.12+ | `brew install python@3.12` |
| UV | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker | latest | [docker.com](https://docker.com/) |

### 빠른 시작

```bash
# 1. 인프라 시작 (PostgreSQL + Redis)
cd backend/docker && docker compose up -d

# 2. Backend 설정
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload  # :8000

# 3. Frontend 설정 (새 터미널)
cd frontend
npm install
npm run dev  # :5173

# 4. Worker 시작 (새 터미널)
cd backend
uv run python -m app.worker
```

---

## TDD 필수 규칙

EAZY 프로젝트는 **TDD (Test-Driven Development)** 를 필수로 준수합니다.

### RED → GREEN → REFACTOR

```
1. RED     → 실패하는 테스트 작성
2. GREEN   → 테스트 통과하는 최소 코드
3. REFACTOR → 코드 개선 (테스트 유지)
```

### Commit 메시지 예시

```bash
# RED Phase
test(api): add project archive tests (TDD RED)

# GREEN Phase
feat(api): implement project archive (TDD GREEN)

# REFACTOR Phase
refactor(api): extract common validation logic (TDD REFACTOR)
```

### 체크리스트

- [ ] 코드 작성 전 테스트 먼저 작성
- [ ] 테스트 실패 확인 후 구현 시작
- [ ] 모든 테스트 통과 확인
- [ ] 커밋 메시지에 TDD Phase 명시

---

## Backend 개발

### Layered Architecture

```
API Layer     → HTTP 처리, 라우팅 (비즈니스 로직 금지)
Service Layer → 비즈니스 로직, 트랜잭션
Repository    → SQLModel ORM, DB CRUD
Infrastructure → DB/Redis 연결, 환경 설정
```

### API 엔드포인트 작성

```python
# app/api/v1/endpoints/project.py
@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    # Service Layer에 위임 (비즈니스 로직 여기 금지)
    return await ProjectService.create_project(db, project)
```

### Service 작성

```python
# app/services/project_service.py
class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
        project = Project(**data.model_dump())
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def archive_project(db: AsyncSession, project_id: int) -> None:
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Not found")
        project.is_archived = True
        project.archived_at = datetime.now(timezone.utc)
        await db.commit()
```

### 주요 명령어

```bash
# 서버 실행
uv run uvicorn app.main:app --reload

# 테스트
uv run pytest -v
uv run pytest -v -k "test_create"  # 특정 테스트

# 마이그레이션
uv run alembic revision --autogenerate -m "add field"
uv run alembic upgrade head

# 타입 체크
uv run mypy .

# 포맷팅
uv run black . && uv run isort .
```

---

## Frontend 개발

### Atomic Design + Presentation/Container

```
Pages      → 라우팅 페이지 (ProjectsPage, DashboardPage)
Features   → 도메인 컴포넌트 (CreateProjectForm, TargetList)
UI         → shadcn/ui 기본 컴포넌트 (Button, Dialog)
Hooks      → TanStack Query 래퍼 (useProjects, useTargets)
Services   → API 클라이언트 (projectService, targetService)
```

### TanStack Query 훅

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

### React Hook Form + Zod

```typescript
// schemas/projectSchema.ts
export const projectFormSchema = z.object({
  name: z.string().min(1, "필수 입력").max(255),
  description: z.string().optional()
});

// 컴포넌트
const form = useForm<ProjectFormValues>({
  resolver: zodResolver(projectFormSchema),
  defaultValues: { name: '', description: '' }
});
```

### 주요 명령어

```bash
# 개발 서버
npm run dev

# 테스트
npm run test              # 전체
npm run test -- --watch   # 감시 모드

# 빌드
npm run build

# Storybook
npm run storybook         # :6006

# 린트/포맷
npm run lint && npm run format

# shadcn/ui 컴포넌트 추가
npx shadcn@latest add button dialog form
```

---

## 테스트 전략

### Backend (Pytest)

```python
# tests/conftest.py
@pytest_asyncio.fixture
async def db_session():
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

```python
# tests/api/test_projects.py
async def test_create_project(client):
    response = await client.post("/api/v1/projects/", json={
        "name": "Test", "description": "Desc"
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Test"
```

### Frontend (Vitest + RTL)

```typescript
// 컴포넌트 테스트
describe('CreateProjectForm', () => {
  it('should create project', async () => {
    const user = userEvent.setup();
    render(<CreateProjectForm />);

    await user.click(screen.getByRole('button', { name: /create/i }));
    await user.type(screen.getByLabelText(/name/i), 'Test');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalled();
    });
  });
});
```

```typescript
// API 서비스 테스트 (MSW)
describe('projectService', () => {
  it('should get projects', async () => {
    server.use(
      http.get('*/projects/', () => HttpResponse.json([{ id: 1 }]))
    );
    const result = await projectService.getProjects();
    expect(result).toHaveLength(1);
  });
});
```

### 현재 통계

| 영역 | 테스트 파일 | 테스트 수 | 통과율 |
|------|------------|----------|--------|
| Backend | 11개 | 30+ | 100% |
| Frontend | 16개 | 168개 | 100% |

---

## Git 워크플로우

### 브랜치 전략 (Trunk-based / GitHub Flow)

```
main (항상 배포 가능)
  ├── feat/asset-discovery
  ├── fix/validation-error
  ├── docs/api-guide
  └── refactor/service-layer
```

### 브랜치 네이밍

| 접두사 | 용도 | 예시 |
|--------|------|------|
| `feat/` | 새 기능 | `feat/scan-trigger` |
| `fix/` | 버그 수정 | `fix/cors-error` |
| `docs/` | 문서 | `docs/api-spec` |
| `refactor/` | 리팩토링 | `refactor/crawler` |
| `test/` | 테스트 | `test/project-crud` |

### Conventional Commits

```bash
# 형식
<type>(<scope>): <subject>

# 예시
feat(frontend): add CreateProjectForm
fix(backend): resolve CORS preflight issue
docs(api): update endpoint documentation
test(api): add project CRUD tests (TDD RED)
```

| Type | 설명 |
|------|------|
| feat | 새 기능 |
| fix | 버그 수정 |
| docs | 문서 |
| refactor | 리팩토링 |
| test | 테스트 |
| chore | 빌드/패키지 |

### PR 체크리스트

- [ ] 모든 테스트 통과
- [ ] Lint/Format 실행
- [ ] Conventional Commits 준수
- [ ] TDD Phase 명시

### Merge 전략

**Squash and Merge** 권장 - main 히스토리 깔끔하게 유지

---

## 배포

### Docker Compose (개발)

```yaml
# backend/docker/docker-compose.yml
services:
  postgres:
    image: postgres:15-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: eazy_db

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

```bash
docker compose up -d
docker compose down -v  # 데이터 초기화
```

### 환경 변수

```bash
# backend/.env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=eazy_db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:5173
```

### 포트 구성

| 서비스 | 포트 |
|--------|------|
| Frontend | 5173 |
| Backend API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| Storybook | 6006 |

### API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 참고 자료

- [QUICK_START.md](./QUICK_START.md) - 5분 설정 가이드
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 시스템 아키텍처
- [API_SPEC.md](./reference/api_spec.md) - REST API 명세
- [DB_SCHEMA.md](./reference/db_schema.md) - 데이터베이스 설계
- [CODING_CONVENTION.md](./reference/coding_convention.md) - 코딩 규약

---

[← 메인 문서로 돌아가기](./README.md)
