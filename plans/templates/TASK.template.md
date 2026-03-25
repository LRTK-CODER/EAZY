# TASK-NNN: [기능명] — TDD 구현 계획

> **SPEC:** `plans/specs/SPEC-NNN-[기능명].md`
> **ARCHITECTURE:** `plans/ARCHITECTURE.md` [N절]
> **PRD 기능:** [기능 N]
> **날짜:** YYYY-MM-DD
> **테스트 러너:** pytest | 최소 커버리지: 80%

---

## 문서 계층에서의 위치

```
PRD.md          → 수락 기준 (Given-When-Then)
ARCHITECTURE.md → 구조 설계 (어떤 구조로)
SPEC-NNN.md     → 검증 기준 + 인터페이스 계약 ← 이것이 테스트의 근거
TASK-NNN.md     → 이 문서: TDD 구현 계획 (RED→GREEN→REFACTOR)
```

**SPEC의 검증 기준 → RED 테스트 → GREEN 구현 → REFACTOR 개선**

---

## 프로젝트 컨텍스트

- **소스 디렉토리**: `src/`
- **테스트 디렉토리**: `tests/`
- **테스트 커맨드**: `uv run pytest -v`
- **커버리지 커맨드**: `uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80`
- **복잡도 체크**: `uv run radon cc src/ --min C -s`

## 컨벤션

- 테스트 파일은 소스를 미러: `src/auth/service.py` → `tests/auth/test_service.py`
- 테스트명은 동작 인코딩: `test_<행동>_<예상_결과>`
- Given/When/Then 주석 사용
- 공유 설정은 `tests/conftest.py` 픽스처
- 테스트 대상은 mock 금지 — 외부 경계만 mock

## 세션 격리 규칙

- 🔴 RED, 🟢 GREEN, 🔵 REFACTOR는 **각각 별도 AI 세션**에서 실행
- RED 세션에 구현 컨텍스트를 제공하지 않음 (컨텍스트 오염 방지)
- GREEN 세션에서 테스트 파일 수정 절대 금지
- 기능 하나의 전체 사이클(🔴→🟢→🔵) 완료 후 다음 기능 시작

---

## SPEC 검증 기준 → 테스트 매핑

> SPEC의 검증 기준이 이 TASK의 테스트를 결정한다.
> 매핑되지 않는 검증 기준이 있으면 Feature를 추가한다.

| SPEC 검증 기준 | 테스트 함수 | Feature |
|---------------|------------|---------|
| `PASS: [SPEC의 검증 기준 1]` | `test_[동작_1]` | Feature 1 |
| `PASS: [SPEC의 검증 기준 2]` | `test_[동작_2]` | Feature 1 |
| `PASS: [SPEC의 부정 검증 1]` | `test_[엣지케이스]_returns_error` | Feature 1 |
| `PERF: [SPEC의 성능 기준 1]` | `test_[성능_조건]` | Feature 2 |

---

## 진행 현황

| Feature | RED | GREEN | REFACTOR | 상태 |
|---------|-----|-------|----------|------|
| Feature 1: [기능명] | [ ] | [ ] | [ ] | pending |
| Feature 2: [기능명] | [ ] | [ ] | [ ] | pending |
| Feature 3: [기능명] | [ ] | [ ] | [ ] | pending |

---

## Feature 1: [기능명]

**우선순위**: high | **의존성**: 없음 (또는 TASK-NNN Feature N ✅)
**SPEC 검증 기준**: [SPEC에서 가져온 PASS/PERF 항목 나열]

---

### Task 1.1 🔴 RED — 실패하는 테스트 작성

**세션**: 격리됨 — 구현 컨텍스트 없음
**상태**: [ ] pending

**동작 명세** (무엇을 기술, 어떻게는 절대 아님):
- [사용자 행동/입력] 시, 시스템은 [관찰 가능한 결과]
- [엣지 케이스] 시, 시스템은 [에러/폴백 동작]
- [경계 조건] 시, 시스템은 [구체적 출력]

**테스트 파일**: `tests/[모듈]/test_[기능].py`

**작성할 테스트 함수**:

