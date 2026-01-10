# EAZY 프로젝트 구조 분석 보고서

> **분석 일자:** 2026-01-10
> **분석 방법:** Sequential-Thinking MCP 기반 다중 전문가 토론
> **참여 전문가:** 시스템 아키텍트, 백엔드 아키텍트, 프론트엔드 스페셜리스트, 보안 전문가, DevOps 엔지니어

---

## 1. 프로젝트 개요

**EAZY**는 AI 기반 DAST(Dynamic Application Security Testing) 도구로, Python/FastAPI 백엔드와 React/TypeScript 프론트엔드로 구성된 모노레포 구조입니다.

### 1.1 기술 스택

| 영역 | 기술 |
|------|------|
| **Backend** | Python 3.12, FastAPI, PostgreSQL (JSONB), Redis |
| **Frontend** | React 19, Vite 7, TypeScript 5.9, shadcn/ui |
| **AI Engine** | OpenAI (GPT-4o), Google Gemini, Anthropic Claude |
| **Core Modules** | Playwright, Mitmproxy, HTTPX |

### 1.2 현재 프로젝트 구조

```
EAZY/
├── backend/                 # FastAPI Backend Application
│   ├── app/
│   │   ├── api/            # API Endpoints (v1/endpoints)
│   │   ├── core/           # Core Configurations
│   │   ├── models/         # Database Models
│   │   ├── services/       # Business Logic
│   │   ├── utils/          # Utility Functions
│   │   ├── main.py         # FastAPI Entry Point
│   │   └── worker.py       # Async Worker (11KB)
│   └── tests/              # Pytest Suites
├── frontend/               # React Frontend Application
│   ├── src/
│   │   ├── components/ui/  # 50+ shadcn/ui Components
│   │   ├── types/          # TypeScript Type Definitions
│   │   ├── schemas/        # Zod Validation Schemas
│   │   ├── config/         # Configuration (nav, etc.)
│   │   ├── utils/          # Utilities (date, http)
│   │   ├── tests/          # Test Files
│   │   ├── App.tsx         # Main App Component
│   │   └── main.tsx        # Entry Point
│   └── .storybook/         # Storybook Configuration
├── docs/                   # Project Documentation
│   ├── development/        # Development Guides
│   ├── plans/              # Development Plans
│   ├── reference/          # Reference Documents
│   ├── reviews/            # Code/Architecture Reviews
│   └── setup/              # Setup Guides
└── README.md               # Project Overview
```

---

## 2. 전문가별 분석

### 2.1 시스템 아키텍트 분석

**초기 평가:**
- 전형적인 모노레포 구조 채택으로 명확한 관심사 분리
- API 버저닝 적용 (`/api/v1`)
- 현대적 Python/TypeScript 생태계 활용
- 보안 도구 특성상 복잡한 엔진 레이어 필요성 인지

**주요 관찰:**
1. Backend/Frontend/Docs 3분할 구조는 적절
2. 각 레이어 간 의존성이 명확히 분리됨
3. 확장을 위한 기반 구조는 마련되어 있음

---

### 2.2 백엔드 아키텍트 분석

**강점:**
| 항목 | 설명 |
|------|------|
| 레이어드 아키텍처 | API → Service → Model 계층 준수 |
| CORS 미들웨어 | 적용 완료 (MVP용 `*` 설정) |
| 라우터 구조 | `/projects`, `/tasks` 명확한 분리 |
| RESTful 설계 | `/projects/{id}/targets` 네스티드 구조 |

**개선 필요 사항:**

```python
# 현재 main.py 라우터 구조
api_router = APIRouter()
api_router.include_router(project.router, prefix="/projects", tags=["projects"])
api_router.include_router(task.router, tags=["tasks"])
```

1. **`worker.py` 분리 필요** - 11KB 단일 파일은 유지보수 어려움
2. **`engine/` 폴더 미구현** - README에 명시되었으나 실제 구조에 없음
3. **CORS 정책 강화** - 프로덕션에서 `*` → 특정 도메인으로 제한
4. **의존성 주입(DI)** - 명시적 패턴 도입 고려

---

### 2.3 프론트엔드 스페셜리스트 분석

**강점:**
| 항목 | 설명 |
|------|------|
| 현대적 스택 | React 19, Vite 7, TypeScript 5.9 |
| 컴포넌트 시스템 | shadcn/ui + Radix UI (접근성 우수) |
| 테스트 인프라 | Vitest + Storybook + Playwright |
| 타입 안전성 | Zod 스키마로 런타임 검증 |

**주요 의존성 분석:**

```json
{
  "react": "^19.2.0",
  "@tanstack/react-query": "^5.90.16",
  "react-router-dom": "^7.11.0",
  "zod": "^4.2.1",
  "recharts": "^2.15.4"
}
```

**README와 실제 구조 불일치:**

| README 명시 | 실제 상태 | 조치 필요 |
|-------------|----------|----------|
| `pages/` | 미확인 | 구현 필요 |
| `store/` (Zustand) | 미확인 | 구현 필요 |
| `lib/` | 미확인 | utils/로 대체 가능 |
| React Flow | package.json 미포함 | 설치 필요 |

---

### 2.4 보안 전문가 분석

**DAST 도구로서의 핵심 도메인:**

