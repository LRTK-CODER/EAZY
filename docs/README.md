# EAZY 프로젝트 문서

> AI 기반 지능형 동적 애플리케이션 보안 테스팅(DAST) 도구

**EAZY**는 LLM을 활용해 웹 애플리케이션의 비즈니스 로직 취약점을 탐지하는 AI 기반 DAST 도구입니다.

**최종 업데이트**: 2026-01-09
**프로젝트 버전**: 0.1.0 (MVP)

---

## ⚡️ Quick Reference

### 핵심 기술 스택
```
Backend:  Python 3.12 + FastAPI + SQLModel + PostgreSQL + Redis + Playwright
Frontend: React 19 + TypeScript + Vite + TailwindCSS + shadcn/ui + TanStack Query
패키지:   UV (Backend - 필수), npm (Frontend)
```

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
```

→ **상세 가이드**: [빠른 시작 (5분)](#quick-start) | [환경 설정](setup/ENVIRONMENT_SETUP.md)

---

## 📍 문서 네비게이션

### 신규 사용자 (Getting Started)
1. **[빠른 시작 (5분)](QUICK_START.md)** - 로컬 환경에서 프로젝트 실행하기
2. **[환경 설정](setup/)** - 개발 환경 구축 상세 가이드
   - [Backend 설정](setup/BACKEND_SETUP.md) - UV, PostgreSQL, Redis
   - [Frontend 설정](setup/FRONTEND_SETUP.md) - npm, Vite
   - [Docker 설정](setup/DOCKER_SETUP.md) - 컨테이너 구성
   - [문제 해결](setup/TROUBLESHOOTING.md) - 자주 하는 실수 & 해결책
3. **[프로젝트 개요](reference/PROJECT_OVERVIEW.md)** - EAZY가 무엇인가?

### 기존 개발자 (Daily Development)
- **[개발 가이드](development/)** - 개발 시 참고 문서
  - [TDD 가이드](development/TDD_GUIDE.md) - RED → GREEN → REFACTOR
  - [테스트 전략](development/TESTING_STRATEGY.md) - Backend/Frontend 테스트
  - [Git 워크플로우](development/GIT_WORKFLOW.md) - Commit 규칙 & PR
  - [Backend 개발](development/BACKEND_DEVELOPMENT.md) - 레이어 분리 & 패턴
  - [Frontend 개발](development/FRONTEND_DEVELOPMENT.md) - Atomic Design
  - [배포 가이드](development/DEPLOYMENT.md) - 프로덕션 빌드
- **[계획 문서](plans/)** - 현재 진행 중인 작업
  - [Frontend MVP](plans/mvp-plans/INDEX.md) - 프론트엔드 MVP 진행 상황
  - [현재 Phase](plans/mvp-plans/PHASE5_CURRENT.md) - 진행 중인 작업
  - [학습 노트](plans/mvp-plans/NOTES.md) - 개발 이력

### 아키텍트/설계 (Design & Planning)
- **[기준 문서](reference/)** - 아키텍처 및 기술 스택
  - [시스템 아키텍처](reference/ARCHITECTURE.md) - Backend/Frontend 구조
  - [기술 스택](reference/TECH_STACK.md) - 사용 기술 상세
  - [프로젝트 구조](reference/PROJECT_STRUCTURE.md) - 디렉토리 구조
  - [Claude 에이전트 시스템](reference/AGENT_SYSTEM.md) - 17개 전문 에이전트
- **[코드 리뷰](reviews/)** - 코드 품질 평가
  - [종합 리뷰](reviews/COMPREHENSIVE_REVIEW.md) - 전체 평가 보고서
  - [코드 리뷰](reviews/CODE_REVIEW_2026-01-08.md) - 상세 코드 리뷰
  - [아키텍처 리뷰](reviews/ARCHITECTURE_REVIEW_2026-01-08.md) - 아키텍처 평가

### API 통합 (Frontend/Backend)
- **[API 명세](reference/api_spec.md)** - REST API 엔드포인트
- **[데이터베이스 스키마](reference/db_schema.md)** - ERD 및 테이블 구조
- **[코딩 컨벤션](reference/coding_convention.md)** - Backend/Frontend 규칙

### 품질 & 테스트 (QA/Testing)
- **[테스트 전략](development/TESTING_STRATEGY.md)** - TDD 기반 테스트
- **[TDD 가이드](development/TDD_GUIDE.md)** - RED-GREEN-REFACTOR
- **[코드 리뷰](reviews/CODE_REVIEW_2026-01-08.md)** - 품질 체크리스트

---

## 🗂️ 데이터 모델 요약

```
PROJECT (1) ──< (N) TARGET (1) ──< (N) TASK (1) ──< (N) ASSET
    │                │                  │               │
    │                │                  │               └─ 공격 표면 (URL, FORM, XHR)
    │                │                  └─ 비동기 작업 (PENDING → RUNNING → COMPLETED/FAILED)
    │                └─ 스캔 대상 (scope: DOMAIN/SUBDOMAIN/URL_ONLY)
    └─ 프로젝트 (is_archived: Soft Delete)
