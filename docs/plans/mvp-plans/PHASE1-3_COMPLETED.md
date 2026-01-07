# Phase 1-3: 초기화 & 레이아웃 & 프로젝트 CRUD (완료)

[◀ 메인 인덱스로 돌아가기](./INDEX.md)

---

**전체 상태**: ✅ 완료
**완료일**: 2025-12-29 ~ 2026-01-04
**총 소요 시간**: 10시간
**테스트**: 168/168 통과 ✅

---

## Phase 1: 프로젝트 초기화 & 인프라
**목표**: React+Vite 프로젝트를 기본 도구 및 구조와 함께 설정.
**예상 시간**: 2시간
**상태**: ✅ 완료

### 작업
**🔴 RED: 실패하는 테스트 먼저 작성**
- [x] **Test 1.1**: App 렌더링 테스트
    - 파일: `frontend/src/App.test.tsx` (생성 예정)
    - 내용: App 컴포넌트가 "EAZY"를 렌더링하는지 확인.

**🟢 GREEN: 테스트를 통과하도록 구현**
- [x] **Task 1.2**: Vite 프로젝트 초기화
    - 명령어: `npm create vite@latest frontend -- --template react-ts`
    - TailwindCSS 설정.
    - 폴더 구조 설정 (`src/components`, `src/pages`, `src/lib`, `src/hooks`).
- [x] **Task 1.3**: 테스트 러너 구성 (Vitest)
    - `vitest`, `jsdom`, `@testing-library/react` 설치.
    - `vitest.setup.ts` 생성.
- [x] **Task 1.4**: 기본 의존성 설치
    - `react-router-dom`, `clsx`, `tailwind-merge`.

### 품질 게이트 ✋
- [x] `npm run dev`로 서버가 시작됨.
- [x] `npm run test`가 통과함 (App 렌더링).

---

## Phase 2: 레이아웃 & 디자인 시스템 기반
**목표**: 기본 레이아웃 (Sidebar, Header) 구현 및 핵심 shadcn 컴포넌트 설치.
**예상 시간**: 3시간
**상태**: ✅ 완료

### 작업
**🔴 RED: 실패하는 테스트 먼저 작성**
- [x] **Test 2.1**: Sidebar 네비게이션 테스트
    - "Dashboard", "Projects" 링크가 존재하는지 확인.
- [x] **Test 2.2**: Layout Wrapper 테스트
    - children이 레이아웃 내에 렌더링되는지 확인.

**🟢 GREEN: 테스트를 통과하도록 구현**
- [x] **Task 2.3**: Shadcn/UI CLI 설치 & 초기화
    - `components.json` 구성.
- [x] **Task 2.4**: 기본 컴포넌트 추가
    - `button`, `card`, `input`, `table` (shadcn을 통해).
    - `components/ui/...`
- [x] **Task 2.5**: 레이아웃 컴포넌트 생성
    - `components/layout/Sidebar.tsx`
    - `components/layout/Header.tsx`
    - `components/layout/MainLayout.tsx`
- [x] **Task 2.6**: 라우팅 설정
    - `App.tsx`에 `ReactRouter` 설정.

**🔵 REFACTOR: 코드 품질 개선**
- [x] **Task 2.7**: Sidebar 컴포넌트 리팩토링
    - NavItems를 config로 추출.
    - 재렌더링 최적화.

### 품질 게이트 ✋
- [x] 모든 UI 컴포넌트가 컴파일됨.
- [x] 레이아웃 테스트가 통과함.

---

## Phase 3: 프로젝트 CRUD (사이드바)
**목표**: 사이드바에서 프로젝트 생성/조회/수정/삭제 기능 구현.
**예상 시간**: 5시간
**상태**: ✅ 완료

