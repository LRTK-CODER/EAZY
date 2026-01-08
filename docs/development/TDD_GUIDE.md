# TDD 가이드 (Test-Driven Development)

[← 메인 문서로 돌아가기](../README.md)

**작성일**: 2026-01-09
**대상 독자**: 모든 개발자 (Backend, Frontend)

---

## 목차

- [TDD란?](#tdd란)
- [왜 TDD를 엄격히 준수하는가?](#왜-tdd를-엄격히-준수하는가)
- [RED → GREEN → REFACTOR 사이클](#red--green--refactor-사이클)
- [Backend TDD 예제](#backend-tdd-예제)
- [Frontend TDD 예제](#frontend-tdd-예제)
- [프로젝트 증거](#프로젝트-증거)
- [TDD 체크리스트](#tdd-체크리스트)

---

## TDD란?

**Test-Driven Development (테스트 주도 개발)**은 테스트 코드를 먼저 작성하고, 그 테스트를 통과하는 최소한의 코드를 작성한 후, 코드를 개선하는 개발 방법론입니다.

### 핵심 원칙

```
RED → GREEN → REFACTOR
```

1. **RED**: 실패하는 테스트 작성
2. **GREEN**: 테스트를 통과하는 최소 코드 작성
3. **REFACTOR**: 코드 개선 (테스트는 여전히 통과)

---

## 왜 TDD를 엄격히 준수하는가?

### 1. 코드 품질 향상

- **버그 조기 발견**: 테스트를 먼저 작성하면 요구사항을 명확히 이해할 수 있습니다.
- **리팩토링 안전성**: 테스트가 있으면 코드 변경 시 기존 기능이 깨지지 않음을 보장합니다.

### 2. 설계 개선

- **느슨한 결합**: 테스트 가능한 코드는 자연스럽게 의존성이 낮아집니다.
- **명확한 인터페이스**: 테스트를 먼저 작성하면 API 설계가 명확해집니다.

### 3. 문서화 효과

- 테스트 코드는 **살아있는 문서**입니다.
- 새로운 팀원이 테스트를 보고 기능을 이해할 수 있습니다.

### 4. EAZY 프로젝트 규칙

EAZY 프로젝트에서는 **모든 새로운 기능은 TDD로 개발**합니다.

- Backend: Pytest 기반 TDD
- Frontend: Vitest + React Testing Library 기반 TDD

---

## RED → GREEN → REFACTOR 사이클

### Phase 1: RED (실패하는 테스트 작성)

**목표**: 구현하려는 기능의 테스트를 먼저 작성합니다.

```python
# tests/api/test_projects.py

async def test_create_project(client):
    """프로젝트 생성 테스트 (RED Phase)"""
    response = await client.post("/api/v1/projects/", json={
        "name": "Test Project",
        "description": "Test Description"
    })

    # 아직 구현되지 않았으므로 이 테스트는 실패합니다.
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["is_archived"] is False
```

**실행 결과**:
```bash
$ uv run pytest tests/api/test_projects.py::test_create_project
FAILED tests/api/test_projects.py::test_create_project - 404 Not Found
```

### Phase 2: GREEN (최소 코드로 테스트 통과)

**목표**: 테스트를 통과하는 **최소한의 코드**만 작성합니다.

```python
# app/api/v1/endpoints/project.py

@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """프로젝트 생성 (GREEN Phase - 최소 구현)"""
    # Service Layer 위임
    return await ProjectService.create_project(db, project)


# app/services/project_service.py

class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
        """프로젝트 생성 로직"""
        project = Project(
            name=data.name,
            description=data.description,
            is_archived=False
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
```

**실행 결과**:
```bash
$ uv run pytest tests/api/test_projects.py::test_create_project
PASSED tests/api/test_projects.py::test_create_project
```

### Phase 3: REFACTOR (코드 개선)

**목표**: 중복 제거, 성능 개선, 가독성 향상 (테스트는 여전히 통과)

```python
# app/services/project_service.py (Refactored)

class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
        """프로젝트 생성 로직 (Refactored)"""
        # 더 명확한 변수명
        new_project = Project(**data.model_dump())

        # 트랜잭션 관리 개선
        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)

        return new_project
```

**실행 결과**:
```bash
$ uv run pytest tests/api/test_projects.py::test_create_project
PASSED tests/api/test_projects.py::test_create_project
```

---

## Backend TDD 예제

### 예제: Project Archive 기능

#### Step 1: RED (테스트 작성)

```python
# tests/api/test_projects.py

async def test_archive_project(client, db_session):
    """프로젝트 Archive 테스트 (RED Phase)"""
    # Given: 프로젝트 생성
    project = await ProjectService.create_project(
        db_session,
        ProjectCreate(name="Test Project", description="Test")
    )

    # When: Archive 요청
    response = await client.delete(f"/api/v1/projects/{project.id}")

    # Then: 204 No Content 반환
    assert response.status_code == 204

    # DB 확인: is_archived=True, archived_at 설정됨
    await db_session.refresh(project)
    assert project.is_archived is True
    assert project.archived_at is not None
```

#### Step 2: GREEN (최소 구현)

```python
# app/api/v1/endpoints/project.py

@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    permanent: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """프로젝트 삭제 (Archive or Hard Delete)"""
    if permanent:
        await ProjectService.permanent_delete(db, project_id)
    else:
        await ProjectService.archive_project(db, project_id)


# app/services/project_service.py

class ProjectService:
    @staticmethod
    async def archive_project(db: AsyncSession, project_id: int) -> None:
        """프로젝트 Archive (Soft Delete)"""
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project.is_archived = True
        project.archived_at = datetime.now(timezone.utc)
        await db.commit()
```

#### Step 3: REFACTOR (개선)

```python
# app/services/project_service.py (Refactored)

class ProjectService:
    @staticmethod
    async def archive_project(db: AsyncSession, project_id: int) -> None:
        """프로젝트 Archive (Soft Delete) - Refactored"""
        # 프로젝트 조회 로직 재사용
        project = await ProjectService.get_project(db, project_id)

        # Archive 상태 설정
        project.is_archived = True
        project.archived_at = datetime.now(timezone.utc)

        await db.commit()

    @staticmethod
    async def get_project(db: AsyncSession, project_id: int) -> Project:
        """프로젝트 조회 (재사용 가능한 헬퍼 메서드)"""
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
```

---

## Frontend TDD 예제

### 예제: CreateProjectForm 컴포넌트

#### Step 1: RED (테스트 작성)

```typescript
// src/components/features/project/CreateProjectForm.test.tsx

describe('CreateProjectForm - TDD RED Phase', () => {
  it('should create project successfully', async () => {
    const user = userEvent.setup();
    render(<CreateProjectForm />);

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
      expect(mockCreateProject).toHaveBeenCalledWith({
        name: 'New Project',
        description: 'Test Description'
      });
    });
  });
});
```

**실행 결과**:
```bash
$ npm run test CreateProjectForm.test.tsx
FAIL CreateProjectForm - Component not found
```

#### Step 2: GREEN (최소 구현)

```typescript
// src/components/features/project/CreateProjectForm.tsx

export function CreateProjectForm() {
  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectFormSchema),
    defaultValues: {
      name: '',
      description: ''
    }
  });

  const createProject = useCreateProject();

  const onSubmit = async (data: ProjectFormValues) => {
    await createProject.mutateAsync(data);
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Create Project</Button>
      </DialogTrigger>
      <DialogContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <FormField
              name="name"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                </FormItem>
              )}
            />
            <FormField
              name="description"
              control={form.control}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea {...field} />
                  </FormControl>
                </FormItem>
              )}
            />
            <Button type="submit">Create</Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

**실행 결과**:
```bash
$ npm run test CreateProjectForm.test.tsx
PASS CreateProjectForm - 1 test passed
```

#### Step 3: REFACTOR (개선)

```typescript
// src/components/features/project/CreateProjectForm.tsx (Refactored)

export function CreateProjectForm() {
  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectFormSchema),
    defaultValues: { name: '', description: '' }
  });

  const createProject = useCreateProject();
  const [open, setOpen] = useState(false);

  const onSubmit = async (data: ProjectFormValues) => {
    await createProject.mutateAsync(data);
    setOpen(false); // Dialog 닫기 추가
    form.reset(); // 폼 리셋 추가
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Create Project</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* ProjectFormFields로 분리 (재사용성 향상) */}
            <ProjectFormFields form={form} />
            <Button type="submit" disabled={createProject.isPending}>
              {createProject.isPending ? 'Creating...' : 'Create'}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

---

## 프로젝트 증거

EAZY 프로젝트는 **TDD를 엄격히 준수**하여 높은 테스트 커버리지를 달성했습니다.

### Backend

- 테스트 파일: **11개**
- 테스트 통과: **모든 테스트 통과**
- 커버리지: **≥80%** (주요 기능 100%)

```bash
$ uv run pytest -v
tests/api/test_projects.py::test_create_project PASSED
tests/api/test_projects.py::test_archive_project PASSED
tests/api/test_targets.py::test_create_target PASSED
... (총 30+ 테스트)
```

### Frontend

- 테스트 파일: **16개**
- 테스트 수: **168개**
- 테스트 통과: **168/168 (100%)**
- 커버리지: **≥80%**

```bash
$ npm run test
✓ src/components/features/project/CreateProjectForm.test.tsx (12 tests)
✓ src/components/features/project/EditProjectForm.test.tsx (10 tests)
✓ src/services/projectService.test.ts (17 tests)
... (총 168개 테스트)

Test Files  16 passed (16)
     Tests  168 passed (168)
```

### 증거: Git Commit 이력

```bash
$ git log --oneline --grep="TDD"
64c2fd6 feat(frontend): implement ProjectDetailPage Target integration (TDD GREEN)
f67bd35 test(frontend): add ProjectDetailPage extension tests (TDD RED)
ea9dc53 test(frontend): add comprehensive TargetList tests (TDD RED)
36955f9 test(frontend): add Target form validation tests (TDD GREEN)
```

---

## TDD 체크리스트

### 작업 시작 전

- [ ] 요구사항을 명확히 이해했는가?
- [ ] 테스트 케이스를 머릿속으로 구상했는가?

### RED Phase

- [ ] 실패하는 테스트를 먼저 작성했는가?
- [ ] 테스트가 실제로 실패하는지 확인했는가?
- [ ] 테스트가 명확하고 이해하기 쉬운가?

### GREEN Phase

- [ ] 테스트를 통과하는 **최소한의 코드**만 작성했는가?
- [ ] 모든 테스트가 통과하는가?
- [ ] 빠른 피드백을 받았는가?

### REFACTOR Phase

- [ ] 중복 코드를 제거했는가?
- [ ] 변수명, 함수명이 명확한가?
- [ ] 리팩토링 후에도 모든 테스트가 통과하는가?
- [ ] 성능 개선 여지가 있는가?

### 커밋 전

- [ ] 모든 테스트가 통과하는가?
- [ ] Conventional Commits 규칙을 따랐는가? (예: `feat:`, `test:`)
- [ ] 커밋 메시지에 TDD Phase를 명시했는가? (예: `(TDD RED)`, `(TDD GREEN)`)

---

## 참고 자료

- [Testing Strategy (TESTING_STRATEGY.md)](./TESTING_STRATEGY.md) - 상세한 테스트 전략
- [Backend Development Guide (BACKEND_DEVELOPMENT.md)](./BACKEND_DEVELOPMENT.md) - Backend TDD 예제
- [Frontend Development Guide (FRONTEND_DEVELOPMENT.md)](./FRONTEND_DEVELOPMENT.md) - Frontend TDD 예제
- Kent Beck, "Test-Driven Development: By Example"
- Martin Fowler, "Refactoring: Improving the Design of Existing Code"

---

**다음 문서**: [Testing Strategy (TESTING_STRATEGY.md)](./TESTING_STRATEGY.md)
