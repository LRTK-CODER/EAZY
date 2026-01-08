# 용어집

[← 메인 문서로 돌아가기](../README.md)

---

## 목차

1. [보안 및 테스팅](#보안-및-테스팅)
2. [개발 방법론](#개발-방법론)
3. [아키텍처 패턴](#아키텍처-패턴)
4. [데이터베이스](#데이터베이스)
5. [기술 스택](#기술-스택)
6. [프로젝트 특화 용어](#프로젝트-특화-용어)

---

## 보안 및 테스팅

### DAST (Dynamic Application Security Testing)

**정의**: 동적 애플리케이션 보안 테스팅

**설명**: 실행 중인 애플리케이션을 외부에서 테스트하여 취약점을 발견하는 블랙박스 테스팅 기법

**특징**:
- 소스 코드 접근 불필요
- 실제 운영 환경과 유사한 조건에서 테스트
- 런타임 취약점 탐지 (SQL Injection, XSS 등)

**EAZY에서의 활용**:
- Playwright 기반 크롤링으로 공격 표면 식별
- LLM 기반 비즈니스 로직 취약점 분석

**관련 문서**: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md#목표)

---

### Business Logic Vulnerability

**정의**: 비즈니스 로직 취약점

**설명**: 애플리케이션의 설계나 구현 논리상의 허점으로 인해 발생하는 보안 취약점. 기술적 취약점과 달리 애플리케이션의 비즈니스 프로세스를 이해해야 발견 가능

**예시**:
- **인증 우회 (Authentication Bypass)**: 로그인 없이 인증된 페이지 접근
- **권한 상승 (Privilege Escalation)**: 일반 사용자가 관리자 권한 획득
- **비즈니스 프로세스 악용**: 쿠폰 중복 사용, 무한 포인트 적립
- **불충분한 검증**: 결제 금액 조작, 수량 음수 입력

**기존 DAST 도구의 한계**:
- 패턴 기반 탐지로는 발견 불가능
- 비즈니스 컨텍스트 이해 부족

**EAZY의 차별점**:
- LLM이 비즈니스 로직 흐름 분석
- 연쇄 공격 시나리오 자동 생성

**관련 문서**: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md#핵심-차별점)

---

### Attack Surface

**정의**: 공격 표면

**설명**: 공격자가 애플리케이션에 접근하거나 데이터를 주고받을 수 있는 모든 진입점

**구성 요소**:
- **URL**: 웹 페이지 경로
- **Form**: HTML 폼 (POST 요청)
- **API Endpoint**: REST/GraphQL API
- **XHR/Fetch**: 비동기 HTTP 요청
- **WebSocket**: 실시간 통신

**EAZY에서의 관리**:
- `assets` 테이블에 저장
- content_hash 기반 중복 제거
- Active/Passive 스캔으로 수집

**관련 문서**: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md#2-공격-표면-식별-attack-surface-discovery)

---

## 개발 방법론

### TDD (Test-Driven Development)

**정의**: 테스트 주도 개발

**설명**: 테스트 코드를 먼저 작성하고, 테스트를 통과하는 최소한의 코드를 구현한 후, 리팩토링하는 개발 방법론

**프로세스**:
```
1. RED: 실패하는 테스트 작성
   ↓
2. GREEN: 테스트를 통과하는 최소 코드 작성
   ↓
3. REFACTOR: 코드 개선 (테스트는 여전히 통과)
```

**장점**:
- 높은 테스트 커버리지
- 리팩토링 안정성
- 명확한 요구사항 정의

**EAZY에서의 적용**:
- Frontend: 168개 테스트 모두 TDD로 작성
- Backend: 11개 테스트 파일, 모두 TDD 적용

**예시**:
```typescript
// RED: 테스트 작성 (CreateProjectForm.test.tsx)
it('should create project successfully', async () => {
  const user = userEvent.setup();
  render(<CreateProjectForm />);

  await user.type(screen.getByLabelText(/name/i), 'New Project');
  await user.click(screen.getByRole('button', { name: /create/i }));

  await waitFor(() => {
    expect(mockCreateProject).toHaveBeenCalled();
  });
});

// GREEN: 최소 구현 (CreateProjectForm.tsx)
export function CreateProjectForm() {
  const form = useForm();
  const createProject = useCreateProject();

  const onSubmit = async (data) => {
    await createProject.mutateAsync(data);
  };

  return <Form {...form} onSubmit={onSubmit} />;
}

// REFACTOR: 코드 개선 (에러 핸들링, UI 개선 등)
```

**관련 문서**: [../development/TESTING.md](../development/TESTING.md)

---

### Atomic Design

**정의**: 원자 단위 설계 방법론

**설명**: UI 컴포넌트를 원자(Atoms), 분자(Molecules), 유기체(Organisms), 템플릿(Templates), 페이지(Pages) 5단계로 계층화하여 설계하는 방법론

**계층 구조**:
```
Atoms (원자)
  ↓ 조합
Molecules (분자)
  ↓ 조합
Organisms (유기체)
  ↓ 배치
Templates (템플릿)
  ↓ 데이터 주입
Pages (페이지)
```

**예시**:
- **Atoms**: Button, Input, Label
- **Molecules**: FormField (Label + Input + ErrorMessage)
- **Organisms**: CreateProjectForm (여러 FormField 조합)
- **Templates**: MainLayout (Header + Sidebar + Content)
- **Pages**: ProjectDetailPage (MainLayout + 데이터)

**EAZY에서의 적용**:
```
components/ui/          → Atoms (shadcn/ui, 93개)
components/features/    → Molecules & Organisms (14개)
components/layout/      → Templates (3개)
pages/                  → Pages (5개)
```

**장점**:
- 컴포넌트 재사용성 증가
- 일관된 디자인 시스템
- 유지보수 용이

**관련 문서**: [ARCHITECTURE.md](ARCHITECTURE.md#frontend-atomic-design-architecture)

---

## 아키텍처 패턴

### Soft Delete

**정의**: 논리 삭제 패턴

**설명**: 데이터를 물리적으로 삭제하지 않고, 삭제 플래그를 설정하여 논리적으로만 삭제하는 패턴

**구현 방법**:
```sql
-- is_archived 플래그 사용
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    is_archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP
);

-- Archive (Soft Delete)
UPDATE projects SET is_archived = true, archived_at = NOW() WHERE id = 1;

-- Restore
UPDATE projects SET is_archived = false, archived_at = null WHERE id = 1;

-- Hard Delete (물리적 삭제)
DELETE FROM projects WHERE id = 1;
```

**장점**:
- 데이터 복구 가능
- 감사 추적 (Audit Trail)
- 삭제 이력 보존

**EAZY에서의 적용**:
- Project 모델에 `is_archived`, `archived_at` 필드
- Archive/Restore API 제공
- 일괄 복원 기능

**관련 문서**: [db_schema.md](db_schema.md#projects-프로젝트)

---

### Dual View

**정의**: 이중 뷰 패턴

**설명**: 동일한 데이터를 두 가지 관점(Total, History)으로 제공하는 패턴

**EAZY에서의 적용**:
- **Total View**: `assets` 테이블 (유니크한 공격 표면의 최신 상태)
- **History View**: `asset_discoveries` 테이블 (각 스캔 작업별 발견 이력)

**구현**:
```sql
-- Total View (최신 상태)
SELECT * FROM assets WHERE target_id = 1;

-- History View (특정 스캔의 발견 이력)
SELECT a.*
FROM assets a
JOIN asset_discoveries ad ON a.id = ad.asset_id
WHERE ad.task_id = 123;
```

**장점**:
- 최신 상태와 이력을 동시에 관리
- 중복 제거 (Total View)
- 감사 추적 (History View)

**관련 문서**: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md#비기능-요구사항-non-functional-requirements)

---

### Layered Architecture

**정의**: 계층형 아키텍처

**설명**: 애플리케이션을 여러 계층(Layer)으로 분리하여, 각 계층이 명확한 책임을 가지도록 설계하는 패턴

**EAZY Backend 계층**:
```
API Layer        → HTTP 요청/응답 처리
Service Layer    → 비즈니스 로직
Repository Layer → 데이터 접근
Infrastructure   → DB, Redis, 설정
```

**규칙**:
- 상위 계층은 하위 계층만 의존
- 하위 계층은 상위 계층을 알지 못함
- 계층 간 인터페이스 명확히 정의

**관련 문서**: [ARCHITECTURE.md](ARCHITECTURE.md#backend-layered-architecture)

---

## 데이터베이스

### ACID

**정의**: 트랜잭션의 4가지 속성

**구성 요소**:
- **A (Atomicity)**: 원자성 - 트랜잭션의 모든 작업이 성공하거나 모두 실패
- **C (Consistency)**: 일관성 - 트랜잭션 전후로 데이터베이스가 일관된 상태 유지
- **I (Isolation)**: 격리성 - 동시 실행 트랜잭션이 서로 영향을 주지 않음
- **D (Durability)**: 지속성 - 커밋된 트랜잭션은 영구적으로 저장

**EAZY에서의 활용**:
- PostgreSQL ACID 트랜잭션 사용
- SQLModel AsyncSession으로 트랜잭션 관리

---

### JSONB

**정의**: PostgreSQL의 바이너리 JSON 타입

**설명**: JSON 데이터를 바이너리 형식으로 저장하여, 효율적인 저장과 빠른 쿼리를 지원하는 데이터 타입

**JSON vs JSONB**:
| 특징 | JSON | JSONB |
|-----|------|-------|
| 저장 형식 | 텍스트 | 바이너리 |
| 저장 속도 | 빠름 | 느림 (변환 필요) |
| 쿼리 속도 | 느림 | 빠름 (인덱싱 지원) |
| 공백 유지 | O | X |

**EAZY에서의 사용**:
```sql
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    request_spec JSONB,   -- HTTP 요청 (Headers, Body, Cookies)
    response_spec JSONB,  -- HTTP 응답 (Headers, Body, Status)
    parameters JSONB      -- 파라미터 분석 (Name, Type, Location)
);

-- JSONB 쿼리 예시
SELECT * FROM assets WHERE request_spec->>'method' = 'POST';

-- GIN 인덱스 (JSONB 검색 최적화)
CREATE INDEX idx_asset_params ON assets USING GIN (parameters);
```

**관련 문서**: [db_schema.md](db_schema.md#assets-공격-표면)

---

### ORM (Object-Relational Mapping)

**정의**: 객체-관계 매핑

**설명**: 객체 지향 프로그래밍 언어와 관계형 데이터베이스 간의 데이터를 변환하는 기술

**EAZY에서의 사용**:
- SQLModel (Pydantic + SQLAlchemy)
- Type Hint 기반 모델 정의
- 비동기 쿼리 지원

**예시**:
```python
# ORM 모델 정의
class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)

# ORM 쿼리
result = await db.execute(select(Project).where(Project.id == 1))
project = result.scalar_one_or_none()

# SQL 직접 작성 불필요 (ORM이 자동 생성)
```

**관련 문서**: [TECH_STACK.md](TECH_STACK.md#sqlmodel)

---

## 기술 스택

### UV

**정의**: Rust 기반 고속 Python 패키지 매니저

**설명**: pip, poetry, pipenv를 대체하는 차세대 패키지 관리 도구

**특징**:
- **10-100배 빠른 설치 속도** (Rust 병렬 처리)
- pyproject.toml 기반 의존성 관리
- 자동 가상환경 생성 및 관리
- Lock 파일을 통한 재현 가능한 빌드

**명령어 비교**:
```bash
# pip (기존)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python script.py

# UV (EAZY)
uv sync
uv run python script.py
```

**EAZY 프로젝트 규칙**:
- ❌ `pip install` 사용 금지
- ✅ `uv add <package>` 사용
- ❌ `python script.py` 금지
- ✅ `uv run python script.py` 사용

**관련 문서**: [TECH_STACK.md](TECH_STACK.md#uv-패키지-매니저)

---

### shadcn/ui

**정의**: 복사-붙여넣기 UI 컴포넌트 라이브러리

**설명**: Radix UI 기반의 접근성 보장 컴포넌트를 Tailwind CSS로 스타일링하여 제공. npm 패키지가 아닌 소스 코드를 직접 복사하여 사용

**특징**:
- **코드 소유권**: npm 의존성 없음, 코드를 직접 소유
- **완전한 커스터마이징**: 모든 코드 수정 가능
- **접근성 보장**: Radix UI 기반 (WCAG 2.1 준수)
- **Tailwind CSS**: 유틸리티 클래스 스타일링

**설치 방법**:
```bash
npx shadcn@latest add button
npx shadcn@latest add dialog
npx shadcn@latest add form
```

**EAZY에서의 사용**:
- 93개 컴포넌트 설치
- components/ui/ 디렉토리에 저장
- 커스터마이징하여 사용

**관련 문서**: [TECH_STACK.md](TECH_STACK.md#shadcnui)

---

### TanStack Query

**정의**: 서버 상태 관리 라이브러리 (구 React Query)

**설명**: React 애플리케이션에서 서버 데이터를 페칭, 캐싱, 동기화하는 라이브러리

**주요 기능**:
- 자동 캐싱
- 백그라운드 동기화
- Optimistic Updates
- 폴링 (Polling)
- 무한 스크롤

**EAZY에서의 사용**:
```typescript
// 데이터 페칭
const { data } = useQuery({
  queryKey: ['projects'],
  queryFn: () => projectService.getProjects()
});

// 데이터 변경
const createProject = useMutation({
  mutationFn: projectService.createProject,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['projects'] });
  }
});
```

**관련 문서**: [TECH_STACK.md](TECH_STACK.md#tanstack-query)

---

## 프로젝트 특화 용어

### Asset

**정의**: 공격 표면 자산

**설명**: 웹 애플리케이션의 모든 진입점 (URL, Form, API Endpoint 등)을 데이터베이스에 저장한 레코드

**구성 요소**:
- `type`: URL, FORM, XHR
- `source`: HTML, JS, NETWORK, DOM
- `method`: GET, POST, PUT, DELETE
- `url`: 전체 URL
- `path`: URL 경로
- `request_spec`: 요청 패킷 (JSONB)
- `response_spec`: 응답 패킷 (JSONB)
- `parameters`: 파라미터 분석 (JSONB)
- `content_hash`: 중복 제거 키 (SHA256)

**관련 테이블**:
- `assets`: Total View (유니크한 자산)
- `asset_discoveries`: History View (스캔 이력)

**관련 문서**: [db_schema.md](db_schema.md#assets-공격-표면)

---

### Scope

**정의**: 스캔 범위 설정

**설명**: Target의 크롤링 범위를 제한하는 옵션

**옵션**:
- **DOMAIN**: 전체 도메인 스캔 (subdomain 포함)
  - 예: `example.com`, `www.example.com`, `api.example.com` 모두 포함
- **SUBDOMAIN**: 특정 서브도메인만
  - 예: `www.example.com`만 스캔
- **URL_ONLY**: 단일 URL만
  - 예: `https://example.com/login` 페이지만

**데이터베이스**:
```sql
CREATE TABLE targets (
    id SERIAL PRIMARY KEY,
    url VARCHAR(2048),
    scope VARCHAR(20)  -- ENUM: DOMAIN/SUBDOMAIN/URL_ONLY
);
```

**관련 문서**: [db_schema.md](db_schema.md#targets-스캔-대상)

---

### Task

**정의**: 비동기 작업

**설명**: 크롤링, 분석 등 시간이 오래 걸리는 작업을 비동기로 처리하기 위한 작업 단위

**상태 전이**:
```
PENDING → RUNNING → COMPLETED
                 → FAILED
```

**타입**:
- **CRAWL**: Active Scan (Playwright 크롤링)
- **SCAN**: Passive Scan (Mitmproxy 감청)

**result 필드** (JSON):
```json
{
  "found_links": 15,
  "saved_assets": 12,
  "duration_ms": 3500,
  "error": null
}
```

**관련 문서**: [db_schema.md](db_schema.md#tasks-비동기-작업)

---

### content_hash

**정의**: 자산 중복 제거 키

**설명**: Asset의 고유성을 판단하기 위한 SHA256 해시 값

**생성 로직**:
```python
content = f"{method}:{url}"
content_hash = hashlib.sha256(content.encode()).hexdigest()
```

**예시**:
```python
# 동일한 자산 (중복)
content_hash("GET:https://example.com/login")
# → "abc123..."

content_hash("GET:https://example.com/login")
# → "abc123..." (동일)

# 다른 자산 (신규)
content_hash("POST:https://example.com/login")
# → "def456..." (다름)
```

**데이터베이스**:
```sql
CREATE TABLE assets (
    content_hash VARCHAR(64) UNIQUE NOT NULL
);

CREATE UNIQUE INDEX idx_asset_content_hash ON assets(content_hash);
```

**관련 문서**: [db_schema.md](db_schema.md#assets-공격-표면)

---

### Polling

**정의**: 폴링 (주기적 조회)

**설명**: 클라이언트가 서버에 주기적으로 요청을 보내 상태 변화를 감지하는 기법

**EAZY에서의 사용**:
- Task 상태 추적 (PENDING → RUNNING → COMPLETED)
- 5초 간격으로 폴링
- COMPLETED/FAILED 시 자동 중지

**구현**:
```typescript
const { data: task } = useQuery({
  queryKey: ['tasks', taskId],
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

**관련 문서**: [ARCHITECTURE.md](ARCHITECTURE.md#frontend-tanstack-query-polling)

---

## 참고 자료

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- PostgreSQL JSONB: https://www.postgresql.org/docs/current/datatype-json.html
- TDD by Example: https://www.oreilly.com/library/view/test-driven-development/0321146530/
- Atomic Design: https://atomicdesign.bradfrost.com/
- UV Documentation: https://github.com/astral-sh/uv
- shadcn/ui: https://ui.shadcn.com/
- TanStack Query: https://tanstack.com/query/latest

---

**다음 문서**: [RESOURCES.md](RESOURCES.md)

[← 메인 문서로 돌아가기](../README.md)
