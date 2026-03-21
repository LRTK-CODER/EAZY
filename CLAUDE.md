# 프로젝트 개요
- **목표:** 웹 앱의 API 흐름·데이터 플로·비즈니스 로직을 Knowledge Graph로 구조화하고, 발견된 취약점을 자동 연계하여 시나리오 기반 공격 체인을 구성·실행하는 LLM 기반 모의해킹 에이전트
- **핵심 기술:** Python 3.11+ · FastAPI · LangChain + LangGraph · LiteLLM · NetworkX · httpx · Playwright · Pydantic · Rich

# 규칙 (Rules)

## 설계 5원칙
1. LLM은 판단만 한다 (HTTP 요청 직접 전송 금지)
2. 도구는 실행만 한다 (전략 결정 금지)
3. Skill은 지식만 제공한다 (런타임 로직 금지)
4. 미들웨어는 상태만 관리한다 (판단 금지)
5. 각 컴포넌트 단일 책임

## 코딩 스타일
- 모든 데이터 모델: Pydantic `BaseModel` 사용 (dict 전달 금지)
- HTTP 클라이언트: 반드시 `httpx` async (`requests` 사용 금지)
- 모든 함수에 타입 힌트 필수
- `async def`가 기본, 동기 함수는 예외적으로만
- 한 함수 = 한 책임
- f-string 사용 (`format()` 아님)

## 네이밍 규칙
- 상수: `UPPER_SNAKE_CASE`
- 변수/함수: `snake_case`
- 클래스: `PascalCase`
- 파일명: `snake_case.py`

## 코드 예시

```python
# ✅ 좋은 예시
from pydantic import BaseModel, Field

class Endpoint(BaseModel):
    url: str = Field(..., description="엔드포인트 URL")
    method: str = Field(..., pattern="^(GET|POST|PUT|DELETE|PATCH)$")
    auth_required: bool = False

async def send_payload(endpoint: str, payload: str) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        return await client.post(endpoint, content=payload)
```

```python
# ❌ 나쁜 예시
endpoint = {"url": "/api/login", "method": "POST"}  # dict 전달
import requests                                       # requests 사용
response = requests.post(url, data=payload)           # 동기 호출
```

## 제약 사항
- `requests` 라이브러리 사용 금지 → `httpx` 사용
- Deep Agents (`deepagents`) 사용 금지
- LangSmith 프로덕션 사용 금지 (모의해킹 데이터 외부 유출 위험)
- SQLite/PostgreSQL 금지 → 세션 데이터는 JSON/YAML 파일 기반
- `workspaces/`는 .gitignore 대상, 절대 커밋 금지
- 민감 데이터(크레덴셜, 키, 취약점 증거)는 반드시 마스킹 저장

# 명령어 (Commands)

```bash
# 개발 환경
uv sync                                    # 의존성 설치
uvicorn src.backend.app:app --reload       # 개발 서버
python cli.py new --target <URL>           # 새 세션 생성
python cli.py scan --workspace <ID>        # 정찰 실행

# 품질 관리
pytest tests/ -v --cov=src/agents          # 테스트 + 커버리지
ruff check src/                            # 린트
mypy src/                                  # 타입 체크
```

# 품질 게이트 (Quality Gates)

## pre-commit hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff                         # 린트
        args: [--fix]
      - id: ruff-format                  # 포맷
  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: mypy src/ --strict
        language: system
        types: [python]
        pass_filenames: false
      - id: pytest
        name: pytest
        entry: pytest tests/ -x -q
        language: system
        types: [python]
        pass_filenames: false
      - id: gitleaks
        name: gitleaks
        entry: gitleaks protect --staged
        language: system
        pass_filenames: false
