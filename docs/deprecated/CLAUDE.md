# ⚠️ DEPRECATED - 이 문서는 더 이상 유지되지 않습니다

> **이 문서는 2026-01-09부로 폐기되었습니다.**
> 대신 **[docs/README.md](../README.md)**를 참고하세요.
>
> CLAUDE.md (1,900줄)는 관리하기 어려워 다음과 같이 분리되었습니다:
> - **기준 문서**: [docs/reference/](../reference/)
> - **환경 설정**: [docs/setup/](../setup/)
> - **개발 가이드**: [docs/development/](../development/)
> - **빠른 시작**: [docs/QUICK_START.md](../QUICK_START.md)

---

# EAZY 프로젝트 종합 문서 (아카이브)

> AI 기반 지능형 동적 애플리케이션 보안 테스팅(DAST) 도구

**최종 업데이트**: 2026-01-04
**문서 버전**: 1.0
**프로젝트 버전**: 0.1.0 (MVP)

---

## Quick Reference (다른 세션에서 빠른 참조용)

### 프로젝트 한줄 요약
**EAZY**는 LLM을 활용해 웹 애플리케이션의 비즈니스 로직 취약점을 탐지하는 AI 기반 DAST 도구입니다.

### 핵심 기술 스택
```
Backend:  Python 3.12 + FastAPI + SQLModel + PostgreSQL + Redis + Playwright
Frontend: React 19 + TypeScript + Vite + TailwindCSS + shadcn/ui + TanStack Query
패키지:   UV (Backend - 필수), npm (Frontend)
```

### 현재 진행 상태
| 영역 | 진행률 | 현재 Phase | 다음 작업 |
|-----|--------|-----------|----------|
| Backend | 80% | Phase 4 완료 | Asset API 엔드포인트 |
| Frontend | 85% | Phase 4 완료 | Phase 5: Asset 시각화 |

### 필수 개발 규칙
1. **TDD 엄격 준수**: RED → GREEN → REFACTOR (테스트 먼저 작성)
2. **UV 필수 사용**: Python 실행 시 반드시 `uv run` 사용 (pip 금지)
3. **Type Hint 필수**: Backend(mypy), Frontend(TypeScript strict)
4. **Conventional Commits**: `feat:`, `fix:`, `test:`, `docs:` 등 prefix 사용
5. **한국어 커뮤니케이션**: 사용자와 대화는 한국어로

### 빠른 실행 명령어
```bash
# Backend 실행
cd backend
docker compose -f docker/docker-compose.yml up -d  # PostgreSQL, Redis 시작
uv sync                                             # 의존성 설치
uv run alembic upgrade head                         # DB 마이그레이션
uv run uvicorn app.main:app --reload                # 서버 시작 (localhost:8000)
uv run python -m app.worker                         # Worker 시작 (별도 터미널)

# Frontend 실행
cd frontend
npm install                                         # 의존성 설치
npm run dev                                         # 개발 서버 (localhost:5173)

# 테스트 실행
uv run pytest                                       # Backend 테스트
npm run test                                        # Frontend 테스트 (168개)
```

### 핵심 파일 경로
```
# 계획 문서 (작업 전 반드시 확인)
docs/plans/frontend/INDEX.md           # Frontend MVP 메인 인덱스
docs/plans/frontend/PHASE5_CURRENT.md  # 현재 진행 중인 Phase
docs/plans/PLAN_MVP_Backend.md         # Backend MVP 진행 상황

# Backend 핵심
backend/app/main.py               # FastAPI 진입점
backend/app/worker.py             # Redis Worker
backend/app/services/             # 비즈니스 로직 (5개)
backend/app/models/               # SQLModel 엔티티 (4개)

# Frontend 핵심
frontend/src/App.tsx              # 라우팅 설정
frontend/src/pages/               # 페이지 컴포넌트 (5개)
frontend/src/hooks/               # TanStack Query 훅 (useProjects, useTargets, useTasks)
frontend/src/services/            # API 클라이언트 (3개)
frontend/src/components/features/ # 도메인 컴포넌트 (project/, target/)
```

### 데이터 모델 요약
```
PROJECT (1) ──< (N) TARGET (1) ──< (N) TASK (1) ──< (N) ASSET
    │                │                  │               │
    │                │                  │               └─ 공격 표면 (URL, FORM, XHR)
    │                │                  └─ 비동기 작업 (PENDING → RUNNING → COMPLETED/FAILED)
    │                └─ 스캔 대상 (scope: DOMAIN/SUBDOMAIN/URL_ONLY)
    └─ 프로젝트 (is_archived: Soft Delete)
```

### API 엔드포인트 요약
```
# Projects
POST   /api/v1/projects/              # 생성
GET    /api/v1/projects/              # 목록 (archived=true/false)
GET    /api/v1/projects/{id}          # 조회
PATCH  /api/v1/projects/{id}          # 수정
DELETE /api/v1/projects/{id}          # Archive (Soft Delete)
DELETE /api/v1/projects/{id}?permanent=true  # 영구 삭제

# Targets
POST   /api/v1/projects/{id}/targets/ # 생성
GET    /api/v1/projects/{id}/targets/ # 목록
PATCH  /api/v1/projects/{id}/targets/{tid}  # 수정
DELETE /api/v1/projects/{id}/targets/{tid}  # 삭제
POST   /api/v1/projects/{id}/targets/{tid}/scan  # 스캔 트리거 (202 Accepted)

# Tasks
GET    /api/v1/tasks/{id}             # 상태 조회
GET    /api/v1/tasks/{id}/assets      # 발견된 Asset 목록
```

### 테스트 현황
| 영역 | 파일 수 | 테스트 수 | 상태 |
|-----|--------|---------|------|
| Frontend | 16개 | 168개 | 모두 통과 |
| Backend | 11개 | 다수 | 모두 통과 |

