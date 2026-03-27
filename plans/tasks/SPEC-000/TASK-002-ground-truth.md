# TASK-002: Ground Truth 스키마 — TDD 구현 계획

> **SPEC:** `plans/specs/SPEC-000-test-infra.md` Feature 2
> **ARCHITECTURE:** `plans/ARCHITECTURE.md` 3절
> **PRD 기능:** 기능 0
> **날짜:** 2026-03-27
> **테스트 러너:** pytest | 최소 커버리지: 80%

---

## 문서 계층에서의 위치

```
PRD.md          → 수락 기준 (Given-When-Then)
ARCHITECTURE.md → 구조 설계 (어떤 구조로)
SPEC-000.md     → 검증 기준 + 인터페이스 계약 ← 이것이 테스트의 근거
TASK-002.md     → 이 문서: Ground Truth 스키마 TDD 계획
```

---

## 프로젝트 컨텍스트

- **테스트 헬퍼**: `tests/helpers/`
- **공유 모델**: `src/models/`
- **테스트 커맨드**: `uv run pytest tests/helpers/test_ground_truth.py -v`
- **커버리지 커맨드**: `uv run pytest --cov=tests/helpers/ground_truth --cov-report=term-missing --cov-fail-under=80`

## 세션 격리 규칙

- 🔴 RED, 🟢 GREEN, 🔵 REFACTOR는 **각각 별도 AI 세션**에서 실행
- RED 세션에 구현 컨텍스트를 제공하지 않음
- GREEN 세션에서 테스트 파일 수정 절대 금지

---

## SPEC 검증 기준 → 테스트 매핑

| SPEC 검증 기준 | 테스트 함수 |
|---------------|------------|
| `PASS: GroundTruth 필드 존재` | `test_ground_truth_has_required_fields` |
| `PASS: JSON 로드 시 유효 모델` | `test_ground_truth_loads_from_json` |
| `PASS: 필수 필드 누락 시 ValidationError` | `test_ground_truth_missing_app_id_raises_validation_error` |
| `PASS: kg_snapshot KnowledgeGraphSnapshot 호환` | `test_kg_snapshot_compatible_with_architecture` |
| `PASS: chains에 steps + impact 포함` | `test_chain_has_steps_and_impact` |
| `PASS: extra 필드 허용 (extra="allow")` | `test_ground_truth_allows_extra_fields` |

---

## 진행 현황

| 단계 | 상태 |
|------|------|
| 🔴 RED | [ ] pending |
| 🟢 GREEN | [ ] pending |
| 🔵 REFACTOR | [ ] pending |

---

### Task 2.1 🔴 RED — 실패하는 테스트 작성

**세션**: 격리됨 — 구현 컨텍스트 없음
**상태**: [ ] pending

**동작 명세**:
- `GroundTruth` 모델이 `app_id`, `endpoints`, `vulnerabilities`, `kg_snapshot`, `chains` 필드를 가진다
- JSON 문자열로부터 `model_validate_json()`으로 로드하면 유효한 인스턴스가 반환된다
- 필수 필드(`app_id`) 누락 시 `ValidationError`가 발생한다
- `kg_snapshot`은 `KnowledgeGraphSnapshot` 스키마와 호환된다 (nodes: `list[KGNode]`, edges: `list[KGEdge]`)
- `chains`의 각 항목은 `steps`(list[str])와 `impact`(str)을 포함한다
- Stage별 확장 필드를 추가해도 `ValidationError`가 발생하지 않는다 (extra="allow")

**테스트 파일**: `tests/helpers/test_ground_truth.py`

**작성할 테스트 함수**:

| 테스트명 | SPEC 검증 기준 | 검증 내용 |
|----------|---------------|-----------|
| `test_ground_truth_has_required_fields` | PASS: 필드 존재 | app_id, endpoints, vulnerabilities, kg_snapshot, chains |
| `test_ground_truth_loads_from_json` | PASS: JSON 로드 | model_validate_json 성공 |
| `test_ground_truth_missing_app_id_raises_validation_error` | PASS: 필수 필드 누락 | ValidationError 발생 |
| `test_kg_snapshot_compatible_with_architecture` | PASS: KG 호환 | nodes/edges 구조 검증 |
| `test_chain_has_steps_and_impact` | PASS: 체인 구조 | steps: list[str], impact: str |
| `test_ground_truth_allows_extra_fields` | 부정: extra 허용 | 임의 필드 추가 시 에러 없음 |

**필요한 픽스처**:
- 유효한 GroundTruth JSON 문자열 (인라인 또는 conftest)
- ARCHITECTURE 3.2절 KGNode/KGEdge 스키마 참조

