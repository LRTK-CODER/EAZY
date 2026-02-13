# Implementation Plan: REQ-001 URL Pattern Normalization

**Status**: 🔄 In Progress
**Started**: 2026-02-13
**Last Updated**: 2026-02-13
**Estimated Completion**: 2026-02-14

---

**CRITICAL INSTRUCTIONS**: After completing each phase:
1. Check off completed task checkboxes
2. Run all quality gate validation commands
3. Verify ALL quality gate items pass
4. Update "Last Updated" date above
5. Document learnings in Notes section
6. Only then proceed to next phase

**DO NOT skip quality gates or proceed with failing checks**

---

## Overview

### Feature Description

URL 패턴 정규화(URL Pattern Normalization)는 동일 구조의 URL(예: `/challenges/2692`, `/challenges/2691`)을 패턴(`/challenges/<int>`)으로 그룹핑하여, 크롤링 예산을 다양한 경로 탐색에 효율적으로 배분하는 기능이다. REQ-001의 마지막 미완료 Acceptance Criteria이다.

### Success Criteria
- [ ] 6가지 세그먼트 타입(`<uuid>`, `<int>`, `<date>`, `<hash>`, `<slug>`, `<string>`) 정확히 분류
- [ ] 동일 구조 URL을 패턴으로 그룹핑하고, 패턴당 N개(기본 3)만 샘플링
- [ ] 서로 다른 타입이 같은 위치에 섞이면 `<string>`으로 승격
- [ ] CrawlResult에 패턴 그룹 정보 포함 및 JSON 내보내기
- [ ] 기존 109개 테스트 전부 통과, 신규 테스트 커버리지 80% 이상

### User Impact

크롤링 시 동일 구조의 페이지(상품 상세, 게시글 등)를 자동 감지하여 중복 크롤링을 방지한다. 크롤링 예산이 다양한 경로 탐색에 효율적으로 배분되어 전체 사이트 구조를 더 빠르고 완전하게 파악할 수 있다.

---

## Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| 새 파일 `url_pattern.py` 생성 (기존 `url_resolver.py` 확장 대신) | `url_resolver.py`는 URL 정규화/스코프 체크 담당, 패턴 분류/그룹핑은 별도 관심사 | 파일 하나 추가되지만 SRP(단일 책임 원칙) 준수 |
| 증분(incremental) 분류 방식 | 크롤링은 URL을 하나씩 발견하므로 스트리밍 처리가 자연스러움 | 타입 승격 시 그룹 병합 로직 필요 |
| 구조적 키(structural key)로 1차 그룹핑 | 리터럴 세그먼트 고정 + 동적 세그먼트 `*`로 마킹하여 구조 매칭 → PRD의 승격 규칙 정확 구현 | 2단계 그룹핑으로 약간 복잡하지만 엣지 케이스 정확 처리 |
| 리터럴 vs 동적 세그먼트 구분 | 5가지 패턴(uuid/int/date/hash/slug)에 매칭되면 동적, 아니면 리터럴(경로명 그대로 유지) | `admin123` 같은 애매한 경우는 리터럴로 분류 (안전한 기본값) |

---

## Dependencies

### Required Before Starting
- [x] REQ-001 기존 크롤링 엔진 구현 완료 (6/7 AC 완료)
- [x] `url_resolver.py`의 `normalize_url()` 함수 동작 확인

### External Dependencies
- 추가 패키지 없음 (stdlib `re` + 기존 `pydantic` 사용)

---

## Test Strategy

### Testing Approach
**TDD Principle**: Write tests FIRST, then implement to make them pass

### Test Pyramid for This Feature
| Test Type | Coverage Target | Purpose |
|-----------|-----------------|---------|
| **Unit Tests** | >=80% | 세그먼트 분류, 패턴 정규화, 그룹핑, 샘플링 로직 |
| **Integration Tests** | Critical paths | CrawlerEngine과 URLPatternNormalizer 연동, 중복 스킵 |
| **E2E Tests** | Key user flows | JSON 내보내기에 패턴 그룹 포함 확인 |

### Test File Organization
```
tests/
├── unit/
│   ├── models/
│   │   └── test_crawl_types.py          # 기존 + SegmentType, PatternGroup 모델 테스트 추가
│   └── crawler/
│       └── test_url_pattern.py          # [NEW] 세그먼트 분류 + 패턴 정규화 + 그룹핑 테스트
├── integration/
│   └── crawler/
│       └── test_crawler_engine.py       # 기존 + 패턴 정규화 통합 테스트 추가
```

