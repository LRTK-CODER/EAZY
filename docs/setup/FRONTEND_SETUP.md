[← 메인 문서로 돌아가기](../README.md)

# Frontend 설정 가이드

EAZY Frontend (React + TypeScript + Vite) 개발 환경을 구축하고 실행하는 방법을 설명합니다.

## 목차

- [개요](#개요)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [설정 단계](#설정-단계)
  - [1. Node.js 설치 확인](#1-nodejs-설치-확인)
  - [2. 의존성 설치](#2-의존성-설치)
  - [3. 환경 변수 설정](#3-환경-변수-설정)
  - [4. 개발 서버 실행](#4-개발-서버-실행)
- [개발 도구](#개발-도구)
  - [테스트 실행](#테스트-실행)
  - [코드 포맷팅](#코드-포맷팅)
  - [빌드](#빌드)
  - [Storybook](#storybook)
- [패키지 관리](#패키지-관리)
- [문제 해결](#문제-해결)

---

## 개요

EAZY Frontend는 다음 기술 스택으로 구성되어 있습니다:

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
| **Vitest** | 4.0.16 | 테스트 러너 (TDD) |
| **Storybook** | 10.1.10 | 컴포넌트 개발 환경 |

---

## 기술 스택

### 핵심 라이브러리

**Vite (빌드 도구)**
- ES 모듈 기반 초고속 HMR (Hot Module Replacement)
- Rollup 기반 프로덕션 빌드
- TypeScript 네이티브 지원

**shadcn/ui (UI 컴포넌트)**
- Radix UI 기반 접근성 우선 컴포넌트
- 복사-붙여넣기 방식 (npm 패키지 아님)
- Tailwind CSS로 스타일링

**TanStack Query (서버 상태 관리)**
- 자동 캐싱 및 재검증
- 폴링 및 백그라운드 업데이트
- Optimistic Updates 지원

---

## 프로젝트 구조

```
frontend/src/
├── components/
│   ├── ui/                        # 93개 shadcn/ui 컴포넌트
│   │   ├── button.tsx
│   │   ├── dialog.tsx
│   │   ├── form.tsx
│   │   └── ...
│   │
│   ├── features/                  # 도메인 컴포넌트
│   │   ├── project/               # 9개 프로젝트 컴포넌트
│   │   └── target/                # 5개 타겟 컴포넌트
│   │
│   ├── layout/                    # 레이아웃 컴포넌트
│   │   ├── MainLayout.tsx
│   │   ├── Header.tsx
│   │   └── Sidebar.tsx
│   │
│   └── theme/                     # 테마 컴포넌트
│       ├── theme-provider.tsx
│       └── theme-toggle.tsx
│
├── pages/                         # 5개 페이지 컴포넌트
│   ├── ProjectsPage.tsx
│   ├── ActiveProjectsListPage.tsx
│   ├── ArchivedProjectsPage.tsx
│   ├── ProjectDetailPage.tsx
│   └── DashboardPage.tsx
│
├── hooks/                         # Custom Hooks
│   ├── useProjects.ts             # 프로젝트 CRUD 훅
│   ├── useTargets.ts              # 타겟 CRUD 훅
│   ├── useTasks.ts                # Task 폴링 훅
│   └── use-mobile.tsx             # 모바일 감지
│
├── services/                      # API 클라이언트
│   ├── projectService.ts
│   ├── targetService.ts
│   └── taskService.ts
│
├── types/                         # TypeScript 타입 정의
│   ├── project.ts
│   ├── target.ts
│   └── task.ts
│
├── schemas/                       # Zod 스키마
│   ├── projectSchema.ts
│   └── targetSchema.ts
│
├── lib/                           # 유틸리티
│   ├── api.ts                     # Axios 설정
│   └── utils.ts                   # cn 함수
│
├── App.tsx                        # 라우팅 설정
├── main.tsx                       # React 진입점
└── index.css                      # TailwindCSS v4 설정
```

---

## 설정 단계

### 1. Node.js 설치 확인

Node.js 18.x 이상이 필요합니다 (20.x 권장).

```bash
node --version
# 출력 예: v20.11.0

npm --version
# 출력 예: 10.2.4
```

설치되지 않은 경우 [환경 설정 가이드](./ENVIRONMENT_SETUP.md#2-nodejs-frontend)를 참고하세요.

---

### 2. 의존성 설치

프로젝트 루트 (frontend/)에서 npm 의존성을 설치합니다:

```bash
cd frontend
npm install
```

**출력 예:**
```
added 1245 packages in 15s
```

> **참고:** `npm install`은 `package.json`의 모든 의존성을 설치합니다.

---

### 3. 환경 변수 설정

`.env` 파일을 생성합니다:

```bash
touch .env
```

다음 내용을 `.env` 파일에 추가:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

> **중요:** Vite에서 환경 변수는 반드시 `VITE_` 접두사로 시작해야 합니다.

---

### 4. 개발 서버 실행

Vite 개발 서버를 시작합니다:

```bash
npm run dev
```

**출력 예:**
```
  VITE v7.2.4  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**서버 접속:**
- Frontend URL: http://localhost:5173

**특징:**
- 초고속 Hot Module Replacement (HMR)
- TypeScript 즉시 컴파일
- 코드 변경 시 자동 새로고침

**옵션:**
```bash
# 특정 포트 사용
npm run dev -- --port 3000

# 외부 접근 허용
npm run dev -- --host

# 디버그 모드
npm run dev -- --debug
```

---

## 개발 도구

### 테스트 실행

EAZY는 Vitest와 React Testing Library를 사용합니다.

#### 전체 테스트

```bash
npm run test
```

**출력 예:**
```
✓ src/components/features/project/CreateProjectForm.test.tsx (12)
✓ src/components/features/target/TargetList.test.tsx (8)
✓ src/services/projectService.test.ts (17)
...

Test Files  16 passed (16)
     Tests  168 passed (168)
```

#### Watch 모드

```bash
npm run test:watch
```

코드 변경 시 관련 테스트만 자동 재실행합니다.

#### UI 모드

```bash
npm run test:ui
```

브라우저에서 인터랙티브 테스트 UI를 제공합니다.

#### 커버리지

```bash
npm run test:coverage
```

커버리지 리포트는 `coverage/index.html`에서 확인 가능합니다.

---

### 코드 포맷팅

#### Prettier (코드 포맷터)

```bash
# 전체 코드 포맷팅
npm run format

# 특정 파일 포맷팅
npx prettier --write src/App.tsx

# Dry-run (변경사항 미리보기)
npx prettier --check .
```

#### ESLint (린터)

```bash
# 린트 검사
npm run lint

# 자동 수정
npm run lint:fix
```

---

### 빌드

#### 프로덕션 빌드

```bash
npm run build
```

**출력:**
```
vite v7.2.4 building for production...
✓ 1234 modules transformed.
dist/index.html                   0.45 kB
dist/assets/index-abc123.css      12.34 kB │ gzip: 3.45 kB
dist/assets/index-xyz789.js      234.56 kB │ gzip: 78.90 kB

✓ built in 5.67s
```

빌드 결과는 `dist/` 디렉토리에 생성됩니다.

#### 빌드 미리보기

```bash
npm run preview
```

프로덕션 빌드를 로컬에서 미리 확인합니다 (http://localhost:4173).

---

### Storybook

Storybook은 UI 컴포넌트를 독립적으로 개발하고 문서화하는 도구입니다.

#### Storybook 개발 서버

```bash
npm run storybook
```

**출력 예:**
```
╭─────────────────────────────────────────────────╮
│                                                 │
│   Storybook 10.1.10 for react-vite started     │
│   http://localhost:6006                         │
│                                                 │
╰─────────────────────────────────────────────────╯
```

브라우저에서 http://localhost:6006 접속.

#### Storybook 빌드

```bash
npm run build-storybook
```

정적 Storybook 사이트가 `storybook-static/` 디렉토리에 생성됩니다.

---

## 패키지 관리

### 패키지 추가

```bash
# 프로덕션 의존성 추가
npm install <package-name>

# 개발 의존성 추가
npm install --save-dev <package-name>

# 특정 버전 설치
npm install <package-name>@1.2.3
```

### 패키지 제거

```bash
npm uninstall <package-name>
```

### 패키지 업데이트

```bash
# 모든 패키지 업데이트
npm update

# 특정 패키지 업데이트
npm update <package-name>

# 업데이트 가능한 패키지 확인
npm outdated
```

### 의존성 보안 검사

```bash
# 보안 취약점 확인
npm audit

# 자동 수정 (권장)
npm audit fix

# 강제 수정 (주의 필요)
npm audit fix --force
```

---

## 문제 해결

### 1. 포트 충돌 (5173)

**증상:**
```
Port 5173 is in use, trying another one...
```

**해결 방법:**
```bash
# 포트 사용 프로세스 확인 (macOS/Linux)
lsof -i :5173

# 프로세스 종료
kill -9 <PID>

# 또는 다른 포트 사용
npm run dev -- --port 3000
```

---

### 2. 의존성 설치 실패

**증상:**
```
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
```

**해결 방법:**
```bash
# 1. node_modules 및 package-lock.json 삭제
rm -rf node_modules package-lock.json

# 2. npm 캐시 클리어
npm cache clean --force

# 3. 재설치
npm install

# 4. 문제 지속 시: legacy peer deps 사용
npm install --legacy-peer-deps
```

---

### 3. TypeScript 오류

**증상:**
```
Type 'string' is not assignable to type 'number'
```

**해결 방법:**
```bash
# 1. TypeScript 컴파일 체크
npx tsc --noEmit

# 2. VSCode 재시작
# Command Palette (Cmd+Shift+P) → "TypeScript: Restart TS Server"

# 3. 타입 정의 업데이트
npm install --save-dev @types/node @types/react @types/react-dom
```

---

### 4. Backend API 연결 실패

**증상:**
```
AxiosError: Network Error
```

**해결 방법:**
```bash
# 1. Backend 서버 상태 확인
curl http://localhost:8000/health

# 2. 환경 변수 확인
cat .env
# VITE_API_BASE_URL=http://localhost:8000/api/v1 확인

# 3. CORS 설정 확인
# backend/.env의 BACKEND_CORS_ORIGINS에
# http://localhost:5173이 포함되어 있는지 확인
```

---

### 5. Vite 빌드 오류

**증상:**
```
[vite]: Rollup failed to resolve import
```

**해결 방법:**
```bash
# 1. 의존성 재설치
npm install

# 2. Vite 캐시 삭제
rm -rf node_modules/.vite

# 3. TypeScript 체크
npx tsc --noEmit

# 4. 문제 지속 시: 빌드 로그 확인
npm run build -- --debug
```

---

### 6. Storybook 실행 오류

**증상:**
```
Error: Cannot find module '@storybook/react-vite'
```

**해결 방법:**
```bash
# 1. Storybook 의존성 재설치
npm install --save-dev @storybook/react-vite

# 2. Storybook 업그레이드
npx storybook@latest upgrade

# 3. Storybook 캐시 삭제
rm -rf node_modules/.cache/storybook
```

---

## 추가 참고 자료

- **[Backend 설정 가이드](./BACKEND_SETUP.md)** - Backend API 실행 방법
- **[Docker 설정 가이드](./DOCKER_SETUP.md)** - PostgreSQL 및 Redis 관리
- **[문제 해결 가이드](./TROUBLESHOOTING.md)** - 자주 발생하는 오류
- **[컴포넌트 카탈로그](../reference/COMPONENTS.md)** - UI 컴포넌트 문서
- **React 공식 문서**: https://react.dev/
- **Vite 공식 문서**: https://vitejs.dev/
- **TanStack Query**: https://tanstack.com/query/latest
- **shadcn/ui**: https://ui.shadcn.com/

---

**작성:** EAZY Technical Writer
**최종 업데이트:** 2026-01-09
