# 구현 계획: MVP 프론트엔드

**상태**: 🔄 Phase 3 진행 중
**시작일**: 2025-12-28
**최근 업데이트**: 2026-01-01
**예상 완료일**: 2026-01-03

---

**⚠️ 중요 지침**: 각 Phase 완료 후 반드시:
1. ✅ 완료된 작업 체크박스를 체크
2. 🧪 모든 품질 게이트 검증 명령어 실행
3. ⚠️ 모든 품질 게이트 항목이 통과했는지 확인
4. 📅 위의 "최근 업데이트" 날짜 갱신
5. 📝 Notes 섹션에 학습 내용 문서화
6. ➡️ 그 후에만 다음 Phase로 진행

⛔ **품질 게이트를 건너뛰거나 실패한 체크를 무시하고 진행하지 말 것**

---

## 📋 개요

### 기능 설명
**React** (Vite), **TypeScript**, **TailwindCSS**, **shadcn/ui**를 사용하여 EAZY MVP 프론트엔드를 구축합니다.
프론트엔드는 프로젝트와 Target을 관리하고 스캔 결과를 확인할 수 있는 대시보드를 제공합니다.

### 성공 기준
- [ ] Vite & TypeScript로 프로젝트가 성공적으로 초기화됨.
- [ ] Shadcn/UI 컴포넌트가 구성되고 작동함.
- [ ] 사용자가 UI를 통해 프로젝트와 Target을 생성/조회/수정/삭제할 수 있음.
- [ ] 사용자가 스캔을 트리거하고 결과(Assets)를 확인할 수 있음.
- [ ] **TDD**: Vitest & React Testing Library를 사용하여 컴포넌트 테스트 구현.

### 사용자 영향
- DAST 도구를 위한 그래픽 인터페이스를 제공하여 Raw API 호출을 대체.
- 공격 표면 데이터를 시각화하여 분석을 용이하게 함.

---

## 🏗️ 아키텍처 결정

| 결정 사항 | 근거 | 트레이드오프 |
|----------|------|------------|
| **Vite** | 빠른 빌드 시간, 최신 생태계. | - |
| **shadcn/ui** | 복사-붙여넣기 컴포넌트, 높은 커스터마이징, 접근성. | npm 패키지가 아니므로 수동 컴포넌트 관리 필요. |
| **Zustand** | 간단한 전역 상태 관리 (필요시). | Redux보다 보일러플레이트 적음. |
| **TanStack Query** | 서버 상태 관리 (API 캐시, 로딩 상태). | 단순한 앱에는 복잡도 증가하지만, 데이터 중심 대시보드에는 필수. |
| **Atomic Layout** | `components/ui` (atoms), `components/features` (molecules/organisms), `pages` (templates). | 재사용성과 작은 컴포넌트 크기 촉진. |

---

## 📦 의존성

### 시작 전 필수 요구사항
- 백엔드 API 실행 중 (통합을 위해)

### 외부 의존성
- `react`, `react-dom`, `react-router-dom`
- `axios` (또는 `ky` / `fetch`)
- `@tanstack/react-query`
- `tailwindcss`, `postcss`, `autoprefixer`
- `lucide-react` (아이콘)
- `clsx`, `tailwind-merge` (유틸)
- `zod`, `react-hook-form` (폼)
- **Dev**: `vitest`, `@testing-library/react`, `jsdom`

---

## 🧪 테스트 전략

### 테스트 접근 방식
**TDD (테스트 주도 개발)**:
1. **RED**: 실패하는 테스트를 먼저 작성 (예: "프로젝트 목록 렌더링").
2. **GREEN**: 테스트를 통과하는 컴포넌트 구현.
3. **REFACTOR**: 코드 구조 및 스타일 개선.

### 이 기능의 테스트 피라미드
| 테스트 유형 | 커버리지 목표 | 목적 |
|-----------|--------------|------|
| **Unit/Component** | ≥80% | UI 컴포넌트, 훅, 유틸 |
| **Integration** | 주요 흐름 | 페이지 수준 상호작용 (모킹된 API) |

---

## 🚀 구현 단계

### Phase 1: 프로젝트 초기화 & 인프라
**목표**: React+Vite 프로젝트를 기본 도구 및 구조와 함께 설정.
**예상 시간**: 2시간
**상태**: ✅ 완료

#### 작업
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