### Coverage Requirements by Phase
- **Phase 1 (Foundation)**: 모델 + 세그먼트 분류 단위 테스트 (>=80%)
- **Phase 2 (Core Logic)**: 정규화 + 그룹핑 + 샘플링 단위 테스트 (>=80%)
- **Phase 3 (Integration)**: 엔진 통합 + 내보내기 테스트 (>=70%)

### Test Naming Convention
```python
# 파일명: test_{모듈명}.py
# 클래스명: Test{컴포넌트명}
# 함수명: test_{행위}_{조건}_{기대결과}
# 예시: test_classify_segment_pure_digits_returns_int
# 패턴: Arrange -> Act -> Assert
```

---

## Implementation Phases

### Phase 1: Foundation - Data Models & Segment Classification
**Goal**: SegmentType enum, URL 패턴 관련 Pydantic 모델, classify_segment() 함수 구현
**Estimated Time**: 2 hours
**Status**: Pending

#### Tasks

**RED: Write Failing Tests First**

- [ ] **Test 1.1**: SegmentType enum 및 패턴 관련 모델 단위 테스트
  - File(s): `tests/unit/models/test_crawl_types.py` (기존 파일에 추가)
  - Expected: Tests FAIL (red) because SegmentType, URLPattern, PatternGroup don't exist
  - Details:
    - `test_segment_type_has_all_six_values` — uuid, int, date, hash, slug, string 존재 확인
    - `test_segment_type_values_are_lowercase_strings` — 값이 소문자 문자열인지 확인
    - `test_url_pattern_creation_with_valid_data` — 정상 생성
    - `test_url_pattern_frozen_immutable` — frozen 모델 변경 시 에러
    - `test_pattern_group_creation_with_defaults` — max_samples 기본값 3
    - `test_pattern_group_tracks_total_count` — total_count 필드
    - `test_pattern_normalization_result_creation` — groups, 통계 필드 포함

- [ ] **Test 1.2**: classify_segment() 함수 단위 테스트
  - File(s): `tests/unit/crawler/test_url_pattern.py` (신규 파일)
  - Expected: Tests FAIL (red) because url_pattern module doesn't exist
  - Details — 세그먼트 타입별 테스트:
    - `test_classify_segment_uuid_v4_lowercase` — `550e8400-e29b-41d4-a716-446655440000` → uuid
    - `test_classify_segment_uuid_v4_uppercase` — `550E8400-E29B-41D4-A716-446655440000` → uuid
    - `test_classify_segment_pure_digits_returns_int` — `123` → int
    - `test_classify_segment_single_digit_returns_int` — `1` → int
    - `test_classify_segment_zero_returns_int` — `0` → int
    - `test_classify_segment_date_yyyy_mm_dd` — `2025-01-15` → date
    - `test_classify_segment_hash_md5_32_hex` — 32자 hex → hash
    - `test_classify_segment_hash_sha1_40_hex` — 40자 hex → hash
    - `test_classify_segment_hash_sha256_64_hex` — 64자 hex → hash
    - `test_classify_segment_slug_lowercase_hyphens` — `my-first-post` → slug
    - `test_classify_segment_slug_with_numbers` — `post-123-title` → slug
    - `test_classify_segment_plain_text_returns_none` — `users` → None (리터럴)
    - `test_classify_segment_mixed_case_returns_none` — `MyPage` → None (리터럴)
    - `test_classify_segment_empty_returns_none` — `""` → None
    - `test_classify_segment_priority_uuid_before_hash` — UUID 형식은 hash가 아닌 uuid
    - `test_classify_segment_priority_int_before_hash` — 순수 숫자는 hash가 아닌 int
    - `test_classify_segment_32_digit_number_returns_int` — 32자 순수 숫자 → int (int 우선)

**GREEN: Implement to Make Tests Pass**