**인터페이스 계약 검증**:
- `GroundTruth(BaseModel, extra="allow")` — app_id 필수, 나머지 기본값
- `GroundTruthChain(BaseModel)` — chain_id, steps, impact 필수

**예상 실패**: `ModuleNotFoundError` (모듈 미존재)

**단계 게이트 ✓**:
- [ ] `uv run pytest tests/helpers/test_ground_truth.py -v` exit non-zero
- [ ] 모든 실패가 `ImportError`/`ModuleNotFoundError` 또는 `AssertionError`
- [ ] 테스트가 public API만 사용
- [ ] SPEC의 모든 PASS 기준에 대응하는 테스트 존재
- [ ] 구현 파일 생성/수정 없음
- [ ] `git add tests/ && git commit -m "red(SPEC-000): Ground Truth 스키마 실패 테스트"`

---

### Task 2.2 🟢 GREEN — 테스트 통과를 위한 최소 코드 구현

**세션**: 격리됨 — 테스트 파일 읽기만, 수정 금지
**상태**: [ ] pending
**의존성**: Task 2.1 ✅

**입력**: `tests/helpers/test_ground_truth.py`
**참조**: `plans/ARCHITECTURE.md` 3절, `plans/specs/SPEC-000-test-infra.md` 인터페이스 계약

**파일**:

**생성:**
- `tests/helpers/ground_truth.py` — `GroundTruth`, `GroundTruthChain` 모델
- `src/__init__.py` — 패키지 초기화 (없으면)
- `src/models/__init__.py` — 패키지 초기화
- `src/models/interfaces.py` — `KnowledgeGraphSnapshot`, `KGNode`, `KGEdge`, `KGMetadata` (ARCHITECTURE 3.2절)
- `src/models/endpoints.py` — `Endpoint` 모델 스텁 (최소 필드만)
- `src/models/findings.py` — `Vulnerability` 모델 스텁 (최소 필드만)
- `src/models/chains.py` — `ChainResult` 모델 스텁 (최소 필드만)

> **주의:** `src/models/` 모델은 ARCHITECTURE 3절의 최소 스텁이다.
> 각 Stage SPEC에서 필드를 채워나간다. 여기서는 GroundTruth가 import할 수 있는 수준만 구현.

**수정 금지:**
- `tests/helpers/test_ground_truth.py`

**단계 게이트 ✓**:
- [ ] `uv run pytest tests/helpers/test_ground_truth.py -v` exit 0
- [ ] `uv run pytest` exit 0 (전체 스위트 — 리그레션 없음)
- [ ] 테스트 파일 변경 없음
- [ ] `uv run mypy tests/helpers/ground_truth.py` 에러 0개
- [ ] `uv run mypy src/models/` 에러 0개
- [ ] GroundTruth 모델이 SPEC 인터페이스 계약과 일치
- [ ] `git commit -m "green(SPEC-000): Ground Truth 스키마 + src/models 스텁 구현"`

---

### Task 2.3 🔵 REFACTOR — 코드 품질 개선

**세션**: 격리됨
**상태**: [ ] pending
**의존성**: Task 2.2 ✅

**평가 체크리스트**:
- [ ] Pydantic 모델 필드에 `Field(description=...)` 적용
- [ ] 모델 간 의존 관계 명확
- [ ] docstring 완비 (Google 스타일)
- [ ] import 정리
- [ ] `src/models/` 스텁이 ARCHITECTURE 3절과 일관성 유지

**결정**: [ ] 리팩토링 수행 / [ ] 건너뛰기

**단계 게이트 ✓**:
- [ ] 전체 테스트 스위트 통과
- [ ] `git commit -m "refactor(SPEC-000): Ground Truth 스키마 [개선 내용]"`

---

## SPEC 검증 완료 체크리스트

| SPEC 검증 기준 | 테스트 통과 | 비고 |
|---------------|-----------|------|
| `PASS: GroundTruth 필드 존재` | [ ] | test_ground_truth_has_required_fields |
| `PASS: JSON 로드 유효` | [ ] | test_ground_truth_loads_from_json |
| `PASS: 필수 필드 누락 ValidationError` | [ ] | test_ground_truth_missing_app_id_raises_validation_error |
| `PASS: kg_snapshot KG 호환` | [ ] | test_kg_snapshot_compatible_with_architecture |
| `PASS: chains steps+impact` | [ ] | test_chain_has_steps_and_impact |
| `PASS: extra 필드 허용` | [ ] | test_ground_truth_allows_extra_fields |