| 테스트명 | SPEC 검증 기준 | 검증 내용 |
|----------|---------------|-----------|
| `test_[동작_1]` | PASS: [기준 1] | [예상 관찰 가능 결과] |
| `test_[동작_2]` | PASS: [기준 2] | [예상 관찰 가능 결과] |
| `test_[엣지케이스]_returns_error` | PASS: [부정 기준] | [에러 메시지 또는 예외] |

**parametrize 케이스** (해당 시):

| 입력 | 예상 출력 |
|------|-----------|
| [input_1] | [output_1] |
| [input_2] | [output_2] |

**필요한 픽스처**:
- [SPEC-000의 어떤 테스트 인프라를 사용하는지 명시]
- [mock 외부 서비스, 테스트 데이터 등]

**인터페이스 계약 검증** (SPEC에서 가져옴):
- 입력 타입: [Pydantic 모델명]
- 출력 타입: [Pydantic 모델명]
- [잘못된 타입 입력 시 ValidationError 발생 검증]

**예상 실패**: `ModuleNotFoundError` (함수/클래스 미존재)

**단계 게이트 ✓**:
- [ ] `uv run pytest tests/[모듈]/test_[기능].py -v` exit non-zero
- [ ] 모든 실패가 `ImportError`/`ModuleNotFoundError` 또는 `AssertionError` (설정 에러 아님)
- [ ] 테스트가 public API만 사용 — private 메서드나 내부 상태 없음
- [ ] SPEC의 모든 PASS 기준에 대응하는 테스트 존재
- [ ] 구현 파일 생성/수정 없음
- [ ] `git add tests/ && git commit -m "red(SPEC-NNN): [기능] 실패 테스트"`

---

### Task 1.2 🟢 GREEN — 테스트 통과를 위한 최소 코드 구현

**세션**: 격리됨 — 테스트 파일 읽기, 테스트 작성 컨텍스트 없음
**상태**: [ ] pending
**의존성**: Task 1.1 ✅

**입력**: RED 단계 테스트 파일 `tests/[모듈]/test_[기능].py`
**참조**: `plans/ARCHITECTURE.md` [N절] (구조 설계), `plans/specs/SPEC-NNN.md` (인터페이스 계약)

**규칙**:
- 실패하는 테스트를 읽고 필요한 동작 이해
- SPEC의 인터페이스 계약(Pydantic 모델)을 준수하여 구현
- 테스트를 통과하는 **최소한의 코드만** 작성 (YAGNI)
- 구현을 수정, **테스트 파일 수정 절대 금지**
- 추가 기능 없음, "있으면 좋겠다" 없음
- 테스트 실패 시 → 구현을 고침 (테스트를 고치지 않음)

**파일**:

**생성:**
- `src/[모듈]/[기능].py` — [역할 설명]
- `src/[모듈]/models.py` — [Pydantic 모델 — SPEC 인터페이스 계약 구현]

**수정:**
- `src/[모듈]/__init__.py` — import 추가

**수정 금지:**
- `tests/*` — 테스트는 계약이지 제안이 아님
- [다른 보호 경로]

**단계 게이트 ✓**:
- [ ] `uv run pytest tests/[모듈]/test_[기능].py -v` exit 0 (RED 테스트 전부 통과)
- [ ] `uv run pytest` exit 0 (전체 스위트 — 리그레션 없음)
- [ ] 테스트 파일 변경 없음 (`git diff tests/` 변경 없음)
- [ ] `uv run mypy src/[모듈]/[기능].py` 에러 0개
- [ ] Pydantic 모델이 SPEC 인터페이스 계약과 일치
- [ ] `git commit -m "green(SPEC-NNN): [기능] 구현"`

---

### Task 1.3 🔵 REFACTOR — 코드 품질 개선

**세션**: 격리됨 — 구현 + 테스트 보기, 이전 컨텍스트 없음
**상태**: [ ] pending
**의존성**: Task 1.2 ✅

**평가 체크리스트**:
- [ ] 순환 복잡도 < 10 (`uv run radon cc --min C`)
- [ ] 코드 중복 없음 (공유 로직 추출)
- [ ] 명확한 네이밍 (변수/함수가 의도 표현)
- [ ] 단일 책임 (함수/클래스마다 하나의 일)
- [ ] 적절한 에러 처리 (bare except 없음, typed exceptions)
- [ ] public API에 docstring