- [ ] **Task 1.3**: Pydantic 모델 추가
  - File(s): `src/eazy/models/crawl_types.py`
  - Goal: Test 1.1 통과
  - Details:
    - `SegmentType(str, Enum)` — uuid, int, date, hash, slug, string
    - `URLPattern(BaseModel, frozen=True)` — scheme, netloc, pattern_path, segment_types
    - `PatternGroup(BaseModel)` — pattern, sample_urls, total_count, max_samples=3
    - `PatternNormalizationResult(BaseModel)` — groups, total_urls_processed, total_patterns_found, total_urls_skipped

- [ ] **Task 1.4**: classify_segment() 함수 구현
  - File(s): `src/eazy/crawler/url_pattern.py` (신규 파일)
  - Goal: Test 1.2 통과
  - Details:
    - PRD 명시 순서로 검사: uuid → int → date → hash → slug → string
    - 모듈 레벨 compiled regex 패턴 사용
    - 동적 타입에 매칭되면 `SegmentType` 반환, 리터럴이면 `None` 반환

**REFACTOR: Clean Up Code**

- [ ] **Task 1.5**: 코드 품질 개선
  - Files: `src/eazy/crawler/url_pattern.py`, `src/eazy/models/crawl_types.py`
  - Goal: 테스트 깨지지 않으면서 설계 개선
  - Checklist:
    - [ ] Regex 패턴을 모듈 상수로 추출 및 이름 지정
    - [ ] Google 스타일 docstring 추가
    - [ ] `__all__` export 리스트 정리
    - [ ] 불필요한 중복 제거

#### Quality Gate

**STOP: Do NOT proceed to Phase 2 until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Test coverage meets requirements

**Build & Tests**:
- [ ] **All Tests Pass**: 기존 109개 + 신규 테스트 전부 통과
- [ ] **No Flaky Tests**: 3회 연속 실행 시 일관된 결과

**Code Quality**:
- [ ] **Linting**: `uv run ruff check src/ tests/` — 에러 없음
- [ ] **Formatting**: `uv run ruff format --check src/ tests/` — 변경 없음
- [ ] **Type Safety**: 모든 함수에 타입 힌트 적용