```
1. 공격 표면 식별 ─── Playwright 크롤링 + Mitmproxy 패시브 스캔
2. AI 취약점 분석 ─── 다중 LLM 비즈니스 로직 분석
3. 공격 수행 엔진 ─── 다단계 시나리오 기반 검증
4. 결과 시각화 ──── 공격 경로 맵핑
```

**구조적 권장사항:**

엔진 모듈 분리가 필수적:

```
backend/app/engine/
├── crawler/      # Playwright 기반 크롤러
├── proxy/        # Mitmproxy 연동
├── attack/       # 공격 실행기
└── ai/           # LLM 분석기
```

**잠재적 보안 위험:**

| 위험 | 현재 상태 | 권장 조치 |
|------|----------|----------|
| CORS 정책 | `*` 허용 | 화이트리스트 적용 |
| LLM API 키 | core/config.py | 환경변수 + 암호화 |
| 스캔 권한 | 미확인 | 인증/인가 로직 구현 |

---

### 2.5 DevOps 엔지니어 분석

**개발 환경 구성:**

| 영역 | 구성 |
|------|------|
| Backend | Python 3.12 + venv + FastAPI |
| Frontend | Node.js + npm + Vite + Storybook (포트 6006) |

**문서화 구조 평가:**

```
docs/
├── QUICK_START.md       # ✅ 빠른 시작 가이드
├── README.md            # ✅ 문서 개요
├── api_spec.md          # ✅ API 명세
├── coding_convention.md # ✅ 코딩 컨벤션
├── db_schema.md         # ✅ DB 스키마
├── development/         # ✅ 개발 가이드
├── plans/               # ✅ 개발 계획
├── reference/           # ✅ 참조 문서
├── reviews/             # ✅ 코드/아키텍처 리뷰
└── setup/               # ✅ 설정 가이드
```

**미구현 항목:**

| 항목 | 상태 | 우선순위 |
|------|------|----------|
| Dockerfile | 미확인 | 높음 |
| docker-compose.yml | 미확인 | 높음 |
| CI/CD 파이프라인 | 미확인 | 중간 |
| .env.example | 미확인 | 중간 |
| 모노레포 도구 | 미사용 | 낮음 |

---

## 3. 종합 평가

### 3.1 강점 요약

| 영역 | 평가 |
|------|------|
| **아키텍처** | 명확한 프론트/백엔드 분리, 레이어드 구조 |
| **기술 스택** | 최신 생태계 (React 19, Python 3.12, FastAPI) |
| **타입 안전성** | TypeScript + Zod로 엔드투엔드 검증 |
| **UI 시스템** | shadcn/ui 기반 일관된 디자인 시스템 |
| **문서화** | 체계적인 docs/ 구조 |

### 3.2 개선 영역

| 우선순위 | 항목 | 이유 |
|----------|------|------|
| **높음** | `engine/` 폴더 구조화 | DAST 핵심 로직 분리 필요 |
| **높음** | `worker.py` 리팩토링 | 11KB 단일 파일은 유지보수 어려움 |
| **높음** | Docker 설정 추가 | 배포 및 개발 환경 일관성 |
| **중간** | `pages/`, `store/` 구현 | README와 실제 구조 일치 |
| **중간** | CI/CD 파이프라인 | 자동화된 테스트/배포 |
| **낮음** | CORS 정책 강화 | 프로덕션 전 필수 |

### 3.3 권장 구조 제안

**Backend 권장 구조:**

```
backend/app/
├── api/
│   └── v1/
│       └── endpoints/
├── core/
├── models/
├── services/
├── engine/              # 신규 추가
│   ├── crawler/         # Playwright 크롤러
│   ├── proxy/           # Mitmproxy 연동
│   ├── attack/          # 공격 실행기
│   └── ai/              # LLM 분석기
├── workers/             # worker.py 분리
│   ├── scan_worker.py
│   ├── attack_worker.py
│   └── analysis_worker.py
└── utils/
```

**Frontend 권장 구조:**

```
frontend/src/
├── components/
│   ├── ui/              # shadcn/ui 컴포넌트
│   └── common/          # 공통 컴포넌트
├── pages/               # 신규 추가
│   ├── Dashboard/
│   ├── Projects/
│   ├── Targets/
│   └── Results/
├── store/               # 신규 추가 (Zustand)
│   ├── useProjectStore.ts
│   └── useScanStore.ts
├── features/            # 기능별 모듈
├── hooks/               # 커스텀 훅
├── types/
├── schemas/
├── utils/
└── config/
```

---

## 4. 최종 평가

### 점수: 7.5 / 10

**평가 근거:**
- MVP로서 견고한 기반 구축 완료
- 현대적 기술 스택 선택
- 체계적인 문서화
- 확장을 위한 추가 구조화 필요

### 다음 단계 권장사항

1. **Phase 1:** `engine/` 폴더 생성 및 핵심 로직 분리
2. **Phase 2:** `worker.py` 모듈화
3. **Phase 3:** Frontend `pages/`, `store/` 구현
4. **Phase 4:** Docker 및 CI/CD 설정
5. **Phase 5:** 보안 정책 강화 (CORS, 인증/인가)

---

## 부록: 분석 메타데이터

| 항목 | 값 |
|------|-----|
| 분석 도구 | Sequential-Thinking MCP |
| 분석 단계 | 6단계 |
| 참여 페르소나 | 5명 |
| 분석 파일 수 | 100+ |
| 문서 버전 | 1.0 |