#### 품질 게이트 ✋
- [x] `npm run dev`로 서버가 시작됨.
- [x] `npm run test`가 통과함 (App 렌더링).

---

### Phase 2: 레이아웃 & 디자인 시스템 기반
**목표**: 기본 레이아웃 (Sidebar, Header) 구현 및 핵심 shadcn 컴포넌트 설치.
**예상 시간**: 3시간
**상태**: ✅ 완료

#### 작업
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

#### 품질 게이트 ✋
- [x] 모든 UI 컴포넌트가 컴파일됨.
- [x] 레이아웃 테스트가 통과함.

---

### Phase 3: 프로젝트 CRUD (사이드바)
**목표**: 사이드바에서 프로젝트 생성/조회/수정/삭제 기능 구현.
**예상 시간**: 5시간
**상태**: 🔄 진행 중

#### 작업
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
- [ ] **Task 3.13**: DeleteProjectDialog 컴포넌트
    - `components/features/project/DeleteProjectDialog.tsx`
    - 확인 다이얼로그 (AlertDialog).
    - 단일 삭제 및 일괄 삭제 지원.
- [ ] **Task 3.14**: Sidebar 프로젝트 목록 통합
    - `components/layout/Sidebar.tsx` 수정:
      - `dummyProjects` 제거.
      - `useProjects()` 훅 사용하여 실제 API 데이터 표시.
      - Plus 버튼 → CreateProjectForm 다이얼로그 열기.
      - Edit 드롭다운 메뉴 → EditProjectForm 다이얼로그 열기.
      - Delete 드롭다운 메뉴 → DeleteProjectDialog 열기 (개별).
      - Trash2 버튼 → DeleteProjectDialog 열기 (일괄).
      - 로딩, 에러, 빈 상태 처리.
- [ ] **Task 3.15**: Main.tsx QueryClient 설정
    - `main.tsx`에 QueryClientProvider 추가 (아직 없다면).

**🔵 REFACTOR: 코드 품질 개선**
- [ ] **Task 3.16**: 컴포넌트 추상화
    - API 로직과 UI 로직 명확히 분리 (`hooks/useProjects`와 컴포넌트).
    - 공통 폼 로직 추출 (필요시).
    - Zod 스키마 재사용 (Create와 Update 간).

#### 품질 게이트 ✋
- [ ] 백엔드에서 프로젝트 목록을 조회할 수 있음.
- [ ] 새 프로젝트를 생성할 수 있음.
- [ ] 프로젝트를 수정할 수 있음.
- [ ] 프로젝트를 개별 삭제할 수 있음.
- [ ] 프로젝트를 일괄 삭제할 수 있음.
- [ ] 모든 테스트가 모킹된 API로 통과함.
- [ ] `npm run build`가 성공함.
- [ ] `npm run lint`가 에러 없이 통과함.

---

### Phase 4: 프로젝트 상세 페이지 & Target 관리
**목표**: 선택된 프로젝트의 상세 정보 표시 및 Target CRUD 구현.
**예상 시간**: 5시간
**상태**: ⏳ 대기 중

#### 작업
**🔴 RED: 실패하는 테스트 먼저 작성**
- [ ] **Test 4.1**: ProjectDetailPage 테스트
    - URL 파라미터에서 projectId를 추출하는지 확인.
    - 프로젝트 데이터를 조회하여 h1 태그에 프로젝트명 표시 확인.
    - 로딩, 에러 상태 처리 확인.
- [ ] **Test 4.2**: Target List 테스트
    - `GET /projects/{id}/targets` API를 모킹하여 Target 목록 렌더링 확인.
    - 로딩, 에러, 빈 상태 처리 확인.
- [ ] **Test 4.3**: CreateTargetForm 테스트
    - 입력 필드 (Name, URL, Scope) 확인.
    - 폼 제출 시 API 호출 확인.
- [ ] **Test 4.4**: EditTargetForm 테스트
    - 기존 Target 데이터로 폼 초기화 확인.
- [ ] **Test 4.5**: 스캔 트리거 테스트
    - "Scan" 버튼 클릭 시 API 호출 확인.
    - 성공/실패 토스트 메시지 확인.

