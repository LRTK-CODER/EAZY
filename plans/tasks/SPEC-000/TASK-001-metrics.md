# TASK-001: 측정 유틸리티 — TDD 구현 계획

> **SPEC:** `plans/specs/SPEC-000-test-infra.md` Feature 1
> **ARCHITECTURE:** `plans/ARCHITECTURE.md` 부록 B
> **PRD 기능:** 기능 0
> **날짜:** 2026-03-27
> **테스트 러너:** pytest | 최소 커버리지: 80%

---

## 문서 계층에서의 위치

```
PRD.md          → 수락 기준 (Given-When-Then)
ARCHITECTURE.md → 구조 설계 (어떤 구조로)
SPEC-000.md     → 검증 기준 + 인터페이스 계약 ← 이것이 테스트의 근거
TASK-001.md     → 이 문서: 측정 유틸리티 TDD 계획
```

---

## 프로젝트 컨텍스트

- **테스트 헬퍼**: `tests/helpers/`
- **테스트 커맨드**: `uv run pytest tests/helpers/test_metrics.py -v`
- **커버리지 커맨드**: `uv run pytest --cov=tests/helpers/metrics --cov-report=term-missing --cov-fail-under=80`

## 세션 격리 규칙

- 🔴 RED, 🟢 GREEN, 🔵 REFACTOR는 **각각 별도 AI 세션**에서 실행
- RED 세션에 구현 컨텍스트를 제공하지 않음
- GREEN 세션에서 테스트 파일 수정 절대 금지

---

## SPEC 검증 기준 → 테스트 매핑

| SPEC 검증 기준 | 테스트 함수 |
|---------------|------------|
| `PASS: compute_metrics 호출 시 MetricsResult 반환` | `test_compute_metrics_returns_metrics_result` |
| `PASS: tn=N 제공 시 Youden's Index 산출` | `test_compute_metrics_with_tn_returns_youdens_index` |
| `PASS: 완전 일치 시 P=1.0, R=1.0, F1=1.0` | `test_perfect_match_returns_all_ones` |
| `PASS: predicted 빈 리스트 시 P=None, R=0.0, F1=None` | `test_empty_predicted_returns_none_precision_zero_recall` |
| `PASS: ground_truth 빈 리스트 시 R=None, F1=None` | `test_empty_ground_truth_returns_none_recall` |
| `PASS: FP만 있으면 P=0.0, R=0.0` | `test_all_fp_returns_zero_precision_zero_recall` |
| `PASS: match_fn 커스텀 매칭` | `test_custom_match_fn_used_for_matching` |
| `PASS: 타입 불일치 시 TypeError` | `test_type_mismatch_raises_type_error` |
| `PERF: 10,000개 항목 < 100ms` | `test_compute_metrics_10k_items_under_100ms` |

---

## 진행 현황

| 단계 | 상태 |
|------|------|
| 🔴 RED | [ ] pending |
| 🟢 GREEN | [ ] pending |
| 🔵 REFACTOR | [ ] pending |

---

### Task 1.1 🔴 RED — 실패하는 테스트 작성

**세션**: 격리됨 — 구현 컨텍스트 없음
**상태**: [ ] pending

**동작 명세**:
- `compute_metrics(predicted, ground_truth)` 호출 시, TP/FP/FN/Precision/Recall/F1이 포함된 `MetricsResult`가 반환된다
- `tn=N`을 제공하면 Youden's Index가 추가로 산출된다. 미제공 시 `None`
- predicted와 ground_truth가 완전 일치하면 Precision=1.0, Recall=1.0, F1=1.0
- predicted가 빈 리스트이면 Precision=`None`, Recall=0.0, F1=`None`
- ground_truth가 빈 리스트이면 Precision=`None`, Recall=`None`, F1=`None`
- predicted에 FP만 있으면 Precision=0.0, Recall=0.0
- `match_fn` 파라미터로 커스텀 매칭 함수를 전달하면 해당 함수로 매칭한다
- predicted와 ground_truth 타입이 불일치하면 `TypeError`
- 10,000개 항목 기준 100ms 이내

**테스트 파일**: `tests/helpers/test_metrics.py`

**작성할 테스트 함수**:

| 테스트명 | SPEC 검증 기준 | 검증 내용 |
|----------|---------------|-----------|
| `test_compute_metrics_returns_metrics_result` | PASS: MetricsResult 반환 | 반환 타입이 MetricsResult |
| `test_compute_metrics_with_tn_returns_youdens_index` | PASS: tn 제공 시 Youden's Index | tn=N 시 float, 미제공 시 None |
| `test_perfect_match_returns_all_ones` | PASS: 완전 일치 | P=1.0, R=1.0, F1=1.0 |
| `test_empty_predicted_returns_none_precision_zero_recall` | PASS: predicted 빈 리스트 | P=None, R=0.0, F1=None |
| `test_empty_ground_truth_returns_none_recall` | PASS: ground_truth 빈 리스트 | P=None, R=None, F1=None |
| `test_all_fp_returns_zero_precision_zero_recall` | PASS: FP만 | P=0.0, R=0.0 |
| `test_custom_match_fn_used_for_matching` | PASS: match_fn 주입 | 커스텀 함수로 매칭 |
| `test_type_mismatch_raises_type_error` | 부정: 타입 불일치 | TypeError 발생 |
| `test_compute_metrics_10k_items_under_100ms` | PERF: 10k < 100ms | 실행 시간 측정 |

