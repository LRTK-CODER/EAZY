# 개발 워크플로우 규칙

## 문서 계층

```
PRD.md               → 무엇을 / 왜 / 수락 기준 / 비목표
ARCHITECTURE.md      → 어떤 구조로 / 왜 이 구조 / 기술 스택 / 인터페이스 계약
specs/SPEC-NNN.md    → 기능 단위 검증 기준 + 인터페이스 계약 + 의존성
tasks/TASK-NNN.md    → SPEC별 TDD 구현 계획 (RED→GREEN→REFACTOR)
```

**정본(source of truth) 규칙:**
- 데이터 모델, 파일 구조, 기술 스택, 커맨드 → ARCHITECTURE.md에만
- 수락 기준, 성공 지표, 비목표, 사용자 플로 → PRD.md에만
- 검증 기준, 완료 조건 → 개별 SPEC에만
- PRD와 ARCHITECTURE에 같은 정보를 중복하지 않는다

## 핵심 원칙: 검증 기준이 아키텍처를 결정한다

- "어떻게 확인할 건가"가 "무엇을 만들 건가"보다 먼저
- SPEC의 첫 번째 섹션은 반드시 "검증 기준"
- SPEC-000은 항상 테스트 인프라 (다른 모든 SPEC이 의존)
- 검증 기준이 없는 기능은 구현하지 않는다

## 개발 순서

### 웹 서비스 프로젝트

```
Phase 1: 코어 엔진 (CLI 동작 가능) → 유닛테스트
Phase 2: REST API 레이어 → API 통합테스트 + OpenAPI 계약테스트
Phase 3: 프론트엔드 → E2E 테스트 (Playwright)
```

- 백엔드와 프론트엔드를 동시에 개발하지 않는다
- OpenAPI 스펙이 프론트-백엔드 "계약"이다
- 테스트 피라미드: 유닛(70%) + API 통합(20%) + E2E(10%)

### 기능 단위

```
SPEC 검증 기준 작성 → TASK 계획 → RED(테스트) → GREEN(구현) → REFACTOR(개선)
```

- 한 SPEC = 한 기능 = 한 세션
- SPEC 완료 → 커밋 → 새 세션에서 다음 SPEC

## TDD 세션 격리

- 🔴 RED, 🟢 GREEN, 🔵 REFACTOR는 각각 별도 세션
- RED 세션에 구현 컨텍스트를 제공하지 않음
- GREEN 세션에서 테스트 파일 수정 절대 금지
- Feature 하나의 전체 사이클(🔴→🟢→🔵) 완료 후 다음 Feature 시작

## 문서 먼저, 코드 나중 (Document-First)

SPEC에 없는 것을 구현하지 않는다. 개발 중 계획에 없던 것을 발견하면:

### 경로 판단

| 크기 | 기준 | 처리 |
|------|------|------|
| 소 | 현재 SPEC 안에서 해결 가능 | SPEC 검증 기준 추가 → TASK Feature 추가 → RED→GREEN→REFACTOR |
| 중 | 새 SPEC이 필요 | ARCHITECTURE 업데이트 → 새 SPEC 작성 → 새 TASK 작성 → 구현 |
| 대 | PRD 수준 기능 변경 | PRD에서 범위 판단 → 범위 밖이면 비목표 추가, 범위 안이면 기능 추가 후 나중 Phase에서 구현 |

### 처리 순서

1. 현재 작업 커밋 (진행 중 상태로)
2. 발견 사항을 DISCOVERIES.md에 기록
3. 해당 계층 문서 업데이트 (SPEC / ARCHITECTURE / PRD)
4. 크기가 "소"면 즉시 처리, "중/대"면 현재 SPEC 완료 후 처리

### 절대 하지 않는 것

- SPEC에 없는 검증 기준의 테스트를 작성
- ARCHITECTURE에 없는 컴포넌트를 구현
- PRD에 없는 기능을 만들기
- 발견 즉시 대규모 변경에 착수 (컨텍스트 스위칭 비용)

## 인터페이스 계약

- Stage 간 데이터는 반드시 Pydantic BaseModel로 전달 (dict 금지)
- ARCHITECTURE.md 3절에 정의된 래퍼 모델(ReconOutput, AttackPlan 등)을 준수
- 필드 추가는 OK, 필드 삭제/타입 변경은 BREAKING CHANGE → ARCHITECTURE 버전 올리고 마이그레이션

## 커밋 메시지

```
<type>(<scope>): <subject>
```

- type: `red` | `green` | `refactor` | `feat` | `fix` | `test` | `docs` | `plan` | `skill` | `plugin` | `docker` | `ci` | `chore` | `style`
- scope: SPEC 관련이면 반드시 `SPEC-NNN` 포함
- subject: 50자 이내, 명령문, 마침표 없음
- SPEC 검증 기준 통과 시 footer에 `Verifies: SPEC-NNN PASS "기준명"`

## 코드 품질 게이트

커밋 전 반드시 실행:
```bash
uv run pytest tests/ -v
uv run ruff check src/
uv run mypy src/
```

- 모든 데이터 모델: Pydantic BaseModel
- HTTP 클라이언트: httpx (async 필수, requests 금지)
- 모든 함수: 타입 힌트 필수
- 한 함수 = 한 책임
- async def가 기본, 동기 함수는 예외적으로만