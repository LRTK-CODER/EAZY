# Coding Convention

## 1. 개요
*   본 문서는 EAZY 프로젝트의 코드 품질 유지 및 일관성을 위한 규칙을 정의합니다.
*   모든 기여자는 이 문서를 숙지하고 준수해야 합니다.

## 2. Backend (Python/FastAPI)

### 2.1. 기술 스택 및 도구
*   **Language**: Python 3.12+
*   **Framework**: FastAPI
*   **Linter**: `ruff`
*   **Formatter**: `black`
*   **Import Sorter**: `isort`
*   **Type Checker**: `mypy` (Strict Mode)

### 2.2. 스타일 가이드
*   **PEP 8**을 기본으로 합니다.
*   들여쓰기는 **4 Spaces**를 사용합니다.
*   최대 라인 길이는 **88자** (Black Default)를 따릅니다.
*   모든 함수와 메서드에는 **Type Hint**를 필수로 작성합니다.

```python
# Good
def get_user(user_id: int) -> User | None:
    ...

# Bad
def get_user(user_id):
    ...
```

### 2.3. 아키텍처 규칙
*   **Layered Architecture**를 준수합니다.
    *   `api/`: Router 및 Controller 역할. 비즈니스 로직 포함 금지.
    *   `services/`: 비즈니스 로직. DB 접근은 Repository(혹은 Crud Utils)를 통해서만 수행 권장.
    *   `models/`: SQLModel (DB Schema + Pydantic Model) 정의.
    *   `core/`: 설정, 인증, 유틸리티 등 공통 모듈.
*   **Pydantic**: 데이터 유효성 검증 모델을 적극 활용합니다.

## 3. Frontend (React/Vite)

### 3.1. 기술 스택
*   **Language**: TypeScript 5.0+
*   **Framework**: React 18+ (Vite)
*   **Styling**: TailwindCSS, shadcn/ui
*   **State Management**: Zustand
*   **Data Fetching**: TanStack Query (React Query)

### 3.2. 스타일 가이드
*   **Prettier**를 사용해 코드를 포맷팅합니다.
*   **ESLint** 규칙을 준수합니다.
*   들여쓰기는 **2 Spaces**를 사용합니다.
*   컴포넌트 파일명은 **PascalCase** (e.g., `MyComponent.tsx`)를 사용합니다.
*   일반 TS/JS 파일명은 **camelCase** (e.g., `utils.ts`)를 사용합니다.

### 3.3. 컴포넌트 구조 (Atomic / shadcn)
*   `components/ui/`: shadcn/ui 등 재사용 가능한 기본 UI 컴포넌트.
*   `components/`: 비즈니스 로직이 포함된 복합 컴포넌트.
*   `pages/`: 라우팅되는 페이지 컴포넌트.
*   **Presentation & Container Pattern**:
    *   가능한 경우 로직(Hook)과 뷰(JSX)를 분리합니다.

## 4. Git Convention

### 4.1. Branch Strategy
*   **Trunk-based Development** 혹은 **GitHub Flow**를 지향합니다.
*   `main`: 배포 가능한 안정 상태.
*   `feat/*`: 기능 개발 브랜치.

### 4.2. Commit Strategy
*   **Conventional Commits**을 따릅니다.
*   `type: subject` 형식을 사용합니다.
    *   `feat`: 새로운 기능 추가
    *   `fix`: 버그 수정
    *   `docs`: 문서 수정
    *   `style`: 코드 포맷팅, 세미콜론 누락 등 (코드 변경 없음)
    *   `refactor`: 코드 리팩토링
    *   `test`: 테스트 코드 추가
    *   `chore`: 빌드 업무 수정, 패키지 매니저 수정 등

```bash
feat: 사용자 로그인 API 구현
fix: 크롤러 중복 URL 수집 오류 수정
docs: API 명세서 업데이트
```

## 5. Security Convention
*   **Secret Key Management**: `.env` 파일에 저장하고 절대 Git에 올리지 않습니다.
*   **SQL Injection**: 반드시 ORM(SQLModel)이나 Parameterized Query를 사용합니다.
*   **Input Validation**: 백엔드에서는 Pydantic, 프론트엔드에서는 Zod를 사용하여 입력을 검증합니다.