**Validation Commands**:
```bash
# 테스트 실행
uv run pytest tests/ -v

# 커버리지 확인
uv run pytest tests/ --cov=src/eazy --cov-report=term-missing

# 린팅
uv run ruff check src/ tests/

# 포맷팅 확인
uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [ ] `classify_segment("550e8400-e29b-41d4-a716-446655440000")` → `SegmentType.UUID`
- [ ] `classify_segment("12345")` → `SegmentType.INT`
- [ ] `classify_segment("users")` → `None`

---

### Phase 2: Core Logic - Pattern Normalization & Grouping
**Goal**: URLPatternNormalizer 클래스 구현 (normalize, add_url, should_skip, get_results)
**Estimated Time**: 3 hours
**Status**: Pending

#### Tasks

**RED: Write Failing Tests First**

- [ ] **Test 2.1**: URL 패턴 정규화 단위 테스트
  - File(s): `tests/unit/crawler/test_url_pattern.py` (추가)
  - Expected: Tests FAIL (red) because URLPatternNormalizer doesn't exist
  - Details — 정규화 테스트:
    - `test_normalize_url_single_int_segment` — `/posts/123` → `/posts/<int>`
    - `test_normalize_url_uuid_segment` — `/items/550e8400-...` → `/items/<uuid>`
    - `test_normalize_url_multiple_dynamic_segments` — `/users/123/posts/456` → `/users/<int>/posts/<int>`
    - `test_normalize_url_no_dynamic_segments` — `/about` → `/about`
    - `test_normalize_url_mixed_literal_and_dynamic` — `/api/v2/users/123` → `/api/v2/users/<int>`
    - `test_normalize_url_root_path` — `/` → `/`
    - `test_normalize_url_preserves_scheme_and_host` — scheme, netloc 유지
    - `test_normalize_url_date_segment` — `/archive/2025-01-15` → `/archive/<date>`
    - `test_normalize_url_hash_segment` — `/commit/a1b2c3...` (40자 hex) → `/commit/<hash>`
    - `test_normalize_url_slug_segment` — `/blog/my-first-post` → `/blog/<slug>`

- [ ] **Test 2.2**: 그룹핑 및 샘플링 로직 단위 테스트
  - File(s): `tests/unit/crawler/test_url_pattern.py` (추가)
  - Expected: Tests FAIL (red)
  - Details — 그룹핑 테스트:
    - `test_add_url_first_url_returns_true` — 첫 URL은 항상 샘플링
    - `test_add_url_same_pattern_within_limit_returns_true` — 샘플 한도 내 → True
    - `test_add_url_same_pattern_exceeds_limit_returns_false` — 한도 초과 → False
    - `test_should_skip_unknown_pattern_returns_false` — 새 패턴 → 스킵 안 함
    - `test_should_skip_full_pattern_returns_true` — 한도 도달 패턴 → 스킵
    - `test_should_skip_partial_pattern_returns_false` — 한도 미달 → 스킵 안 함
    - `test_type_promotion_mixed_int_and_slug_to_string` — `/items/123` + `/items/my-item` → `/items/<string>`
    - `test_type_promotion_same_types_preserved` — `/items/123` + `/items/456` → `/items/<int>` 유지
    - `test_type_promotion_updates_existing_group` — 승격 시 기존 그룹의 패턴도 업데이트
    - `test_get_results_correct_statistics` — total_urls_processed, total_patterns_found, total_urls_skipped 정확
    - `test_get_results_multiple_groups` — 서로 다른 패턴은 별도 그룹
    - `test_custom_max_samples_value` — max_samples=5 설정 시 5개까지 샘플링
    - `test_add_url_literal_only_paths_each_separate_group` — `/about`, `/contact` 각각 별도 그룹 (동적 세그먼트 없음)
    - `test_add_url_query_params_ignored_in_pattern` — 쿼리 파라미터는 패턴에 영향 없음

**GREEN: Implement to Make Tests Pass**

- [ ] **Task 2.3**: URLPatternNormalizer 클래스 구현
  - File(s): `src/eazy/crawler/url_pattern.py`
  - Goal: Test 2.1 + Test 2.2 통과
  - Details:
    - `_compute_structural_key(path_segments)` — 리터럴 고정, 동적은 `*`로 마킹
    - `normalize_url_to_pattern(url)` — URL을 URLPattern으로 변환
    - `add_url(url) -> bool` — URL 등록, 샘플링 여부 반환
    - `should_skip(url) -> bool` — 패턴 그룹 한도 도달 여부
    - `get_results() -> PatternNormalizationResult` — 최종 결과 반환
    - 내부 `_PatternTracker` 자료구조로 증분 타입 승격 관리

**REFACTOR: Clean Up Code**

- [ ] **Task 2.4**: 코드 품질 개선
  - Files: `src/eazy/crawler/url_pattern.py`
  - Goal: 테스트 깨지지 않으면서 설계 개선
  - Checklist:
    - [ ] 헬퍼 메서드 추출 (복잡한 로직 분리)
    - [ ] 명확한 네이밍 확인
    - [ ] 인라인 문서 추가
    - [ ] dict lookup 최적화 확인

#### Quality Gate

**STOP: Do NOT proceed to Phase 3 until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: `url_pattern.py` 커버리지 80% 이상

**Build & Tests**:
- [ ] **All Tests Pass**: 기존 + Phase 1 + Phase 2 테스트 전부 통과
- [ ] **No Flaky Tests**: 3회 연속 실행 시 일관된 결과

**Code Quality**:
- [ ] **Linting**: `uv run ruff check src/ tests/` — 에러 없음
- [ ] **Formatting**: `uv run ruff format --check src/ tests/` — 변경 없음

**Validation Commands**:
```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src/eazy/crawler/url_pattern --cov-report=term-missing
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [ ] `/users/123` + `/users/456` + `/users/789` + `/users/999` → 3개만 샘플링, 1개 스킵
- [ ] `/items/123` + `/items/my-item` → 타입 승격으로 `/items/<string>`
- [ ] 서로 다른 구조의 URL은 별도 그룹으로 분리됨

---

### Phase 3: Integration - Engine, Config & Export
**Goal**: URLPatternNormalizer를 CrawlerEngine에 통합, CrawlConfig/CrawlResult 확장, JSON 내보내기 포함
**Estimated Time**: 2 hours
**Status**: Pending

#### Tasks

**RED: Write Failing Tests First**