### 작업
**🔴 RED: 실패하는 테스트 먼저 작성**
- [x] **Test 3.1**: API Client 테스트
    - `lib/api.ts`의 HTTP 메서드 테스트 (get, post, put, del).
    - 인터셉터 동작 테스트 (인증 토큰, 에러 처리).
    - **완료**: 2026-01-01 (Commit: 194fabc)
    - 테스트 결과: ❌ FAIL (예상대로 - RED Phase, lib/api.ts 파일 미존재)
- [x] **Test 3.2**: Project Service 테스트
    - `getProjects`, `getProject`, `createProject`, `updateProject`, `deleteProject`, `deleteProjects` 테스트.
    - Mock API 응답 검증.
    - **완료**: 2026-01-01 (Commit: 908c956)
    - 테스트 결과: ❌ FAIL (예상대로 - RED Phase, services/projectService.ts 파일 미존재)
- [x] **Test 3.3**: CreateProjectForm 테스트
    - 입력 필드 (이름, 설명) 및 제출 버튼 확인.
    - 폼 제출 시 API 호출 트리거 확인.
    - 유효성 검사 (이름 필수, 최대 255자).
    - 폼 상호작용 (제출 중 버튼 비활성화, 취소 버튼).
    - **완료**: 2026-01-01 (Commit: e1d17d5)
    - 테스트 결과: ❌ FAIL (예상대로 - RED Phase, CreateProjectForm.tsx 파일 미존재)
- [x] **Test 3.4**: EditProjectForm 테스트
    - 기존 프로젝트 데이터로 폼 초기화 확인.
    - 수정 시 API 호출 확인.
    - 폼 검증 (이름 필수, 최대 255자).
    - 폼 상호작용 (업데이트 중 버튼 비활성화, 취소 버튼).
    - **완료**: 2026-01-01 (Commit: 3717a8b)
    - 테스트 결과: ❌ FAIL (예상대로 - RED Phase, EditProjectForm.tsx 파일 미존재)
- [x] **Test 3.5**: Sidebar 프로젝트 목록 테스트
    - API에서 프로젝트 목록을 가져와 렌더링하는지 확인.
    - 로딩, 에러, 빈 상태 처리 확인.
    - 프로젝트 선택 및 Select All 기능.
    - Header 액션 (Plus, Trash 버튼).
    - 라우트 기반 렌더링 (/projects, /dashboard, /settings).
    - **완료**: 2026-01-01 (Commit: d768a09)
    - 테스트 결과: ❌ FAIL (예상대로 - RED Phase, services/projectService.ts 파일 미존재)
- [x] **Test 3.6**: 프로젝트 삭제 테스트
    - 개별 삭제 버튼 클릭 시 확인 다이얼로그 표시.
    - 일괄 삭제 버튼 클릭 시 선택된 프로젝트들 삭제.
    - 삭제 후 목록 갱신 확인.
    - Dialog 렌더링 및 상호작용 (Cancel, 버튼 비활성화).
    - 영구 삭제 경고 메시지.
    - **완료**: 2026-01-01 (Commit: 15d73f1)
    - 테스트 결과: ❌ FAIL (예상대로 - RED Phase, DeleteProjectDialog.tsx 파일 미존재)

**🟢 GREEN: 테스트를 통과하도록 구현**
- [x] **Task 3.7**: API Client 설정
    - `lib/api.ts` (Axios 인스턴스).
    - 인터셉터 (인증 로직 주석 처리 - MVP는 로그인 불필요).
    - HTTP 메서드: `get`, `post`, `put`, `patch`, `del`.
    - **완료**: 2026-01-01 (Commit: 96e2c00)
    - 테스트 결과: ✅ PASS (5/5 tests passed)
    - 참고: 인증 관련 테스트 제거 (14개 → 5개)
- [x] **Task 3.8**: 타입 정의
    - `types/project.ts`: `Project`, `ProjectCreate`, `ProjectUpdate`, `ProjectListParams` 인터페이스.
    - 모든 테스트 파일에서 타입 관련 `@ts-expect-error` 제거.
    - **완료**: 2026-01-01 (Commit: 9ba9767)
    - 테스트 결과: ✅ 타입 정의 완료, TypeScript 컴파일 성공
