# **개발 컨벤션 및 기술 스택 규칙 (Tech Stack & Conventions)**

본 문서는 프로젝트의 일관성을 유지하고 기술 부채를 최소화하기 위한 **공통 규약**입니다.
모든 기여자는 리뷰 요청(PR) 전 본 문서를 확인하여 준수 여부를 자가 점검해야 합니다.

## 1. Backend Rules

### **Tech Stack**
*   **Language**: Python 3.12+
*   **Framework**: FastAPI
*   **ORM**: SQLAlchemy (Async support preferred where applicable, currently Sync sessions used)
*   **Linter/Formatter**: Ruff (Preferred) or Black/Isort
*   **Package Manager**: `uv` (Recommended) or `pip`

### **Architecture: Layered Pattern**
엄격한 계층 분리를 원칙으로 합니다.
1.  **API Layer (`app/api/`)**: `APIRouter` 정의, Request/Response DTO(Pydantic) 변환 담당. **비즈니스 로직 금지.**
2.  **Service Layer (`app/services/`)**: 핵심 비즈니스 로직 구현. Transaction 관리. **Direct DB Query 금지 (Repository 위임).**
3.  **Repository Layer (`app/repositories/`)**: DB CRUD 전담. SQLAlchemy `Session` 사용.
4.  **Models (`app/models/`)**: Pure SQLAlchemy ORM Classes.

### **Coding Standards**
*   **Type Hinting**: 모든 함수 인자와 반환값에 Type Hint 명시 (e.g., `def func(a: int) -> str:`)
*   **Variable Naming**: `snake_case` 사용.
*   **DTO**: `pydantic.BaseModel`을 상속받아 `app/schemas/`에 정의. Request/Response 모델 분리 권장 (`UserCreate`, `UserResponse`).
*   **Async**: I/O Bound 작업(DB, Network)은 `async/await` 사용 권장.

## 2. Frontend Rules

### **Tech Stack**
*   **Framework**: React 18+ (Vite)
*   **Language**: TypeScript
*   **Styling**: Tailwind CSS (Shadcn/UI components preferred)
*   **State Management**: Zustand (Global Store), React Query (Server State recommended)
*   **Routing**: React Router DOM

### **Architecture: Component Design**
*   **Container/Presenter Pattern**: 로직(Data Fetching, State)과 뷰(Render) 분리 지향.
*   **Directory Structure**:
    *   `components/ui/`: Shadcn 등 재사용 가능한 UI 아톰.
    *   `components/[feature]/`: 특정 도메인(예: proxy, target)에 종속된 컴포넌트.
    *   `pages/`: 라우트 단위 페이지.
    *   `store/`: Zustand 스토어 정의.

### **Coding Standards**
*   **Naming**:
    *   Components/Files: `PascalCase.tsx`
    *   Functions/Variables: `camelCase`
*   **Type Safety**: `any` 사용 금지. Interface/Type 명시.
*   **Hooks**: 커스텀 훅은 `use` 접두사 사용. 비즈니스 로직은 훅으로 분리.

## 3. Common Rules

### **Git Convention**
*   **Commit Message**: `[Type] Description` 형식 (e.g., `[Feat] Add proxy packet implementation`)
    *   Types: `Feat`, `Fix`, `Refactor`, `Docs`, `Chore`, `Test`
*   **Branch Strategy**: `feature/[ticket-id]-description`

### **Documentation**
*   API 변경 시 `docs/specs/api_spec.md` (혹은 Swagger) 최신화.
*   DB 변경 시 `docs/specs/db_schema.md` 즉시 반영.