- [ ] **Test 3.1**: CrawlConfig/CrawlResult 모델 확장 테스트
  - File(s): `tests/unit/models/test_crawl_types.py` (추가)
  - Expected: Tests FAIL (red) because new fields don't exist
  - Details:
    - `test_crawl_config_max_samples_per_pattern_default_3` — 기본값 3
    - `test_crawl_config_enable_pattern_normalization_default_true` — 기본 활성화
    - `test_crawl_result_has_pattern_groups_field` — pattern_groups 필드 존재
    - `test_crawl_result_pattern_groups_default_none` — 기본값 None (비활성 시)

- [ ] **Test 3.2**: CrawlerEngine 통합 테스트
  - File(s): `tests/integration/crawler/test_crawler_engine.py` (추가)
  - Expected: Tests FAIL (red) because engine doesn't use pattern normalizer
  - Details:
    - `test_crawl_with_pattern_normalization_skips_duplicate_patterns` — 동일 패턴 URL은 N개 이후 스킵
    - `test_crawl_without_pattern_normalization_crawls_all` — 비활성 시 전체 크롤링
    - `test_crawl_result_includes_pattern_groups` — 결과에 패턴 그룹 포함
    - `test_crawl_pattern_normalization_statistics` — "M개 발견, N개 샘플링" 통계

- [ ] **Test 3.3**: JSON 내보내기 통합 테스트
  - File(s): `tests/unit/crawler/test_exporter.py` (추가)
  - Expected: Tests FAIL (red) because exporter doesn't include pattern data
  - Details:
    - `test_export_json_includes_pattern_groups` — JSON 출력에 pattern_groups 포함
    - `test_export_json_pattern_group_has_statistics` — 그룹별 total_count, sample_urls 포함

**GREEN: Implement to Make Tests Pass**

- [ ] **Task 3.4**: CrawlConfig/CrawlResult 모델 확장
  - File(s): `src/eazy/models/crawl_types.py`
  - Goal: Test 3.1 통과
  - Details:
    - `CrawlConfig`에 추가: `max_samples_per_pattern: int = 3`, `enable_pattern_normalization: bool = True`
    - `CrawlResult`에 추가: `pattern_groups: PatternNormalizationResult | None = None`

- [ ] **Task 3.5**: CrawlerEngine에 URLPatternNormalizer 통합
  - File(s): `src/eazy/crawler/engine.py`
  - Goal: Test 3.2 통과
  - Details:
    - `__init__`에 `URLPatternNormalizer` 인스턴스 생성 (enable 옵션 확인)
    - BFS 루프에서 URL 처리 전 `should_skip()` 호출
    - URL 방문 후 `add_url()` 호출
    - `crawl()` 반환 시 `get_results()` 결과를 CrawlResult에 포함

- [ ] **Task 3.6**: JSON 내보내기 확인
  - File(s): `src/eazy/crawler/exporter.py`
  - Goal: Test 3.3 통과
  - Details:
    - Pydantic v2 `model_dump(mode="json")`이 새 필드도 자동 직렬화하므로, exporter 코드 변경 불필요할 가능성 높음
    - 필요 시 `PatternNormalizationResult`의 직렬화 확인

**REFACTOR: Clean Up Code**

- [ ] **Task 3.7**: 통합 코드 품질 개선
  - Files: `src/eazy/crawler/engine.py`, `src/eazy/models/crawl_types.py`
  - Goal: 테스트 깨지지 않으면서 설계 개선
  - Checklist:
    - [ ] 기존 109개 테스트 전부 통과 재확인 (backward compatibility)
    - [ ] engine.py의 패턴 정규화 로직이 깔끔하게 분리되어 있는지 확인
    - [ ] CrawlConfig의 새 옵션이 기존 동작에 영향 없는지 확인
    - [ ] `__init__.py` export 정리

#### Quality Gate

**STOP: Do NOT proceed until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: 전체 커버리지 80% 이상

**Build & Tests**:
- [ ] **Build**: 프로젝트 에러 없이 빌드
- [ ] **All Tests Pass**: 기존 109개 + 전체 신규 테스트 통과
- [ ] **No Flaky Tests**: 3회 연속 실행 시 일관된 결과

**Code Quality**:
- [ ] **Linting**: `uv run ruff check src/ tests/` — 에러 없음
- [ ] **Formatting**: `uv run ruff format --check src/ tests/` — 변경 없음
- [ ] **Type Safety**: 모든 새 함수에 타입 힌트 적용

