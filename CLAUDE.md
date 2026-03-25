# EAZY — 프로젝트 가이드라인

## 프로젝트 개요
LLM 기반 웹 모의해킹 에이전트. 웹 애플리케이션의 API 흐름·데이터 플로·비즈니스 로직을 Knowledge Graph로 구조화하고, 취약점들을 자동 연계하여 공격 체인을 구성·실행한다.

## 기술 스택
- **언어**: Python 3.11+
- **에이전트 프레임워크**: LangChain + LangGraph
- **LLM 추상화**: LiteLLM
- **백엔드**: FastAPI + uvicorn
- **프론트엔드**: React + TypeScript
- **HTTP 클라이언트**: httpx (async)
- **Knowledge Graph**: NetworkX
- **데이터 검증**: Pydantic
- **테스트**: pytest + pytest-asyncio

## 주요 명령어
- **의존성 설치**: `uv sync`
- **개발 서버 실행**: `uv run uvicorn src.backend.app:app --reload`
- **CLI 세션 생성**: `uv run python cli.py new --target <URL>`
- **CLI 스캔 실행**: `uv run python cli.py scan --workspace <ID>`
- **테스트 실행**: `uv run pytest tests/ -v --cov=src/agents`
- **린트 체크**: `uv run ruff check src/`
- **타입 체크**: `uv run mypy src/`
- **패키지 추가**: `uv add <패키지>` (pip 절대 사용 금지)
- **Docker 빌드**: `bash scripts/build_dockers.sh`

## 문서 위치
- **PRD**: `plans/PRD.md` — 무엇을 / 왜 / 수락 기준 / 비목표
- **아키텍처**: `plans/ARCHITECTURE.md` — 구조 설계 / 기술 스택 / 인터페이스 계약
- **SPEC**: `plans/specs/SPEC-NNN-*.md` — 기능별 검증 기준 + 인터페이스 계약
- **TASK**: `plans/tasks/TASK-NNN-*.md` — SPEC별 TDD 구현 계획
- **발견 사항**: `DISCOVERIES.md` — 개발 중 계획에 없던 발견 기록

## 코드 스타일 및 규칙
- **작성 언어**: 모든 주석, docstring, 커밋 메시지는 **한국어**로 작성
- **docstring**: Google 스타일 (Args, Returns, Raises)
- **데이터 모델**: 모든 구조화된 데이터는 Pydantic `BaseModel` (dict 전달 금지)
- **비동기**: `async def`가 기본, 동기 함수는 예외적으로만
- **타입 힌트**: 모든 함수에 필수 (인자 + 반환값)
- **함수 설계**: 한 함수 = 한 책임 (판단 + 실행 + 검증을 하나에 넣지 않는다)
- **네이밍**: 변수/함수 snake_case, 클래스 PascalCase, 상수 UPPER_SNAKE_CASE
- **에러 처리**: bare `except:` 금지, 구체적 예외 타입 사용
- **로깅**: `print()` 금지, `logging` 모듈 사용, 민감 데이터 마스킹 필수

## 워크플로우
- SPEC의 검증 기준 → RED 테스트 → GREEN 구현 → REFACTOR 순서
- SPEC에 없는 것은 구현하지 않는다 — 필요하면 문서를 먼저 업데이트
- 1 PR = 1 SPEC, 여러 SPEC을 하나의 PR에 섞지 않는다
- 브랜치: `spec-NNN/[간단한-설명]`
- PR 생성 전 반드시 `pytest` + `ruff` + `mypy`를 통과해야 한다
- 커밋: `<type>(SPEC-NNN): <subject>`

## 절대 금지
- `pip install` 사용 (`uv add`만 사용)
- `requests` 라이브러리 사용 (httpx async 사용)
- LangSmith에 모의해킹 데이터 전송
- 민감 데이터를 평문으로 저장/로그
- 스코프 밖 도메인/IP에 요청 전송
- 사용자 승인 없이 High 영향도 공격 실행
- `workspaces/`를 Git에 커밋
- SPEC에 없는 기능 구현
- GREEN 세션에서 테스트 파일 수정