**🟢 GREEN: 테스트를 통과하도록 구현**
- [ ] **Task 4.6**: ProjectDetailPage 생성
    - `pages/projects/ProjectDetailPage.tsx`
    - `useParams()`로 projectId 추출.
    - `useProject(projectId)` 훅으로 프로젝트 조회.
    - `<main>` 태그 내 `<h1>{project.name}</h1>` 표시.
    - 로딩, 에러 상태 UI.
- [ ] **Task 4.7**: 라우팅 추가
    - `App.tsx`에 `/projects/:projectId` 라우트 추가.
    - ProjectDetailPage 컴포넌트 연결.
- [ ] **Task 4.8**: Target 타입 정의
    - `types/target.ts`: `Target`, `TargetCreate`, `TargetUpdate` 인터페이스.
- [ ] **Task 4.9**: Target Service
    - `services/targetService.ts`:
      - `getTargets(projectId)`: Target 목록 조회
      - `getTarget(projectId, targetId)`: 단일 Target 조회
      - `createTarget(projectId, data)`: Target 생성
      - `updateTarget(projectId, targetId, data)`: Target 수정
      - `deleteTarget(projectId, targetId)`: Target 삭제
      - `triggerScan(projectId, targetId)`: 스캔 트리거
- [ ] **Task 4.10**: Target 훅
    - `hooks/useTargets.ts`:
      - `useTargets(projectId)`: Target 목록 조회
      - `useTarget(projectId, targetId)`: 단일 Target 조회
      - `useCreateTarget()`: Target 생성
      - `useUpdateTarget()`: Target 수정
      - `useDeleteTarget()`: Target 삭제
      - `useTriggerScan()`: 스캔 트리거
- [ ] **Task 4.11**: TargetList 컴포넌트
    - `components/features/target/TargetList.tsx`
    - `useTargets(projectId)` 훅 사용.
    - Table 형식으로 Target 목록 표시.
- [ ] **Task 4.12**: CreateTargetForm 컴포넌트
    - `components/features/target/CreateTargetForm.tsx`
    - 필드: Name, URL, Scope.
    - React Hook Form + Zod.
- [ ] **Task 4.13**: EditTargetForm 컴포넌트
    - `components/features/target/EditTargetForm.tsx`
    - CreateTargetForm과 유사.
- [ ] **Task 4.14**: ProjectDetailPage에 Target 기능 통합
    - TargetList 표시.
    - "Add Target" 버튼 → CreateTargetForm.
    - 각 Target 행에 Edit, Delete, Scan 버튼.

**🔵 REFACTOR: 코드 품질 개선**
- [ ] **Task 4.15**: Optimistic Updates (선택사항)
    - 스캔 트리거 후 UI 즉시 업데이트.
    - Target 관련 컴포넌트 추출 및 재사용성 개선.

#### 품질 게이트 ✋
- [ ] 프로젝트 상세 페이지가 프로젝트명을 h1으로 표시함.
- [ ] 프로젝트에 Target을 추가할 수 있음.
- [ ] Target을 수정/삭제할 수 있음.
- [ ] "Scan" 버튼을 클릭하면 토스트/응답을 볼 수 있음.
- [ ] 모든 테스트가 통과함.

---

### Phase 5: 대시보드 & 스캔 결과
**목표**: 스캔 결과(Assets)를 시각화.
**예상 시간**: 3시간
**상태**: ⏳ 대기 중

#### 작업
**🔴 RED: 실패하는 테스트 먼저 작성**
- [ ] **Test 5.1**: Asset Table 테스트
    - Method, URL, Type 렌더링 확인.

**🟢 GREEN: 테스트를 통과하도록 구현**
- [ ] **Task 5.2**: Asset Service & Query
    - `GET /tasks/{id}/assets`.
    - (선택사항) `GET /projects/{id}/assets` (전체 뷰) - *백엔드 지원 필요 또는 파생 뷰*.
- [ ] **Task 5.3**: Asset Table 컴포넌트
    - `components/features/asset/AssetTable.tsx`.
    - 열: Hash, Method, URL, Type, Last Seen.

**🔵 REFACTOR: 코드 품질 개선**
- [ ] **Task 5.4**: 데이터 테이블 최적화
    - 데이터가 많을 경우 페이지네이션/정렬 구현.
    - 비용이 많이 드는 행 메모이제이션.

#### 품질 게이트 ✋
- [ ] 스캔 결과를 볼 수 있음.

---

## 📝 노트 & 학습 내용
*   (구현 중 작성 예정)