- [x] **Task 3.9**: Project Service
    - `services/projectService.ts`:
      - `getProjects(params?)`: 프로젝트 목록 조회 (페이지네이션 지원)
      - `getProject(id)`: 단일 프로젝트 조회
      - `createProject(data)`: 프로젝트 생성
      - `updateProject(id, data)`: 프로젝트 수정
      - `deleteProject(id)`: 프로젝트 삭제
      - `deleteProjects(ids)`: 프로젝트 일괄 삭제 (Promise.all 사용)
    - **완료**: 2026-01-01 (Commit: e2a9386)
    - 테스트 결과: ✅ PASS (17/17 tests passed)
    - 참고: 쿼리 스트링 빌더 구현 (skip, limit 파라미터)
- [x] **Task 3.10**: TanStack Query 훅
    - `hooks/useProjects.ts`:
      - `projectKeys`: Query Key Factory 패턴 (일관된 캐시 키 관리)
      - `useProjects(params?)`: 프로젝트 목록 조회 (useQuery, 페이지네이션 지원)
      - `useProject(id)`: 단일 프로젝트 조회 (useQuery, enabled 옵션)
      - `useCreateProject()`: 프로젝트 생성 (useMutation, lists 무효화)
      - `useUpdateProject()`: 프로젝트 수정 (useMutation, detail + lists 무효화)
      - `useDeleteProject()`: 프로젝트 삭제 (useMutation, 전체 무효화)
      - `useDeleteProjects()`: 프로젝트 일괄 삭제 (useMutation, 전체 무효화)
    - **완료**: 2026-01-01 (Commit: 6e5d9b2)
    - 테스트 결과: ✅ Dev 서버 컴파일 성공, 컴포넌트 테스트에서 간접 검증 예정
    - 참고: 자동 캐시 무효화 및 리페치 구현
- [x] **Task 3.11**: CreateProjectForm 컴포넌트
    - `components/features/project/CreateProjectForm.tsx`
    - React Hook Form + Zod 검증.
    - Dialog 형식.
    - **완료**: 2026-01-01 (Commit: f9df5f7)
    - 테스트 결과: ✅ PASS (16/16 tests passed)
    - 참고: Name 필드 (필수, max 255자), Description 필드 (선택), Toast 알림, 자동 폼 초기화
- [x] **Task 3.12**: EditProjectForm 컴포넌트
    - `components/features/project/EditProjectForm.tsx`
    - CreateProjectForm과 유사하지만 기존 데이터로 초기화.
    - Dialog 형식.
    - **완료**: 2026-01-01 (Commit: ae50900)
    - 테스트 결과: ✅ PASS (20/20 tests passed)
    - 참고: useEffect로 project 변경 감지 및 폼 초기화, null description 처리, useUpdateProject 훅 사용
- [x] **Task 3.13**: DeleteProjectDialog 컴포넌트
    - `components/features/project/DeleteProjectDialog.tsx`
    - 확인 다이얼로그 (AlertDialog).
    - 단일 삭제 및 일괄 삭제 지원.
    - **완료**: 2026-01-01 (Commit: 8cced6b)
    - 테스트 결과: ✅ PASS (18/18 tests passed)
    - 참고: useState로 loading state 관리, projectService 직접 호출, 단일/일괄 자동 판별