**Security & Performance**:
- [ ] **Dependencies**: 추가 패키지 없음 (보안 취약점 해당 없음)
- [ ] **Performance**: dict 기반 O(1) 패턴 조회, 성능 회귀 없음
- [ ] **Memory**: URL 수에 비례한 선형 메모리 사용

**Documentation**:
- [ ] **Code Comments**: 복잡한 타입 승격 로직에 인라인 주석
- [ ] **Docstring**: 모든 public 함수에 Google 스타일 docstring

**Validation Commands**:
```bash
# 전체 테스트 실행
uv run pytest tests/ -v

# 전체 커버리지 확인
uv run pytest tests/ --cov=src/eazy --cov-report=term-missing

# 린팅 + 포맷팅
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [ ] 패턴 정규화 활성 상태에서 동일 구조 URL 4개 중 3개만 크롤링 확인
- [ ] 패턴 정규화 비활성 시 모든 URL 크롤링 확인
- [ ] JSON 출력에 `pattern_groups` 필드와 통계 포함 확인

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| 타입 승격 시 기존 그룹 키 변경 필요 | Medium | Low | 구조적 키(structural key) 기반 그룹핑으로 키 불변 보장. 타입만 내부적으로 업데이트 |
| 기존 109개 테스트 깨짐 | Low | High | 모든 새 필드에 기본값 설정. 각 Phase 완료 시 전체 테스트 스위트 실행 |
| 세그먼트 분류 엣지 케이스 | Medium | Low | Phase 1에서 17개 이상의 분류 단위 테스트로 커버 |
| 대규모 URL 세트에서 성능 저하 | Low | Medium | dict 기반 O(1) 조회. 필요 시 structural key 해싱 최적화 |
| engine.py BFS 루프 복잡도 증가 | Medium | Medium | `should_skip()` 단일 호출로 로직 캡슐화. 엔진 코드 변경 최소화 |

---

## Rollback Strategy

### If Phase 1 Fails
**Steps to revert**:
- `src/eazy/crawler/url_pattern.py` 삭제
- `src/eazy/models/crawl_types.py`에서 추가한 모델 제거
- `tests/unit/crawler/test_url_pattern.py` 삭제
- `tests/unit/models/test_crawl_types.py`에서 추가한 테스트 제거

### If Phase 2 Fails
**Steps to revert**:
- Phase 1 완료 상태로 복원
- `src/eazy/crawler/url_pattern.py`에서 URLPatternNormalizer 제거
- 관련 테스트 제거

### If Phase 3 Fails
**Steps to revert**:
- Phase 2 완료 상태로 복원
- `src/eazy/crawler/engine.py` 원본 복원
- `src/eazy/models/crawl_types.py`에서 CrawlConfig/CrawlResult 변경 복원
- 통합 테스트 제거

---

## Progress Tracking

### Completion Status
- **Phase 1**: 0%
- **Phase 2**: 0%
- **Phase 3**: 0%

**Overall Progress**: 0% complete

### Time Tracking
| Phase | Estimated | Actual | Variance |
|-------|-----------|--------|----------|
| Phase 1 | 2 hours | - | - |
| Phase 2 | 3 hours | - | - |
| Phase 3 | 2 hours | - | - |
| **Total** | **7 hours** | - | - |

---

## Notes & Learnings

### Implementation Notes
- (구현 중 발견사항 기록 예정)

### Blockers Encountered
- (없음)

### Improvements for Future Plans
- (구현 완료 후 기록 예정)

---

## References

### Documentation
- PRD REQ-001 URL 패턴 정규화 스펙: `plan/PRD.md` (lines 92-112)
- 기존 크롤링 엔진 소스: `src/eazy/crawler/`
- Pydantic v2 문서: https://docs.pydantic.dev/latest/

### Related Issues
- Branch: `feature/req-001-url-pattern-normalization`
- Commit 824b3b0: "docs: add URL pattern normalization spec to REQ-001"

---

## Final Checklist

**Before marking plan as COMPLETE**:
- [ ] All phases completed with quality gates passed
- [ ] Full integration testing performed
- [ ] 기존 109개 테스트 + 신규 테스트 전부 통과
- [ ] 전체 커버리지 80% 이상
- [ ] PRD REQ-001 마지막 AC 체크 (`[ ] URL 패턴 정규화...` → `[x]`)
- [ ] Plan document archived for future reference