### 자주 하는 실수 방지
- ❌ `pip install` 사용 → ✅ `uv add <package>` 또는 `uv sync`
- ❌ `python script.py` 실행 → ✅ `uv run python script.py`
- ❌ 테스트 없이 구현 → ✅ 테스트 먼저 작성 (RED phase)
- ❌ 영어로 대화 → ✅ 한국어로 대화

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [기술 스택](#2-기술-스택)
3. [프로젝트 구조](#3-프로젝트-구조)
4. [아키텍처](#4-아키텍처)
5. [데이터베이스 스키마](#5-데이터베이스-스키마)
6. [API 명세](#6-api-명세)
7. [주요 기능](#7-주요-기능)
8. [개발 환경 설정](#8-개발-환경-설정)
9. [개발 컨벤션](#9-개발-컨벤션)
10. [테스트 전략](#10-테스트-전략)
11. [Claude 에이전트 시스템](#11-claude-에이전트-시스템)
12. [현재 진행 상황](#12-현재-진행-상황)
13. [주요 파일 경로](#13-주요-파일-경로)

---

## 1. 프로젝트 개요

### 프로젝트명
**EAZY** - AI-Powered Dynamic Application Security Testing Tool

### 목표
단순한 웹 스캐너를 넘어 **LLM(ChatGPT, Gemini, Claude)**을 활용하여 웹 애플리케이션의 **비즈니스 로직과 흐름을 심층 분석**하는 지능형 DAST 도구 개발

### 핵심 차별점
- **비즈니스 로직 취약점(Business Logic Vulnerabilities)** 탐지
  - 기존 DAST 도구가 발견하기 어려운 논리적 허점 식별
- **연쇄 공격(Chained Attacks)** 가능성 탐지
- **React Flow 기반 비즈니스 로직 맵** 시각화

### 핵심 기능 (5대 모듈)
1. **프로젝트 및 타겟 관리**: 진단 대상 그룹화, LLM 설정 관리
2. **공격 표면 식별 (Attack Surface Discovery)**
   - Active Scan: Playwright 기반 패턴 크롤링
   - Passive Scan: Mitmproxy 기반 사용자 주도 패시브 스캔
3. **AI 기반 취약점 분석**: 기능 흐름(Flow)을 LLM에 주입하여 논리적 허점 도출
4. **공격 수행 (Attack Execution)**: 시나리오 기반 다단계 공격 검증
5. **결과 시각화**: React Flow를 활용한 공격 경로 시각화

### MVP 범위
현재 MVP는 **프로젝트 관리**와 **공격 표면 식별** 기능에 집중
(LLM 분석 및 공격 수행 모듈은 추후 Phase)

### 라이선스
Apache License 2.0

---

## 2. 기술 스택

### Backend

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

**UV (고속 패키지 매니저) 특징**:
- Rust 기반으로 pip 대비 **10-100배 빠른 설치 속도**
- pyproject.toml 기반 의존성 관리
- 자동 가상환경 생성 및 관리
- Lock 파일을 통한 재현 가능한 빌드

### Frontend

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

### 인프라

- **Docker Compose**: PostgreSQL, Redis 컨테이너 관리
- **UV**: Backend 패키지 관리 (Rust 기반, pip 대체)
- **npm**: Frontend 패키지 관리

---

## 3. 프로젝트 구조

### Backend 디렉토리 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 애플리케이션 진입점
│   ├── worker.py                  # Redis Queue Worker (비동기 크롤링)
│   │
│   ├── core/                      # 핵심 인프라
│   │   ├── config.py              # 환경 설정 (Pydantic Settings)
│   │   ├── db.py                  # PostgreSQL AsyncEngine
│   │   ├── redis.py               # Redis 연결
│   │   └── queue.py               # TaskManager (Redis Queue 관리)
│   │
│   ├── models/                    # SQLModel 엔티티 (4개)
│   │   ├── project.py             # Project (is_archived 지원)
│   │   ├── target.py              # Target (scope 지원)
│   │   ├── task.py                # Task (PENDING/RUNNING/COMPLETED/FAILED)
│   │   └── asset.py               # Asset, AssetDiscovery (공격 표면)
│   │
│   ├── services/                  # 비즈니스 로직 레이어 (5개)
│   │   ├── project_service.py     # Project CRUD
│   │   ├── target_service.py      # Target CRUD
│   │   ├── task_service.py        # Task 생성 및 큐 관리
│   │   ├── crawler_service.py     # Playwright 크롤러
│   │   └── asset_service.py       # Asset 중복 제거 및 이력 관리
│   │
│   └── api/v1/endpoints/          # RESTful API (2개)
│       ├── project.py             # Project + Target CRUD
│       └── task.py                # Task 트리거 & 조회
│
├── tests/                         # Pytest 테스트 스위트 (11개)
│   ├── api/                       # API 엔드포인트 테스트
│   ├── core/                      # 인프라 테스트
│   ├── services/                  # 서비스 레이어 테스트
│   └── integration/               # 통합 테스트
│
├── alembic/                       # DB 마이그레이션
│   ├── versions/                  # 8개 마이그레이션 파일
│   └── env.py
│
├── docker/
│   └── docker-compose.yml         # PostgreSQL + Redis
│
├── pyproject.toml                 # UV 의존성 관리
└── alembic.ini                    # Alembic 설정
```

**파일 통계**:
- Python 파일: 19개
- 테스트 파일: 11개
- 마이그레이션: 8개

### Frontend 디렉토리 구조

```
frontend/src/
├── components/
│   ├── ui/                        # 93개 shadcn/ui 컴포넌트 (Radix UI 기반)
│   │   ├── button.tsx             # Button, ButtonGroup
│   │   ├── dialog.tsx             # Dialog, Alert Dialog
│   │   ├── form.tsx               # Form 컴포넌트
│   │   ├── input.tsx, textarea.tsx
│   │   ├── table.tsx              # Table (TanStack Table)
│   │   ├── card.tsx, badge.tsx
│   │   └── ... (총 93개)
│   │
│   ├── features/                  # 도메인 컴포넌트
│   │   ├── project/               # 9개 컴포넌트
│   │   │   ├── CreateProjectForm.tsx
│   │   │   ├── EditProjectForm.tsx
│   │   │   ├── DeleteProjectDialog.tsx
│   │   │   ├── ArchivedDialog.tsx
│   │   │   ├── RestoreDialog.tsx
│   │   │   ├── PermanentDeleteDialog.tsx
│   │   │   ├── ProjectFormFields.tsx
│   │   │   ├── ActiveProjectItem.tsx
│   │   │   └── ArchivedProjectItem.tsx
│   │   │
│   │   └── target/                # 5개 컴포넌트
│   │       ├── TargetList.tsx     # Target 목록 테이블
│   │       ├── CreateTargetForm.tsx
│   │       ├── EditTargetForm.tsx
│   │       ├── DeleteTargetDialog.tsx
│   │       └── TargetFormFields.tsx
│   │
│   ├── layout/                    # 3개 레이아웃 컴포넌트
│   │   ├── MainLayout.tsx         # 전체 레이아웃 (Grid)
│   │   ├── Header.tsx             # 상단 헤더
│   │   └── Sidebar.tsx            # 동적 사이드바 (422줄)
│   │
│   └── theme/                     # 2개 테마 컴포넌트
│       ├── theme-provider.tsx
│       └── theme-toggle.tsx
│
├── pages/                         # 5개 페이지 컴포넌트
│   ├── ProjectsPage.tsx           # 프로젝트 허브
│   ├── ActiveProjectsListPage.tsx # 활성 프로젝트 목록
│   ├── ArchivedProjectsPage.tsx   # 아카이브 프로젝트 목록
│   ├── ProjectDetailPage.tsx      # 프로젝트 상세 + Target 관리
│   └── DashboardPage.tsx          # 대시보드 (placeholder)
│
├── hooks/                         # Custom Hooks (4개)
│   ├── useProjects.ts             # 7개 export (CRUD + 일괄 삭제)
│   ├── useTargets.ts              # 6개 export (CRUD + 스캔 트리거)
│   ├── useTasks.ts                # Task 상태 폴링 (5초 간격)
│   └── use-mobile.tsx             # 모바일 감지
│
├── services/                      # API 클라이언트 (3개)
│   ├── projectService.ts          # 17개 테스트 통과
│   ├── targetService.ts           # 15개 테스트 통과
│   └── taskService.ts             # 4개 테스트 통과
│
├── types/                         # TypeScript 타입 정의 (3개)
│   ├── project.ts
│   ├── target.ts
│   └── task.ts
│
├── schemas/                       # Zod 스키마 (2개)
│   ├── projectSchema.ts
│   └── targetSchema.ts
│
├── lib/                           # 유틸리티
│   ├── api.ts                     # Axios 설정 및 래퍼
│   └── utils.ts                   # cn (clsx + tailwind-merge)
│
├── utils/
│   └── date.ts                    # 날짜 포맷팅 (date-fns)
│
├── config/
│   └── nav.ts                     # 네비게이션 설정
│
├── App.tsx                        # 라우팅 설정
├── main.tsx                       # React 진입점
└── index.css                      # TailwindCSS v4 설정
```

**파일 통계**:
- TypeScript 파일: 151개
- 테스트 파일: 16개 (168개 테스트 통과)
- UI 컴포넌트: 93개 (shadcn/ui)
- Storybook Stories: 47개

---

## 4. 아키텍처

### 시스템 구성도

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │ ◄─────► │   React     │ ◄─────► │   FastAPI   │
│             │  HTTP   │   Frontend  │  REST   │   Backend   │
└─────────────┘         └─────────────┘         └──────┬──────┘
                                                        │
                        ┌───────────────────────────────┼───────────────┐
                        │                               │               │
                   ┌────▼─────┐                   ┌─────▼────┐   ┌─────▼────┐
                   │PostgreSQL│                   │  Redis   │   │Playwright│
                   │   (DB)   │                   │  (Queue) │   │(Crawler) │
                   └──────────┘                   └──────────┘   └──────────┘
```

### Backend Layered Architecture

```
┌─────────────────────────────────────────┐
│   API Layer (Controllers/Routers)       │  FastAPI Endpoints
├─────────────────────────────────────────┤
│   Service Layer (Business Logic)        │  ProjectService, CrawlerService
├─────────────────────────────────────────┤
│   Repository Layer (Data Access)        │  SQLModel ORM
├─────────────────────────────────────────┤
│   Infrastructure Layer                  │  DB, Redis, Queue
└─────────────────────────────────────────┘
```

**레이어별 책임**:
- **API Layer**: HTTP 요청/응답 처리, 데이터 유효성 검증
- **Service Layer**: 비즈니스 로직, 트랜잭션 관리
- **Repository Layer**: DB 접근 추상화
- **Infrastructure Layer**: DB 연결, Redis 큐, 설정 관리

### Frontend Atomic Design Architecture

```
┌─────────────────────────────────────────┐
│   Pages (Templates)                     │  ProjectDetailPage, DashboardPage
├─────────────────────────────────────────┤
│   Features (Organisms/Molecules)        │  CreateProjectForm, TargetList
├─────────────────────────────────────────┤
│   UI Components (Atoms)                 │  Button, Input, Dialog (shadcn)
├─────────────────────────────────────────┤
│   State Management                      │  TanStack Query (서버 상태)
├─────────────────────────────────────────┤
│   Services & Hooks                      │  API Client, Custom Hooks
└─────────────────────────────────────────┘
```

### 데이터 플로우 (스캔 트리거 예시)

```
1. User: "Scan" 버튼 클릭 (Frontend)
   ↓
2. useTriggerScan.mutate() → POST /targets/{id}/scan
   ↓
3. TargetService.trigger_scan()
   ↓
4. Task 생성 (DB, status: PENDING) + Redis Queue.enqueue()
   ↓ (202 Accepted 반환)
5. Worker.dequeue() → CrawlerService.crawl()
   ↓
6. Playwright Browser → HTML 파싱 → Link 추출
   ↓
7. AssetService.process_asset() → content_hash 기반 UPSERT
   ↓
8. Task.status = COMPLETED (result JSON 저장)
   ↓
9. Frontend: useTaskStatus() 폴링 → UI 업데이트
```

### 비동기 처리 패턴

**Backend**: Redis Queue + Worker Process (ARQ 패턴)
- API 서버와 크롤링 작업 분리
- Worker는 독립 프로세스로 실행 (`app.worker`)
- Redis FIFO Queue로 작업 관리

**Frontend**: TanStack Query Polling
- `refetchInterval: 5000` (5초)
- Task 상태가 COMPLETED/FAILED 시 폴링 자동 중지

---

## 5. 데이터베이스 스키마

### ERD (Entity Relationship Diagram)

```
┌─────────────────┐
│   projects      │
├─────────────────┤
│ id (PK)         │
│ name            │◄───┐
│ description     │    │
│ is_archived     │    │  1:N
│ archived_at     │    │
│ created_at      │    │
│ updated_at      │    │
└─────────────────┘    │
                       │
┌─────────────────┐    │
│   targets       │    │
├─────────────────┤    │
│ id (PK)         │────┘
│ project_id (FK) │
│ name            │◄───┐
│ url             │    │
│ description     │    │  1:N
│ scope (ENUM)    │    │
│ created_at      │    │
│ updated_at      │    │
└─────────────────┘    │
                       │
┌─────────────────┐    │
│   tasks         │    │
├─────────────────┤    │
│ id (PK)         │────┘
│ project_id (FK) │◄───┐
│ target_id (FK)  │    │
│ type (ENUM)     │    │  1:N
│ status (ENUM)   │    │
│ result (JSON)   │    │
│ created_at      │    │
│ updated_at      │    │
└─────────────────┘    │
                       │
┌─────────────────────┐│
│   assets            ││
├─────────────────────┤│
│ id (PK)             │├┘
│ target_id (FK)      ││
│ content_hash (UQ)   ││◄──┐
│ type (ENUM)         ││   │
│ source (ENUM)       ││   │ N:M
│ method              ││   │
│ url                 ││   │
│ path                ││   │
│ request_spec (JSON) ││   │
│ response_spec (JSON)││   │
│ parameters (JSON)   ││   │
│ last_task_id (FK)   │├───┤
│ first_seen_at       ││   │
│ last_seen_at        ││   │
└─────────────────────┘│   │
                       │   │
┌──────────────────────┐   │
│ asset_discoveries    │   │
├──────────────────────┤   │
│ id (PK)              │   │
│ task_id (FK)         │───┘
│ asset_id (FK)        │───┐
│ parent_asset_id (FK) │◄──┘ (자기참조)
│ discovered_at        │
└──────────────────────┘
```

### 테이블 상세

#### 1. Projects (프로젝트)

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_archived BOOLEAN DEFAULT FALSE,  -- Soft Delete
    archived_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**특징**:
- **Soft Delete 패턴**: `is_archived`, `archived_at`
- Archive/Restore 기능 지원
- Target/Task와 1:N 관계 (CASCADE DELETE)

#### 2. Targets (스캔 대상)

```sql
CREATE TABLE targets (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(2048) NOT NULL,
    scope VARCHAR(20) NOT NULL,  -- ENUM: DOMAIN/SUBDOMAIN/URL_ONLY
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Scope ENUM 정의
-- DOMAIN: 전체 도메인 스캔 (subdomain 포함)
-- SUBDOMAIN: 특정 서브도메인만
-- URL_ONLY: 단일 URL만
```

**특징**:
- Project 종속 (1:N)
- Scope 옵션으로 크롤링 범위 제어

#### 3. Tasks (비동기 작업)

```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    target_id INTEGER REFERENCES targets(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,  -- ENUM: CRAWL, SCAN
    status VARCHAR(20) NOT NULL,  -- ENUM: PENDING, RUNNING, COMPLETED, FAILED
    result TEXT,  -- JSON 문자열
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**상태 전이**:
```
PENDING → RUNNING → COMPLETED
                 → FAILED
```

**result JSON 예시**:
```json
{
  "found_links": 15,
  "saved_assets": 12,
  "duration_ms": 3500,
  "error": null
}
```

#### 4. Assets (공격 표면)

```sql
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    content_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 (중복 제거 키)
    type VARCHAR(20) NOT NULL,  -- ENUM: URL, FORM, XHR
    source VARCHAR(20) NOT NULL,  -- ENUM: HTML, JS, NETWORK, DOM
    method VARCHAR(10) NOT NULL,  -- HTTP Method
    url VARCHAR(2048) NOT NULL,
    path VARCHAR(2048) NOT NULL,
    request_spec JSONB,  -- 요청 패킷 (Headers, Body, Cookies)
    response_spec JSONB,  -- 응답 패킷 (Headers, Body, Status)
    parameters JSONB,  -- 파라미터 분석 (Name, Type, Location, Value)
    last_task_id INTEGER REFERENCES tasks(id),
    first_seen_at TIMESTAMP NOT NULL,
    last_seen_at TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX idx_asset_content_hash ON assets(content_hash);
```

**content_hash 생성 로직**:
```python
content = f"{method}:{url}"
content_hash = hashlib.sha256(content.encode()).hexdigest()
```

**중복 제거 전략 (Dual View)**:
1. **Total View**: `assets` 테이블 (유니크한 공격 표면의 최신 상태)
2. **Scan History**: `asset_discoveries` 테이블 (각 스캔 작업별 발견 이력)

#### 5. AssetDiscoveries (스캔 이력)

```sql
CREATE TABLE asset_discoveries (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    parent_asset_id INTEGER REFERENCES assets(id),  -- 유입 경로 추적
    discovered_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**특징**:
- Task와 Asset 간 Many-to-Many 관계
- `parent_asset_id`로 자산 발견 계층 추적 (어떤 URL에서 발견되었는지)

### 마이그레이션 이력

1. `3d8835436778`: Project 테이블 생성
2. `b72e50c328e9`: Target 테이블 생성
3. `b4ffda872654`: Task 테이블 생성
4. `c20804e39fe7`: Asset 및 AssetDiscoveries 테이블 생성
5. `f0732575d8bc`: Target에 `scope` 필드 추가
6. `58583a82aff1`: Project에 `is_archived` 필드 추가
7. `03d37afa12f2`: Project에 `archived_at` 필드 추가

---

## 6. API 명세

### Base URL

- **개발 환경**: `http://localhost:8000`
- **API Prefix**: `/api/v1`

### 인증

현재 MVP에서는 인증 미구현 (추후 JWT 기반 인증 계획)

### 공통 응답 형식

**성공 응답**:
```json
{
  "id": 1,
  "name": "Example",
  ...
}
```

**에러 응답**:
```json
{
  "detail": "Error message"
}
```

### 엔드포인트

#### 헬스 체크

```http
GET /health
```

**응답 (200 OK)**:
```json
{
  "status": "healthy"
}
```

---

#### Projects API

**1. 프로젝트 생성**
```http
POST /api/v1/projects/
Content-Type: application/json

{
  "name": "My Project",
  "description": "Optional description"
}
```

**응답 (201 Created)**:
```json
{
  "id": 1,
  "name": "My Project",
  "description": "Optional description",
  "is_archived": false,
  "archived_at": null,
  "created_at": "2026-01-04T12:00:00Z",
  "updated_at": "2026-01-04T12:00:00Z"
}
```

---

**2. 프로젝트 목록 조회**
```http
GET /api/v1/projects/?skip=0&limit=10&archived=false
```

**Query Parameters**:
- `skip` (int): 페이지네이션 오프셋 (기본: 0)
- `limit` (int): 페이지 크기 (기본: 100)
- `archived` (bool): 아카이브 필터 (기본: false)

**응답 (200 OK)**:
```json
[
  {
    "id": 1,
    "name": "Project 1",
    ...
  },
  {
    "id": 2,
    "name": "Project 2",
    ...
  }
]
```

---

**3. 프로젝트 조회**
```http
GET /api/v1/projects/{project_id}
```

**응답 (200 OK)**: Project 객체

---

**4. 프로젝트 수정**
```http
PATCH /api/v1/projects/{project_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**응답 (200 OK)**: 수정된 Project 객체

---

**5. 프로젝트 삭제 (Archive)**
```http
DELETE /api/v1/projects/{project_id}
```

**동작**: `is_archived=true`, `archived_at=NOW()` 설정 (Soft Delete)
**응답 (204 No Content)**

---

**6. 프로젝트 영구 삭제**
```http
DELETE /api/v1/projects/{project_id}?permanent=true
```

**동작**: DB에서 완전 삭제 (Hard Delete, CASCADE)
**응답 (204 No Content)**

---

**7. 프로젝트 복원**
```http
PATCH /api/v1/projects/{project_id}/restore
```

**동작**: `is_archived=false`, `archived_at=null` 설정
**응답 (204 No Content)**

---

#### Targets API

**1. Target 생성**
```http
POST /api/v1/projects/{project_id}/targets/
Content-Type: application/json

{
  "name": "Main Website",
  "url": "https://example.com",
  "description": "Optional",
  "scope": "DOMAIN"
}
```

**응답 (201 Created)**:
```json
{
  "id": 1,
  "project_id": 1,
  "name": "Main Website",
  "url": "https://example.com",
  "description": "Optional",
  "scope": "DOMAIN",
  "created_at": "2026-01-04T12:00:00Z",
  "updated_at": "2026-01-04T12:00:00Z"
}
```

---

**2. Target 목록 조회**
```http
GET /api/v1/projects/{project_id}/targets/
```

**응답 (200 OK)**: Target 배열

---

**3. Target 조회**
```http
GET /api/v1/projects/{project_id}/targets/{target_id}
```

**응답 (200 OK)**: Target 객체

---

**4. Target 수정**
```http
PATCH /api/v1/projects/{project_id}/targets/{target_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "scope": "SUBDOMAIN"
}
```

**응답 (200 OK)**: 수정된 Target 객체

---

**5. Target 삭제**
```http
DELETE /api/v1/projects/{project_id}/targets/{target_id}
```

**응답 (204 No Content)**

---

**6. 스캔 트리거**
```http
POST /api/v1/projects/{project_id}/targets/{target_id}/scan
```

**동작**:
1. Task 생성 (DB, status: PENDING)
2. Redis Queue에 작업 Enqueue
3. Worker가 비동기로 크롤링 수행

**응답 (202 Accepted)**:
```json
{
  "status": "pending",
  "task_id": 123
}
```

---

#### Tasks API

**1. Task 상태 조회**
```http
GET /api/v1/tasks/{task_id}
```

**응답 (200 OK)**:
```json
{
  "id": 123,
  "project_id": 1,
  "target_id": 1,
  "type": "CRAWL",
  "status": "COMPLETED",
  "result": "{\"found_links\": 15, \"saved_assets\": 12}",
  "created_at": "2026-01-04T12:00:00Z",
  "updated_at": "2026-01-04T12:05:00Z"
}
```

---

**2. Task가 발견한 Asset 조회**
```http
GET /api/v1/tasks/{task_id}/assets
```

**응답 (200 OK)**: Asset 배열

---

### API 문서

FastAPI 자동 생성 문서:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 7. 주요 기능

### 1. 프로젝트 관리

**기능**:
- CRUD (Create, Read, Update, Delete)
- Archive/Restore (Soft Delete 패턴)
- 일괄 삭제/복원 (Bulk Operations)

**컴포넌트**:
- `CreateProjectForm.tsx`: Dialog 기반 생성 폼
- `EditProjectForm.tsx`: Dialog 기반 수정 폼
- `DeleteProjectDialog.tsx`: 삭제 확인 Dialog
- `ArchivedDialog.tsx`: Archive 확인
- `RestoreDialog.tsx`: 복원 확인
- `PermanentDeleteDialog.tsx`: 영구 삭제 확인

**프로젝트 목록 표시**:
- Sidebar: 실시간 프로젝트 목록 (체크박스 다중 선택)
- ProjectsPage: 통계 대시보드 (Active/Archived 카운트)
- ActiveProjectsListPage: 활성 프로젝트 카드 그리드
- ArchivedProjectsPage: 아카이브 프로젝트 + 일괄 작업

---

### 2. Target 관리

**기능**:
- Target CRUD
- URL 유효성 검증 (Zod + URL API)
- Scope 설정 (DOMAIN/SUBDOMAIN/URL_ONLY)
- 스캔 트리거

**컴포넌트**:
- `TargetList.tsx`: Table 형식 목록 (스캔 버튼 포함)
- `CreateTargetForm.tsx`: Dialog 기반 생성 폼
- `EditTargetForm.tsx`: Dialog 기반 수정 폼
- `DeleteTargetDialog.tsx`: 삭제 확인 Dialog
- `TargetFormFields.tsx`: 폼 필드 재사용 컴포넌트

**통합**:
- ProjectDetailPage에서 Target 섹션 통합
- 프로젝트 메타데이터 (생성일, 수정일) 표시

---

### 3. 비동기 크롤링

**아키텍처**:
```
FastAPI (API)
    ↓
TaskService.create_scan_task()
    ↓
Redis Queue (RPUSH)
    ↓
Worker (LPOP)
    ↓
CrawlerService.crawl()
    ↓
Playwright Browser
    ↓
AssetService.process_asset()
    ↓
PostgreSQL (Assets 저장)
```

**CrawlerService 동작**:
1. Playwright Chromium 브라우저 런칭
2. `page.goto(url, wait_until="networkidle")` (JS 렌더링 대기)
3. `<a>` 태그 href 속성 추출
4. Set으로 중복 제거 후 반환

**AssetService 동작**:
1. content_hash 생성 (SHA256 of "METHOD:URL")
2. 기존 Asset 존재 확인 (content_hash UNIQUE)
3. 존재 시: `last_seen_at` 업데이트
4. 미존재 시: 신규 Asset 생성
5. AssetDiscovery 이력 레코드 생성

---

### 4. 스캔 결과 추적

**Frontend 폴링**:
```typescript
// useTasks.ts
const { data: task } = useQuery({
  queryKey: taskKeys.detail(taskId),
  queryFn: () => getTaskStatus(taskId),
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

**UI 피드백**:
- ScanStatusBadge: Task 상태 시각화
  - PENDING: 회색 Badge
  - RUNNING: 파란색 Badge (애니메이션)
  - COMPLETED: 녹색 Badge
  - FAILED: 빨간색 Badge

**이력 관리**:
- AssetDiscoveries 테이블로 각 스캔별 발견 Asset 추적
- `parent_asset_id`로 자산 발견 계층 추적

---

## 8. 개발 환경 설정

### Backend (UV 기반)

#### UV란?

**UV (Rust 기반 고속 Python 패키지 매니저)**는 pip, poetry, pipenv를 대체하는 차세대 도구입니다.

**주요 특징**:
- Rust로 작성되어 **10-100배 빠른 패키지 설치 속도**
- pyproject.toml 기반 의존성 관리
- 자동 가상환경 생성 및 관리
- Lock 파일을 통한 재현 가능한 빌드
- 크로스 플랫폼 지원 (macOS, Linux, Windows)

#### UV 설치 (필수)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Homebrew (macOS)
brew install uv

# 설치 확인
uv --version
```

#### 프로젝트 실행

```bash
# 1. 인프라 시작 (PostgreSQL, Redis)
cd backend/docker
docker compose up -d

# 확인
docker ps
# → eazy-postgres (5432)
# → eazy-redis (6379)

# 2. 의존성 설치 (UV로 자동 venv 생성)
cd ..
uv sync

# 3. DB 마이그레이션
uv run alembic upgrade head

# 4. 서버 실행
uv run uvicorn app.main:app --reload
# → http://localhost:8000
# → Swagger UI: http://localhost:8000/docs

# 5. Worker 실행 (별도 터미널)
uv run python -m app.worker

# 6. 테스트
uv run pytest

# 7. 코드 포맷팅
uv run black .
uv run isort .

# 8. 타입 체크
uv run mypy .
```

#### 주요 UV 명령어

```bash
# 의존성 설치 (pyproject.toml 기반)
uv sync

# 패키지 추가
uv add <package-name>
uv add --dev <dev-package>  # 개발 의존성

# 패키지 제거
uv remove <package-name>

# venv 내에서 명령 실행
uv run <command>

# Python REPL
uv run python

# 설치된 패키지 목록
uv pip list

# Lock 파일 생성 (자동)
uv lock

# venv 경로 확인
uv venv --path
```

#### 환경 변수 설정

`.env` 파일 생성 (backend 루트):
```bash
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=eazy_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security (변경 필수)
SECRET_KEY=CHANGE_THIS_TO_A_SECURE_KEY_IN_PRODUCTION
ACCESS_TOKEN_EXPIRE_MINUTES=11520  # 8 days
```

---

### Frontend

#### 의존성 설치

```bash
cd frontend
npm install
```

#### 개발 서버

```bash
npm run dev
# → http://localhost:5173
```

#### 테스트

```bash
# 단위 테스트 실행
npm run test

# Watch 모드
npm run test:watch

# 커버리지
npm run test:coverage
```

#### 빌드

```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

#### Storybook

```bash
# Storybook 개발 서버
npm run storybook
# → http://localhost:6006

# Storybook 빌드
npm run build-storybook
```

#### 코드 포맷팅

```bash
# Prettier
npm run format

# ESLint
npm run lint
```

#### 환경 변수 설정

`.env` 파일 생성 (frontend 루트):
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 9. 개발 컨벤션

### Git Convention

#### 브랜치 전략
- **Trunk-based Development / GitHub Flow**
- `main`: 배포 가능한 안정 상태
- `feat/*`: 기능 개발 브랜치
- 현재 작업: `feature/redesign` (MVP 개발 중)

#### Commit 규칙 (Conventional Commits)

```bash
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅 (코드 변경 없음)
refactor: 코드 리팩토링
test: 테스트 코드 추가
chore: 빌드 업무, 패키지 수정
```

**Commit 메시지 형식**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**예시**:
```bash
feat(frontend): implement ProjectDetailPage Target integration

- Add TargetList component with scan trigger
- Integrate CreateTargetForm dialog
- Add Task status polling (5s interval)
- Write 28 comprehensive tests (TDD GREEN)

Closes #42
```

---

### Backend (Python/FastAPI)

#### 코딩 스타일
- **PEP 8** 준수
- **Black** 포맷터 (최대 88자)
- **isort** (import 정렬)
- **ruff** (린터)
- **mypy Strict Mode** (타입 체크)

#### 필수 규칙

```python
# ✅ Good: Type Hint 필수
async def get_user(user_id: int, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# ❌ Bad: Type Hint 없음
async def get_user(user_id, db):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

#### 레이어 분리

```
api/         → Router만 담당 (비즈니스 로직 금지)
services/    → 비즈니스 로직 (DB 접근은 간접적으로)
models/      → SQLModel 정의
core/        → 설정, 유틸리티
```

**예시 (올바른 레이어 분리)**:
```python
# api/v1/endpoints/project.py
@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """비즈니스 로직은 Service Layer에 위임"""
    return await ProjectService.create_project(db, project)

# services/project_service.py
class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
        """실제 비즈니스 로직"""
        project = Project(**data.model_dump())
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
```

---

### Frontend (React/TypeScript)

#### 코딩 스타일
- **Prettier** 포맷터 (2 Spaces)
- **ESLint** 린터
- **TypeScript Strict Mode**

#### 파일 명명 규칙

```
MyComponent.tsx      # PascalCase (컴포넌트)
utils.ts             # camelCase (일반 파일)
projectService.ts    # camelCase (서비스)
use-mobile.tsx       # kebab-case (hooks, shadcn 규칙)
```

#### 컴포넌트 구조

```
components/ui/       # shadcn/ui 기본 컴포넌트 (Atoms)
components/features/ # 비즈니스 로직 컴포넌트 (Molecules/Organisms)
components/layout/   # 레이아웃 컴포넌트
pages/               # 라우팅 페이지 (Templates)
```

#### Presentation & Container 패턴

**권장**: 로직(Hooks)과 뷰(JSX) 분리

```typescript
// TargetFormFields.tsx (Presentation - 재사용 가능)
export function TargetFormFields({ form }: { form: UseFormReturn<TargetFormValues> }) {
  return (
    <>
      <FormField name="name" control={form.control} render={...} />
      <FormField name="url" control={form.control} render={...} />
      <FormField name="scope" control={form.control} render={...} />
    </>
  );
}

// CreateTargetForm.tsx (Container - 로직 포함)
export function CreateTargetForm() {
  const form = useForm({ resolver: zodResolver(targetFormSchema) });
  const createTarget = useCreateTarget();

  const onSubmit = async (data) => {
    await createTarget.mutateAsync(data);
  };

  return (
    <Dialog>
      <Form {...form}>
        <TargetFormFields form={form} />
      </Form>
    </Dialog>
  );
}
```

---

### 보안 규칙

1. **.env 파일 절대 커밋 금지** (Git에서 제외)
2. **SQL Injection 방지**: ORM(SQLModel) 사용 필수
3. **Input Validation**: Pydantic(백엔드), Zod(프론트엔드)
4. **XSS 방지**: React는 기본적으로 XSS 방지 (dangerouslySetInnerHTML 금지)
5. **CORS 설정**: FastAPI CORS Middleware (프로덕션에서는 특정 도메인만 허용)

---

## 10. 테스트 전략

### TDD (Test-Driven Development)

**RED → GREEN → REFACTOR** 사이클 엄격 준수

```
1. RED: 테스트 작성 (실패)
2. GREEN: 최소한의 코드로 테스트 통과
3. REFACTOR: 코드 개선 (테스트는 여전히 통과)
```

**증거**:
- Frontend 168/168 테스트 통과 (Phase 3 완료 기준)
- 모든 컴포넌트는 테스트 먼저 작성 → 구현 순서

---

### Backend 테스트

#### 프레임워크
- **Pytest** (단위 테스트, 통합 테스트)
- **Pytest-asyncio** (비동기 테스트)
- **Pytest-cov** (커버리지)

#### 테스트 구조 (11개 파일)

```
tests/
├── conftest.py              # Pytest Fixtures
├── api/
│   ├── test_health.py       # 헬스체크 API
│   ├── test_projects.py     # Project CRUD (8개 테스트)
│   ├── test_targets.py      # Target CRUD
│   ├── test_targets_mgmt.py # Target 관리
│   └── test_tasks.py        # Task API (3개 테스트)
├── core/
│   ├── test_task_manager.py # Redis Queue 테스트
│   └── test_worker.py       # Worker 로직 테스트
├── services/
│   ├── test_crawler.py      # Crawler 단위 테스트 (Mock)
│   └── test_asset_service.py # Asset 처리 로직
└── integration/
    └── test_full_flow.py    # 전체 스캔 플로우 통합 테스트
```

#### 주요 Fixtures

```python
# tests/conftest.py

@pytest.fixture
async def db_session() -> AsyncSession:
    """
    각 테스트마다 DB 클린업:
    - DELETE FROM asset_discoveries
    - DELETE FROM assets
    - DELETE FROM tasks
    - DELETE FROM targets
    - DELETE FROM projects
    """
    # ... (설정 생략)

@pytest.fixture
async def client(db_session, redis_client) -> AsyncClient:
    """
    FastAPI 테스트 클라이언트
    - dependency_overrides로 DB/Redis 주입
    """
    # ... (설정 생략)
```

#### 테스트 예시

```python
# tests/api/test_projects.py

async def test_create_project(client):
    """프로젝트 생성 테스트"""
    response = await client.post("/api/v1/projects/", json={
        "name": "Test Project",
        "description": "Test Description"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["is_archived"] is False

async def test_archive_project(client, db_session):
    """프로젝트 Archive (Soft Delete) 테스트"""
    # 1. 프로젝트 생성
    project = await ProjectService.create_project(...)

    # 2. Archive
    response = await client.delete(f"/api/v1/projects/{project.id}")
    assert response.status_code == 204

    # 3. DB 확인
    archived = await db_session.get(Project, project.id)
    assert archived.is_archived is True
    assert archived.archived_at is not None
```

#### Mocking 전략

```python
# Crawler Mock (네트워크 호출 방지)
from unittest.mock import patch

with patch("app.services.crawler_service.CrawlerService.crawl") as mock_crawl:
    mock_crawl.return_value = [
        "http://example.com/page1",
        "http://example.com/page2"
    ]
    # 테스트 실행
```

#### 실행 방법

```bash
# 전체 테스트
uv run pytest

# 특정 파일
uv run pytest tests/api/test_projects.py

# 특정 테스트
uv run pytest tests/api/test_projects.py::test_create_project

# 커버리지
uv run pytest --cov=app --cov-report=html

# Verbose 모드
uv run pytest -v
```

---

### Frontend 테스트

#### 프레임워크
- **Vitest** (테스트 러너)
- **React Testing Library** (컴포넌트 테스트)
- **Jest DOM** (매처)

#### 테스트 구조 (16개 파일)

```
frontend/src/
├── components/features/
│   ├── project/
│   │   ├── CreateProjectForm.test.tsx
│   │   ├── EditProjectForm.test.tsx
│   │   └── DeleteProjectDialog.test.tsx
│   └── target/
│       ├── CreateTargetForm.test.tsx
│       ├── EditTargetForm.test.tsx
│       ├── TargetList.test.tsx
│       └── DeleteTargetDialog.test.tsx
├── components/layout/
│   └── Sidebar.test.tsx
├── pages/
│   └── ProjectDetailPage.test.tsx
├── services/
│   ├── projectService.test.ts
│   ├── targetService.test.ts
│   └── taskService.test.ts
├── schemas/
│   └── targetSchema.test.ts
└── lib/
    └── api.test.ts
```

#### 테스트 통계

| 카테고리 | 파일 수 | 테스트 수 |
|---------|--------|---------|
| Component | 10개 | 120+ |
| Service | 3개 | 36개 |
| Schema | 1개 | 6개 |
| API | 1개 | 6개 |
| **Total** | **16개** | **168개** |

#### 테스트 예시

```typescript
// CreateProjectForm.test.tsx

describe('CreateProjectForm', () => {
  it('should create project successfully', async () => {
    const user = userEvent.setup();
    render(<CreateProjectForm />);

    // 1. Dialog 열기
    const trigger = screen.getByRole('button', { name: /create project/i });
    await user.click(trigger);

    // 2. 폼 입력
    const nameInput = screen.getByLabelText(/name/i);
    await user.type(nameInput, 'New Project');

    const descInput = screen.getByLabelText(/description/i);
    await user.type(descInput, 'Test Description');

    // 3. Submit
    const submitBtn = screen.getByRole('button', { name: /create/i });
    await user.click(submitBtn);

    // 4. API 호출 확인
    await waitFor(() => {
      expect(mockCreateProject).toHaveBeenCalledWith({
        name: 'New Project',
        description: 'Test Description'
      });
    });
  });

  it('should show validation error for invalid input', async () => {
    const user = userEvent.setup();
    render(<CreateProjectForm />);

    // ... (Zod 유효성 검증 테스트)
  });
});
```

#### Mock 설정

```typescript
// vitest.setup.ts

// 1. ResizeObserver Mock (ScrollArea 컴포넌트용)
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}));

// 2. TanStack Query Mock
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false }
  }
});
```

#### 실행 방법

```bash
# 전체 테스트
npm run test

# Watch 모드
npm run test:watch

# 특정 파일
npm run test CreateProjectForm.test.tsx

# UI 모드
npm run test:ui

# 커버리지
npm run test:coverage
```

---

### Storybook 통합 테스트

**총 Stories**: 47개 (모든 UI 컴포넌트)

```bash
# Storybook 서버
npm run storybook

# Storybook + Vitest 통합
npm run test:storybook

# Playwright 브라우저 테스트
npm run test:storybook:e2e
```

**자동 시각적 회귀 테스트** 가능 (Chromatic 연동 시)

---

### 테스트 Coverage 목표

- Backend: **≥80%**
- Frontend: **≥80%**

현재 주요 기능은 100% 커버리지 (TDD 적용)

---

## 11. Claude 에이전트 시스템

### 에이전트 구성

`.claude/agents/` 디렉토리에 **17개 전문 에이전트** 구성:

| 에이전트 | 역할 |
|---------|------|
| **api-designer** | API 아키텍처 설계 (REST, OpenAPI 3.1) |
| **architect-reviewer** | 시스템 아키텍처 검토 |
| **backend-developer** | Python/FastAPI 백엔드 개발 |
| **code-reviewer** | 코드 리뷰 자동화 (보안, 성능, 스타일) |
| **feature-planner** | 기능 계획 수립 (Phase 기반) |
| **frontend-developer** | React 프론트엔드 개발 |
| **git-workflow-manager** | Git 워크플로우 관리 |
| **python-pro** | Python 전문가 (타입 힌트, 비동기) |
| **react-specialist** | React 전문가 (Hooks, 성능 최적화) |
| **sql-pro** | SQL 및 데이터베이스 전문가 |
| **task-distributor** | 작업 분배 조정자 |
| **technical-writer** | 기술 문서 작성 |
| **typescript-pro** | TypeScript 전문가 |
| **ui-designer** | UI 디자인 검토 |
| **ux-researcher** | UX 분석 |
| **websocket-engineer** | WebSocket 통신 전문가 |
| **react-flow-specialist** | React Flow 시각화 전문가 |

### 에이전트 협업 예시

**Task 4.22 (ProjectDetailPage 구현)**:
```
1. typescript-pro       → 컴포넌트 구현
2. ui-designer          → UI 검토 (8.5/10 평가)
3. ux-researcher        → UX 검토 (8.5/10 평가)
```

### 설정 파일

```json
// .claude/settings.local.json
{
  "outputStyle": "default",
  "spinnerTipsEnabled": false,
  "statusLine": {
    "type": "command",
    "command": "~/.claude/scripts/context-bar.sh"
  }
}
```

---

## 12. 현재 진행 상황

### 전체 MVP 진행률: **82%**

#### Backend MVP: **80% 완료**

**완료된 Phase**:
- ✅ **Phase 1**: Backend 인프라 구축 (FastAPI, DB, Redis)
- ✅ **Phase 2**: 프로젝트 관리 API (Project CRUD)
- ✅ **Phase 3**: 공격 표면 탐지 엔진 (Crawler, Asset Service)
- ✅ **Phase 4**: 비동기 작업 API (Task Queue, Worker)
- ✅ **Phase 5**: 타겟 관리 개선 (Update/Delete API)

**남은 작업**:
- Phase 6: Asset API 및 결과 조회 엔드포인트
- Phase 7: LLM 분석 모듈 통합 (추후)

---

#### Frontend MVP: **85% 완료**

**완료된 Phase**:
- ✅ **Phase 1**: 프로젝트 초기화 (Vite, TypeScript, TailwindCSS)
- ✅ **Phase 2**: 레이아웃 & 디자인 시스템 (Sidebar, Header, 93개 shadcn 컴포넌트)
- ✅ **Phase 3**: 프로젝트 CRUD (**168개 테스트 통과**)
- 🔄 **Phase 4**: 프로젝트 상세 페이지 & Target 관리 (85% 완료)
  - ✅ Step 1: Backend API 및 기반 구조
  - ✅ Step 2: Target 폼 컴포넌트 (Create/Edit)
  - ✅ Step 3: Delete Dialog & TargetList
  - ✅ Step 4: ProjectDetailPage 통합 (**28/28 테스트 통과**)

**남은 작업**:
- Phase 5: 대시보드 & 스캔 결과 (Asset Table 시각화)
  - Asset 목록 테이블 컴포넌트
  - React Flow 기반 Business Logic Map

---

### 최근 커밋

```
9b9ed19 docs(plan): update PLAN_MVP_Frontend.md - Phase 4 Task 4.22 completed
64c2fd6 feat(frontend): implement ProjectDetailPage Target integration (TDD GREEN)
ea9dc53 docs(plan): update PLAN_MVP_Frontend.md - Phase 4 Test 4.21 completed
f67bd35 test(frontend): add ProjectDetailPage extension tests (TDD RED)
36955f9 feat(ui): implement Target components UI improvements
```

---

## 13. 주요 파일 경로

### 문서

- `/Users/lrtk/Documents/Project/EAZY/README.md` - 프로젝트 개요
- `/Users/lrtk/Documents/Project/EAZY/docs/PRD.md` - 제품 요구사항 정의서
- `/Users/lrtk/Documents/Project/EAZY/docs/db_schema.md` - 데이터베이스 스키마
- `/Users/lrtk/Documents/Project/EAZY/docs/api_spec.md` - API 명세
- `/Users/lrtk/Documents/Project/EAZY/docs/coding_convention.md` - 코딩 컨벤션
- `/Users/lrtk/Documents/Project/EAZY/docs/plans/PLAN_MVP_Backend.md` - 백엔드 MVP 계획
- `/Users/lrtk/Documents/Project/EAZY/docs/plans/frontend/INDEX.md` - 프론트엔드 MVP 메인 인덱스
- `/Users/lrtk/Documents/Project/EAZY/docs/plans/frontend/PHASE5_CURRENT.md` - 현재 진행 중인 Phase

### Backend 핵심

- `/Users/lrtk/Documents/Project/EAZY/backend/app/main.py` - FastAPI 앱
- `/Users/lrtk/Documents/Project/EAZY/backend/app/worker.py` - Redis Worker
- `/Users/lrtk/Documents/Project/EAZY/backend/app/services/crawler_service.py` - Playwright 크롤러
- `/Users/lrtk/Documents/Project/EAZY/backend/app/core/config.py` - 환경 설정
- `/Users/lrtk/Documents/Project/EAZY/backend/pyproject.toml` - UV 의존성
- `/Users/lrtk/Documents/Project/EAZY/backend/docker/docker-compose.yml` - PostgreSQL + Redis

### Frontend 핵심

- `/Users/lrtk/Documents/Project/EAZY/frontend/src/App.tsx` - 라우팅
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/main.tsx` - React 진입점
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/pages/ProjectDetailPage.tsx` - 프로젝트 상세
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/components/layout/Sidebar.tsx` - 사이드바
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/hooks/useProjects.ts` - Query 훅
- `/Users/lrtk/Documents/Project/EAZY/frontend/src/services/projectService.ts` - API 클라이언트
- `/Users/lrtk/Documents/Project/EAZY/frontend/package.json` - npm 의존성

### Claude 에이전트

- `/Users/lrtk/Documents/Project/EAZY/.claude/settings.local.json` - 에이전트 설정
- `/Users/lrtk/Documents/Project/EAZY/.claude/agents/` - 17개 전문 에이전트

---

## 부록

### A. 용어집

- **DAST**: Dynamic Application Security Testing (동적 애플리케이션 보안 테스팅)
- **Business Logic Vulnerability**: 비즈니스 로직 취약점 (인증 우회, 권한 상승 등)
- **Soft Delete**: 논리 삭제 (is_archived 플래그 사용)
- **TDD**: Test-Driven Development (테스트 주도 개발)
- **Atomic Design**: UI 컴포넌트 설계 방법론 (Atoms → Molecules → Organisms → Templates → Pages)
- **UV**: Rust 기반 고속 Python 패키지 매니저

### B. 참고 자료

**Backend**:
- FastAPI 공식 문서: https://fastapi.tiangolo.com/
- SQLModel 공식 문서: https://sqlmodel.tiangolo.com/
- Playwright 공식 문서: https://playwright.dev/python/
- UV 공식 문서: https://github.com/astral-sh/uv

**Frontend**:
- React 공식 문서: https://react.dev/
- TanStack Query: https://tanstack.com/query/latest
- shadcn/ui: https://ui.shadcn.com/
- Vitest: https://vitest.dev/

---

**문서 끝**

*이 문서는 Claude 에이전트 시스템을 통해 자동 생성되었으며, 프로젝트 진행 상황에 따라 지속적으로 업데이트됩니다.*