- [x] **Task 3.14**: Sidebar 프로젝트 목록 통합
    - `components/layout/Sidebar.tsx` 수정:
      - `dummyProjects` 제거.
      - `useProjects()` 훅 사용하여 실제 API 데이터 표시.
      - Plus 버튼 → CreateProjectForm 다이얼로그 열기.
      - Edit 드롭다운 메뉴 → EditProjectForm 다이얼로그 열기.
      - Delete 드롭다운 메뉴 → DeleteProjectDialog 열기 (개별).
      - Trash2 버튼 → DeleteProjectDialog 열기 (일괄).
      - 로딩, 에러, 빈 상태 처리.
    - **완료**: 2026-01-02 (Commits: 53be71b, 18903f8)
    - 테스트 결과: ✅ 브라우저 검증 완료 - 모든 CRUD 기능 정상 작동
    - 추가 구현:
      - Backend: Archive 패턴 구현 (soft delete)
      - is_archived 필드 추가, Alembic migration
      - PATCH /projects/{id} 엔드포인트 추가
      - DELETE /projects/{id}?permanent=true 엔드포인트 추가
      - 백엔드 테스트 7/7 통과
      - Frontend: React Query 통합 및 버그 수정
      - AxiosInstance import 타입 수정
      - QueryClientProvider 추가
      - React Hook order 에러 수정 (enabled 파라미터)
      - DeleteProjectDialog mutation hooks 사용으로 캐시 자동 무효화
- [x] **Task 3.15**: Main.tsx QueryClient 설정
    - `main.tsx`에 QueryClientProvider 추가 (아직 없다면).
    - **완료**: 2026-01-02 (Task 3.14와 함께 완료)

**🔵 REFACTOR: 코드 품질 개선**
- [x] **Task 3.16**: 컴포넌트 추상화
    - API 로직과 UI 로직 명확히 분리 (`hooks/useProjects`와 컴포넌트).
    - 공통 폼 로직 추출: `ProjectFormFields.tsx` 컴포넌트 생성.
    - Zod 스키마 재사용: `schemas/projectSchema.ts` (Create와 Update 공용).
    - ESLint/TypeScript 설정 개선 및 테스트 파일 정리.
    - **완료**: 2026-01-02

### 품질 게이트 ✋
- [x] 백엔드에서 프로젝트 목록을 조회할 수 있음.
- [x] 새 프로젝트를 생성할 수 있음.
- [x] 프로젝트를 수정할 수 있음.
- [x] 프로젝트를 개별 삭제할 수 있음 (Archive).
- [x] 프로젝트를 일괄 삭제할 수 있음 (Archive).
- [x] 모든 테스트가 모킹된 API로 통과함 (168/168 tests).
- [x] `npm run build`가 성공함.
- [x] `npm run lint`가 에러 없이 통과함.

**완료**: 2026-01-02 - Phase 3 프로젝트 CRUD 완료 ✅

---

## 📊 Phase 1-3 요약

| Phase | 소요 시간 | 테스트 | 주요 성과 |
|-------|----------|--------|-----------|
| Phase 1 | 2h | - | Vite + TypeScript + Vitest 환경 구축 |
| Phase 2 | 3h | - | Shadcn/UI + 레이아웃 시스템 |
| Phase 3 | 5h | 168/168 ✅ | 프로젝트 CRUD + TanStack Query 통합 |
| **총합** | **10h** | **168/168 ✅** | **MVP 기반 완성** |

---

## 🎓 주요 학습 내용

### 1. TDD 프로세스
- RED → GREEN → REFACTOR 사이클 준수
- 테스트 먼저 작성 → 실패 확인 → 구현 → 통과 → 리팩토링

### 2. TanStack Query 패턴
- Query Key Factory (`projectKeys`)
- 자동 캐시 무효화 (`invalidateQueries`)
- Optimistic Update 가능성

### 3. Shadcn/UI 활용
- 복사-붙여넣기 컴포넌트로 빠른 UI 구축
- Radix UI 기반 접근성 확보

### 4. Backend Archive 패턴
- Soft Delete (`is_archived` 필드)
- 영구 삭제 옵션 (`?permanent=true`)

---

## 🔗 네비게이션

- [◀ 메인 인덱스](./INDEX.md)
- [▶ Phase 4 - 프로젝트 상세 페이지](./PHASE4_COMPLETED.md)
- [📝 학습 내용 & 이력](./NOTES.md)