```

**상세 정보**: [데이터베이스 스키마](reference/db_schema.md)

---

## 🚀 API 엔드포인트 요약

### Projects
```
POST   /api/v1/projects/              # 생성
GET    /api/v1/projects/              # 목록 (archived=true/false)
GET    /api/v1/projects/{id}          # 조회
PATCH  /api/v1/projects/{id}          # 수정
DELETE /api/v1/projects/{id}          # Archive (Soft Delete)
DELETE /api/v1/projects/{id}?permanent=true  # 영구 삭제
```

### Targets
```
POST   /api/v1/projects/{id}/targets/ # 생성
GET    /api/v1/projects/{id}/targets/ # 목록
PATCH  /api/v1/projects/{id}/targets/{tid}  # 수정
DELETE /api/v1/projects/{id}/targets/{tid}  # 삭제
POST   /api/v1/projects/{id}/targets/{tid}/scan  # 스캔 트리거 (202 Accepted)
```

### Tasks
```
GET    /api/v1/tasks/{id}             # 상태 조회
GET    /api/v1/tasks/{id}/assets      # 발견된 Asset 목록
```

**상세 정보**: [API 명세](reference/api_spec.md)

---

## 🧪 테스트 현황

| 영역 | 파일 수 | 테스트 수 | 상태 |
|------|--------|----------|------|
| **Frontend** | 16개 | 168개 | ✅ 모두 통과 |
| **Backend** | 11개 | 다수 | ✅ 모두 통과 |

**커버리지 목표**: ≥80% (현재 주요 기능 100% 커버리지)

**테스트 실행**:
```bash
# Backend
uv run pytest

# Frontend
npm run test
```

**상세 정보**: [테스트 전략](development/TESTING_STRATEGY.md)

---

## 📈 현재 진행 상황

| 영역 | 진행률 | 현재 Phase | 다음 작업 |
|------|--------|-----------|----------|
| **Backend** | 80% | Phase 4 완료 | Asset API 엔드포인트 |
| **Frontend** | 85% | Phase 4 완료 | Phase 5: Asset 시각화 |

**상세 정보**: [계획 문서](plans/)

---

## ⚙️ 필수 개발 규칙

1. **TDD 엄격 준수**: RED → GREEN → REFACTOR (테스트 먼저 작성)
2. **UV 필수 사용**: Python 실행 시 반드시 `uv run` 사용 (pip 금지)
3. **Type Hint 필수**: Backend(mypy), Frontend(TypeScript strict)
4. **Conventional Commits**: `feat:`, `fix:`, `test:`, `docs:` 등 prefix 사용
5. **한국어 커뮤니케이션**: 사용자와 대화는 한국어로

**상세 정보**: [코딩 컨벤션](reference/coding_convention.md)

---

## 🚫 자주 하는 실수 방지

| ❌ 잘못된 방법 | ✅ 올바른 방법 |
|--------------|--------------|
| `pip install <package>` | `uv add <package>` 또는 `uv sync` |
| `python script.py` | `uv run python script.py` |
| 테스트 없이 구현 | 테스트 먼저 작성 (TDD) |
| 영어로 대화 | 한국어로 대화 |

**상세 정보**: [문제 해결 가이드](setup/TROUBLESHOOTING.md)

---

## 📚 참고 자료

### Backend
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLModel 공식 문서](https://sqlmodel.tiangolo.com/)
- [Playwright 공식 문서](https://playwright.dev/python/)
- [UV 공식 문서](https://github.com/astral-sh/uv)

### Frontend
- [React 공식 문서](https://react.dev/)
- [TanStack Query](https://tanstack.com/query/latest)
- [shadcn/ui](https://ui.shadcn.com/)
- [Vitest](https://vitest.dev/)

**전체 목록**: [참고자료](reference/RESOURCES.md)

---

## 📖 용어집

| 용어 | 설명 |
|------|------|
| **DAST** | Dynamic Application Security Testing (동적 애플리케이션 보안 테스팅) |
| **Business Logic Vulnerability** | 비즈니스 로직 취약점 (인증 우회, 권한 상승 등) |
| **Soft Delete** | 논리 삭제 (is_archived 플래그 사용) |
| **TDD** | Test-Driven Development (테스트 주도 개발) |
| **UV** | Rust 기반 고속 Python 패키지 매니저 |

**전체 목록**: [용어집](reference/GLOSSARY.md)

---

## 📜 라이선스

Apache License 2.0

---

## 📌 주요 문서 링크

### 기준 문서 (Reference)
- [프로젝트 개요](reference/PROJECT_OVERVIEW.md)
- [기술 스택](reference/TECH_STACK.md)
- [프로젝트 구조](reference/PROJECT_STRUCTURE.md)
- [아키텍처](reference/ARCHITECTURE.md)
- [Claude 에이전트 시스템](reference/AGENT_SYSTEM.md)
- [API 명세](reference/api_spec.md)
- [데이터베이스 스키마](reference/db_schema.md)
- [코딩 컨벤션](reference/coding_convention.md)
- [용어집](reference/GLOSSARY.md)
- [참고자료](reference/RESOURCES.md)

### 환경 설정 (Setup)
- [개발 환경 구축](setup/ENVIRONMENT_SETUP.md)
- [Backend 설정](setup/BACKEND_SETUP.md)
- [Frontend 설정](setup/FRONTEND_SETUP.md)
- [Docker 설정](setup/DOCKER_SETUP.md)
- [문제 해결](setup/TROUBLESHOOTING.md)

### 개발 가이드 (Development)
- [TDD 가이드](development/TDD_GUIDE.md)
- [테스트 전략](development/TESTING_STRATEGY.md)
- [Git 워크플로우](development/GIT_WORKFLOW.md)
- [Backend 개발](development/BACKEND_DEVELOPMENT.md)
- [Frontend 개발](development/FRONTEND_DEVELOPMENT.md)
- [배포 가이드](development/DEPLOYMENT.md)

### 계획 & 리뷰
- [계획 문서](plans/)
- [코드 리뷰](reviews/)

---

**문서 끝**

> 💡 **Tip**: 처음 시작하시나요? [빠른 시작 (5분)](QUICK_START.md) 가이드를 참고하세요!
