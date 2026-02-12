# EAZY - AI 기반 블랙박스 모의해킹 도구

## 1. 프로젝트 개요
- **목적**: 웹 애플리케이션 대상 AI 기반 블랙박스 모의해킹 도구. 공격자 관점에서 취약점을 자동 탐지 및 검증한다.
- **핵심 기능**: 스마트 크롤링 + AI 공격 시나리오 생성 + 오탐 필터링 + 자동 리포팅
- **PRD**: `plan/PRD.md`
- **구현 계획**: `plan/TASK.md`

## 2. 기술 스택 및 환경

### 백엔드 (Python 3.12.10)
| 항목 | 기술 |
|------|------|
| 패키지 매니저 | **uv** |
| CLI 프레임워크 | Click / Typer |
| 백엔드 프레임워크 | FastAPI |
| 비동기 작업 큐 | Celery + Redis |
| HTTP 클라이언트 | httpx |
| 데이터 모델 | Pydantic v2 |
| 크롤링 | Playwright (Phase 2) |
| AI/LLM | Gemini API + LiteLLM |
| 벡터 DB | Qdrant |
| 데이터베이스 | PostgreSQL 15+ |
| 리포트 | WeasyPrint / Jinja2 |
| 린팅/포맷팅 | Ruff |
| 테스트 | pytest, pytest-asyncio, pytest-cov, respx |

### 프론트엔드 (Node.js 20 LTS)
| 항목 | 기술 |
|------|------|
| 패키지 매니저 | **pnpm** |
| 프레임워크 | React + Next.js (App Router) |
| 린팅 | ESLint + Prettier |
| 테스트 | Vitest |

## 3. 개발 우선순위
- **Phase 1 (v0.1)**: CLI 기반 기본 진단 - REQ-001, 010, 004-basic, 009, 008-basic
- **Phase 2 (v0.5)**: AI 기능 통합 - REQ-002A/B, 003, 004-AI, 005A/B, 007
- **Phase 3 (v1.0)**: 대시보드 + 완전한 기능 - REQ-006, 011, Dashboard, OWASP 전체 커버리지

## 4. 프로젝트 구조
```
EAZY/
├── src/
│   ├── eazy/                     # Python 백엔드 + CLI 패키지
│   │   ├── cli/                  # CLI 인터페이스 (Click/Typer) [REQ-009]
│   │   ├── core/                 # 공통 유틸리티, 설정, 로깅
│   │   ├── models/               # Pydantic 데이터 모델
│   │   ├── crawler/              # 크롤링 엔진 [REQ-001, 002]
│   │   ├── scanner/              # 취약점 스캐너 [REQ-004, 010]
│   │   ├── api/                  # FastAPI REST API (Phase 2+)
│   │   ├── workers/              # Celery 워커 (Phase 2+)
│   │   ├── ai/                   # LLM 통합 (Phase 2+)
│   │   ├── rag/                  # RAG 지식 관리 (Phase 2+)
│   │   └── report/               # 리포트 생성 (Phase 3)
│   └── frontend/                 # Next.js 대시보드 (Phase 3)
│       ├── src/
│       │   ├── app/              # App Router 페이지
│       │   └── components/       # 재사용 컴포넌트
│       └── public/
├── tests/                        # Python 테스트
│   ├── conftest.py
│   ├── unit/
│   │   ├── models/
│   │   └── crawler/
│   └── integration/
│       └── crawler/
└── plan/                         # 기획 문서
```

## 5. 코딩 스타일 및 컨벤션

### Python
- PEP 8 준수, Ruff로 강제
- 모든 함수 시그니처에 타입 힌트 필수
- 변수/함수는 `snake_case`, 클래스는 `PascalCase`
- 모든 I/O 작업에 `async/await` 사용
- 모든 데이터 모델에 Pydantic v2 사용

### TypeScript (Phase 3)
- ESLint + Prettier 강제
- 함수형 컴포넌트만 사용 (클래스 컴포넌트 금지)
- Next.js App Router
- 컴포넌트는 `PascalCase`, 변수는 `camelCase`
- `@/` 접두사로 절대 경로 임포트

### 공통
- Conventional Commits (`feat:`, `fix:`, `test:`, `chore:`, `refactor:`, `docs:`)
- GitHub Flow 브랜칭 (`feature/req-XXX-description`)
- 용어 통일 (예: "크롤링 엔진"으로 통일, "크롤러/스파이더" 사용 금지)

## 6. 자주 사용하는 명령어

### Python (백엔드/CLI)
```bash
uv run pytest                                              # 테스트 실행
uv run pytest --cov=src/eazy --cov-report=term-missing     # 커버리지 포함 테스트
uv run ruff check src/ tests/                              # 린팅
uv run ruff format src/ tests/                             # 포맷팅
uv run ruff check --fix src/ tests/                        # 린트 자동 수정
```

### 프론트엔드 (Phase 3)
```bash
cd src/frontend && pnpm install    # 의존성 설치
cd src/frontend && pnpm dev        # 개발 서버
cd src/frontend && pnpm build      # 프로덕션 빌드
cd src/frontend && pnpm test       # 테스트 실행
```

## 7. 핵심 지침
- **TDD 엄격 준수**: RED -> GREEN -> REFACTOR 사이클. 실패하는 테스트를 먼저 작성하고, 그 다음 구현한다.
- **테스트 커버리지**: 항상 80% 이상 유지
- **보안 도구 특성**: 안전한 페이로드 가이드라인 준수 - 대상에 파괴적인 페이로드를 절대 전송하지 않는다
- **Phase 1 오프라인**: Phase 1은 LLM API 없이 동작해야 한다 (AI 네트워크 의존성 없음)
- **CLI 우선**: 1차 인터페이스는 CLI; API 서버와 대시보드는 이후 Phase에서 구현
- **아키텍처**:
  - CLI -> 백엔드: 직접 Python 모듈 호출 (같은 프로세스)
  - 대시보드 -> 백엔드: REST API (Phase 3)
  - 비동기 처리: Celery + Redis (Phase 2+)

## 8. 테스트 컨벤션
```python
# 파일명: test_{모듈명}.py
# 클래스명: Test{컴포넌트명}
# 함수명: test_{행위}_{조건}_{기대결과}
# 예시: test_extract_links_from_empty_html_returns_empty_list
# 패턴: Arrange -> Act -> Assert
```