```

## AI 에이전트 작업 합의
- 절대 `git commit --no-verify` 실행 금지
- 통과를 위해 린트 규칙을 약화하거나 타입 체크를 비활성화 금지
- 테스트를 삭제하거나 `@pytest.mark.skip`으로 우회 금지
- hooks이나 테스트에 막히면 멈추고 보고
- 커밋 전 반드시 `pytest` + `ruff` + `mypy` 통과 확인

## AI가 자주 하는 실수 — 반드시 확인
- **환각된 임포트:** 존재하지 않는 LangChain 클래스나 이전 버전 API 사용 → 설치된 버전과 항상 대조
- **비일관적 async:** `async def` 안에서 동기 호출 혼합, `await` 누락 → mypy strict가 포착
- **잘못된 NetworkX 사용:** 방향 그래프(DiGraph)에 무방향 메서드 사용, 엣지 속성 무시
- **보안 갭:** FastAPI 입력 검증 누락, 문자열 연결 SQL 인젝션, 시크릿 하드코딩
- **의존성 혼동:** 존재하지 않는 PyPI 패키지 제안 → 설치 전 항상 확인
- **테스트 동어반복:** 구현 후 테스트 작성 시, 자기 코드를 검증하는 무의미한 테스트 생성 → 반드시 TDD (테스트 먼저)

## 구현 순서 (각 태스크마다)
```
1. Pydantic 스키마 정의
2. 인터페이스/API 시그니처 정의 (구현 없음)
3. 실패하는 테스트 작성 (수락 기준에서 도출)
4. 구현 코드 작성 (테스트 통과 목표)
5. ruff + mypy + pytest 통과 확인
6. git commit
```

## 세션 규율
- 태스크 1개 = 세션 1개 = 커밋 1개
- 모든 AI 프롬프트 전: `git add -p && git commit -m "checkpoint: pre-AI"`
- 8~10번 교환 후 모델이 비일관적이면 세션 종료 후 새 세션
- 세션 종료 전: 변경사항 + 미해결 문제 + 시도한 접근법 요약 → `activeContext.md`에 저장

# 컨텍스트 (Context)

## 구조
```
EAZY/
├── src/
│   ├── agents/                 # 에이전트 파이프라인 (핵심)
│   │   ├── core/               # 엔진 · 상태 · 공통 모델
│   │   ├── middleware/         # 세션 미들웨어 (쿠키/JWT/CSRF)
│   │   ├── recon/             # Stage 1 — 정찰 + KG 구축
│   │   ├── planning/          # Stage 2 — KG 탐색 기반 공격 경로 계획
│   │   ├── exploit/           # Stage 3 — 4레이어 익스플로잇
│   │   │   └── execution/     # L2 이중 경로 (커스텀 + 도구)
│   │   ├── analysis/          # Stage 4 — CVSS + 리포트
│   │   ├── skills/static/     # 정적 Skill (attacks/tools/waf/verify/chains/crypto)
│   │   ├── scanners/          # 플러그인 레지스트리 (6카테고리)
│   │   └── rag/               # RAG (축소 · 최신 CVE + 과거 보고서)
│   ├── backend/               # FastAPI + WebSocket
│   └── frontend/              # React 대시보드 (마지막 개발)
├── workspaces/                # 세션 데이터 (가변 · .gitignore)
├── tests/                     # src/ 미러 구조
├── docs/                      # PRD, Spec, API 계약
├── cli.py                     # CLI 진입점
└── config.yaml                # 전역 설정 (LLM 모델, API 키)
```

## 아키텍처 = 디렉토리
Spec의 각 컴포넌트가 디렉토리에 1:1 매핑된다:
- Stage 3 L2 페이로드 팩토리 → `src/agents/exploit/execution/payload_factory.py`
- Knowledge Graph → `src/agents/recon/knowledge_graph.py`
- Skill Selector → `src/agents/skills/selector.py`

## 코드(src/)와 데이터(workspaces/) 완전 분리
- `src/` = 불변, Git 관리, 모든 세션이 공유
- `workspaces/` = 가변, .gitignore, 세션별 격리

## 주의사항
- 4 Stage 파이프라인: 정찰(HTTP O) → 계획(HTTP X) → 익스플로잇(HTTP O) → 분석(HTTP X)
- Stage 구분 기준: "서버에 HTTP 요청을 보내는가"
- L3 검증은 결정론적 (LLM 미사용) — 이 원칙 절대 변경 금지
- 병렬 스캐너(Stage 1.2)는 LLM 0회 호출 — 도구만 실행 후 LLM 해석 1회

## 참조 문서
- 제품 요구사항: `docs/PRD.md`
- 기술 명세서: `docs/tech-spec.md`
- 개발 로드맵: `docs/tech-spec.md` 섹션 15

## 수정 금지 (명시적 지시 없이)
- `workspaces/` (세션 데이터)
- `.env` 파일
- `config.yaml`의 프로덕션 설정
- Skill 파일 (`skills/static/`) — 보안 전문가만 수정

## 제약 사항
- `pip install` 절대 사용 금지 → 패키지 추가는 반드시 `uv add <패키지>` 또는 `uv add --dev <패키지>`
- `pip` 자체가 .venv에 존재하지 않음 — uv가 패키지 관리를 전담
- Python 실행은 `uv run python`, `uv run pytest`, `uv run mypy` 사용