**parametrize 케이스**:

| predicted | ground_truth | tn | expected P | expected R | expected F1 | expected Youden |
|-----------|--------------|-----|-----------|-----------|------------|-----------------|
| `[1,2,3]` | `[1,2,3]` | None | 1.0 | 1.0 | 1.0 | None |
| `[1,2,3]` | `[1,2,3]` | 5 | 1.0 | 1.0 | 1.0 | 1.0 |
| `[]` | `[1,2,3]` | None | None | 0.0 | None | None |
| `[1,2,3]` | `[]` | None | None | None | None | None |
| `[4,5,6]` | `[1,2,3]` | None | 0.0 | 0.0 | 0.0 | None |
| `[1,2,4]` | `[1,2,3]` | None | ≈0.67 | ≈0.67 | ≈0.67 | None |

**필요한 픽스처**: 없음 (순수 함수 테스트)

**인터페이스 계약 검증**:
- 입력: `list[T]`, `list[T]`, `Callable[[T, T], bool]`, `int | None`
- 출력: `MetricsResult` (Pydantic BaseModel)

**예상 실패**: `ModuleNotFoundError` (모듈 미존재)

**단계 게이트 ✓**:
- [ ] `uv run pytest tests/helpers/test_metrics.py -v` exit non-zero
- [ ] 모든 실패가 `ImportError`/`ModuleNotFoundError` 또는 `AssertionError`
- [ ] 테스트가 public API만 사용
- [ ] SPEC의 모든 PASS 기준에 대응하는 테스트 존재
- [ ] 구현 파일 생성/수정 없음
- [ ] `git add tests/ && git commit -m "red(SPEC-000): 측정 유틸리티 실패 테스트"`

---

### Task 1.2 🟢 GREEN — 테스트 통과를 위한 최소 코드 구현

**세션**: 격리됨 — 테스트 파일 읽기만, 수정 금지
**상태**: [ ] pending
**의존성**: Task 1.1 ✅

**입력**: `tests/helpers/test_metrics.py`
**참조**: `plans/specs/SPEC-000-test-infra.md` 인터페이스 계약

**파일**:

**생성:**
- `tests/__init__.py` — 패키지 초기화 (없으면)
- `tests/helpers/__init__.py` — 패키지 초기화
- `tests/helpers/metrics.py` — `compute_metrics()` 함수 + `MetricsResult` 모델

**수정 금지:**
- `tests/helpers/test_metrics.py`

**단계 게이트 ✓**:
- [ ] `uv run pytest tests/helpers/test_metrics.py -v` exit 0
- [ ] `uv run pytest` exit 0 (전체 스위트 — 리그레션 없음)
- [ ] 테스트 파일 변경 없음 (`git diff tests/helpers/test_metrics.py` 변경 없음)
- [ ] `uv run mypy tests/helpers/metrics.py` 에러 0개
- [ ] MetricsResult가 SPEC 인터페이스 계약과 일치
- [ ] `git commit -m "green(SPEC-000): 측정 유틸리티 구현"`

---

### Task 1.3 🔵 REFACTOR — 코드 품질 개선

**세션**: 격리됨
**상태**: [ ] pending
**의존성**: Task 1.2 ✅

**평가 체크리스트**:
- [ ] 순환 복잡도 < 10 (`uv run radon cc tests/helpers/metrics.py --min C -s`)
- [ ] 코드 중복 없음
- [ ] 명확한 네이밍
- [ ] 단일 책임
- [ ] 적절한 에러 처리
- [ ] public API에 Google 스타일 docstring

**결정**: [ ] 리팩토링 수행 / [ ] 건너뛰기

**단계 게이트 ✓**:
- [ ] 전체 테스트 스위트 통과
- [ ] C+ 등급 함수 없음
- [ ] `git commit -m "refactor(SPEC-000): 측정 유틸리티 [개선 내용]"`

---

## SPEC 검증 완료 체크리스트

| SPEC 검증 기준 | 테스트 통과 | 비고 |
|---------------|-----------|------|
| `PASS: compute_metrics MetricsResult 반환` | [ ] | test_compute_metrics_returns_metrics_result |
| `PASS: tn 제공 시 Youden's Index 산출` | [ ] | test_compute_metrics_with_tn_returns_youdens_index |
| `PASS: 완전 일치 P=1.0, R=1.0, F1=1.0` | [ ] | test_perfect_match_returns_all_ones |
| `PASS: predicted 빈 리스트 P=None, R=0.0` | [ ] | test_empty_predicted_returns_none_precision_zero_recall |
| `PASS: ground_truth 빈 리스트 R=None` | [ ] | test_empty_ground_truth_returns_none_recall |
| `PASS: FP만 P=0.0, R=0.0` | [ ] | test_all_fp_returns_zero_precision_zero_recall |
| `PASS: match_fn 커스텀 매칭` | [ ] | test_custom_match_fn_used_for_matching |
| `PASS: 타입 불일치 TypeError` | [ ] | test_type_mismatch_raises_type_error |
| `PERF: 10k < 100ms` | [ ] | test_compute_metrics_10k_items_under_100ms |