**결정**: [ ] 리팩토링 수행 / [ ] 건너뛰기

**리팩토링 시**:
- 변경 후 반드시 `uv run pytest -v` 실행
- 테스트 깨지면 → `git checkout .`으로 복원 후 재평가
- 개선사항별 개별 커밋

**건너뛰기 시**: 근거 기록
<!-- 예: "구현이 최소하고 집중됨, 중복 없음, 모든 함수 CC=3" -->

**단계 게이트 ✓**:
- [ ] 전체 테스트 스위트 통과
- [ ] C+ 등급 함수 없음 (`uv run radon cc src/[모듈]/[기능].py --min C -s`)
- [ ] `git commit -m "refactor(SPEC-NNN): [기능]에서 [개선 내용]"`

---

## Feature 2: [기능명]

**우선순위**: medium | **의존성**: Feature 1 (Task 1.3 ✅)
**SPEC 검증 기준**: [SPEC에서 가져온 PASS/PERF 항목]

---

### Task 2.1 🔴 RED — [기능 2] 실패 테스트 작성

<!-- Task 1.1과 동일 구조 -->

---

### Task 2.2 🟢 GREEN — [기능 2] 구현

<!-- Task 1.2와 동일 구조 -->

---

### Task 2.3 🔵 REFACTOR — [기능 2] 개선

<!-- Task 1.3과 동일 구조 -->

---

<!-- Feature 3, 4, ... 동일 양식으로 반복 -->

---

## 안티패턴 가드

### 절대 하지 말 것:
1. 실패하는 테스트를 삭제하거나 약화 — 테스트 실패 시 구현을 수정
2. 테스트 대상 자체를 mock — 외부 경계만 mock 허용
3. mock을 검증하는 테스트 작성 — 실제 코드 경로를 검증
4. 하드코딩으로 기술적 통과 — `@parametrize`로 다수 입력 강제
5. private 메서드 테스트 — public 인터페이스만 테스트
6. 테스트명에 "and" 사용 — 테스트당 하나의 동작
7. RED 테스트 없이 구현 작성 — 삭제하고 재시작
8. GREEN에서 테스트 파일 수정 — 테스트는 계약
9. REFACTOR 평가 건너뛰기 — "불필요"는 정당하나 평가는 필수
10. Feature N 미완료 상태에서 Feature N+1 시작 — 전체 🔴→🟢→🔵 완료 후
11. SPEC에 없는 검증 기준을 테스트에 추가 — SPEC을 먼저 업데이트
12. SPEC 인터페이스 계약과 다른 입출력 타입 사용 — 계약이 코드를 결정

---

## SPEC 검증 완료 체크리스트

> 모든 Feature 완료 후, SPEC의 검증 기준을 하나씩 확인한다.

| SPEC 검증 기준 | 테스트 통과 | 비고 |
|---------------|-----------|------|
| `PASS: [기준 1]` | [ ] | [Feature 1 - test_동작_1] |
| `PASS: [기준 2]` | [ ] | [Feature 1 - test_동작_2] |
| `PASS: [부정 기준 1]` | [ ] | [Feature 1 - test_엣지케이스] |
| `PERF: [성능 기준 1]` | [ ] | [Feature 2 - test_성능] |

**SPEC 검증 기준 100% 통과 시 → 이 SPEC은 완료.**

---

## 의존성 그래프

```
Feature 1: [1.1 🔴] → [1.2 🟢] → [1.3 🔵] ✓
                                         ↓
Feature 2: [2.1 🔴] → [2.2 🟢] → [2.3 🔵] ✓
                                         ↓
Feature 3: [3.1 🔴] → [3.2 🟢] → [3.3 🔵] ✓

독립 기능 (병렬 가능):
Feature 4: [4.1 🔴] → [4.2 🟢] → [4.3 🔵] ✓  (의존성 없음)
Feature 5: [5.1 🔴] → [5.2 🟢] → [5.3 🔵] ✓  (의존성 없음)
```