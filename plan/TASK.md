# Implementation Plan: REQ-002A Smart Crawling Engine (Core)

**Status**: 🔄 In Progress
**Started**: 2026-02-13
**Last Updated**: 2026-02-13 (Phase 3 complete)
**Estimated Completion**: 2026-02-20

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

Playwright 기반 헤드리스 브라우저로 실제 사용자와 동일하게 웹 페이지를 탐색하여 페이지 구조, 폼, API 엔드포인트를 자동으로 식별하는 스마트 크롤링 엔진. REQ-001(정규식 크롤링)이 정적 HTML만 분석하는 반면, REQ-002A는 JavaScript 렌더링이 필요한 SPA(Single Page Application)까지 지원한다.

### Success Criteria
- [ ] Playwright 기반 헤드리스 브라우저로 실제 사용자와 동일하게 페이지를 탐색한다
- [ ] JavaScript 렌더링이 필요한 SPA를 지원한다
- [ ] 폼 필드, 버튼, 링크, API 호출을 자동으로 식별한다
- [ ] 크롤링 결과를 지식 그래프 형태로 구조화한다
- [ ] 크롤링 깊이 및 범위를 사용자가 설정할 수 있다
- [ ] robots.txt 및 크롤링 제한 정책을 준수할 수 있는 옵션을 제공한다

### User Impact

보안 담당자가 대상 웹 애플리케이션의 URL만 입력하면, SPA를 포함한 모든 페이지와 API 엔드포인트가 자동으로 매핑된다. 기존 정규식 크롤러가 놓치는 JavaScript 동적 콘텐츠와 XHR/fetch API 호출까지 탐지하여 진단 범위 누락을 방지한다.

---

## Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| 별도 `SmartCrawlerEngine` 클래스 (기존 `CrawlerEngine` 확장 대신) | regex 크롤러(httpx)와 smart 크롤러(Playwright)는 근본적으로 다른 동작. 기존 엔진 안정성 보존 | 일부 로직 중복(BFS, scope check) 가능하나 composition으로 해결 |
| `BrowserManager` 분리 | Playwright 브라우저 생명주기(시작/종료/페이지 관리)를 크롤링 로직과 분리하여 테스트 용이성 확보 | 파일 하나 추가되지만 SRP 준수 |
| `PageAnalyzer` 분리 | 렌더링된 DOM 분석 로직을 엔진에서 분리. 기존 `regex_parser`와 대응되는 역할 | 추상화 레이어 하나 추가 |
| `NetworkInterceptor` 분리 | XHR/fetch 캡처를 DOM 분석과 별도 관심사로 분리. 실패 모드가 다름(selector vs timing) | Phase 2B에서 별도 TDD cycle |
| Knowledge Graph를 `crawl_types.py`에 정의 | 기존 모델들과 일관된 위치. CrawlResult에서 참조 가능 | crawl_types.py가 커지나 현재 규모에서 문제없음 |
| `page.route()` 기반 테스트 | 실제 Playwright 브라우저 사용하되 네트워크를 가로채서 제어. respx 패턴과 유사 | CI에 브라우저 설치 필요하나 가장 현실적 |
| REQ-002B 확장 고려 | PageAnalyzer에 LLM 주입 가능한 구조 설계. 직접 LLM 호출은 안 함 | 약간의 추상화 오버헤드 |

---

## Dependencies

### Required Before Starting
- [x] REQ-001 정규식 크롤링 엔진 완료 (215 tests, 98% coverage)
- [x] 기존 모듈 동작 확인: url_resolver, robots_parser, url_pattern, sitemap, exporter

### External Dependencies
- `playwright>=1.40` (신규 추가)
- Chromium 브라우저 바이너리 (`playwright install chromium`)

---

## Test Strategy

### Testing Approach
**TDD Principle**: Write tests FIRST, then implement to make them pass

**Playwright Test Guidelines**:
- ALWAYS use `async with` or fixture teardown로 browser/page 정리
- NEVER share browser context between tests (state leakage 방지)
- page.wait_for_selector() 사용, time.sleep() 금지
- page.on() listener는 테스트 후 반드시 cleanup

### Test Pyramid for This Feature
| Test Type | Coverage Target | Purpose |
|-----------|-----------------|---------|
| **Unit Tests** | >=80% | BrowserManager, PageAnalyzer, NetworkInterceptor, GraphBuilder |
| **Integration Tests** | Critical paths | SmartCrawlerEngine 전체 워크플로우, CLI 통합 |
| **E2E Tests** | Key user flows | 크롤링→그래프→JSON 내보내기 전체 파이프라인 |

### Test File Organization
```
tests/
├── unit/
│   ├── crawler/
│   │   ├── test_browser_manager.py     # [NEW] 브라우저 생명주기 테스트
│   │   ├── test_page_analyzer.py       # [NEW] DOM 분석 테스트
│   │   ├── test_network_interceptor.py # [NEW] API 캡처 테스트
│   │   └── test_graph_builder.py       # [NEW] 그래프 변환 테스트
│   └── models/
│       └── test_crawl_types.py         # [MODIFY] 새 모델 테스트 추가
├── integration/
│   └── crawler/
│       └── test_smart_engine.py        # [NEW] 스마트 크롤링 통합 테스트
```

### Coverage Requirements by Phase
- **Phase 1 (Foundation)**: BrowserManager + 모델 단위 테스트 (>=80%)
- **Phase 2A (DOM Analysis)**: PageAnalyzer 단위 테스트 (>=80%)
- **Phase 2B (Network Capture)**: NetworkInterceptor 단위 테스트 (>=80%)
- **Phase 3 (Engine)**: SmartCrawlerEngine 통합 테스트 (>=80%)
- **Phase 4 (Graph)**: KnowledgeGraph + GraphBuilder 테스트 (>=80%)
- **Phase 5 (CLI)**: CLI 통합 테스트 (>=70%)

### Test Naming Convention
```python
# File: test_{module_name}.py
# Class: Test{ComponentName}
# Function: test_{behavior}_{condition}_{expected_result}
# Example: test_extract_links_from_rendered_dom_returns_absolute_urls
# Pattern: Arrange -> Act -> Assert
```

---

## Implementation Phases

### Phase 1: Foundation - Dependencies & BrowserManager
**Goal**: Playwright 의존성 설정, CrawlConfig 확장, BrowserManager 클래스 구현
**Estimated Time**: 3 hours
**Status**: ✅ Complete (228 tests, 99% coverage on new code)

#### Tasks

**RED: Write Failing Tests First**

- [x] **Test 1.1**: CrawlConfig 스마트 크롤링 필드 확장 테스트 (6 tests)
  - File(s): `tests/unit/models/test_crawl_types.py` (기존 파일에 추가)
  - Expected: Tests FAIL (red) because new fields don't exist
  - Details:
    - `test_crawl_config_headless_default_true` — headless 기본값 True
    - `test_crawl_config_wait_until_default_networkidle` — wait_until 기본값 "networkidle"
    - `test_crawl_config_viewport_width_default_1280` — viewport_width 기본값 1280
    - `test_crawl_config_viewport_height_default_720` — viewport_height 기본값 720
    - `test_crawl_config_auto_detect_spa_default_true` — SPA 자동 감지 기본 활성
    - `test_crawl_config_smart_fields_backward_compatible` — 기존 테스트 깨지지 않음

- [x] **Test 1.2**: BrowserManager 클래스 단위 테스트 (7 tests)
  - File(s): `tests/unit/crawler/test_browser_manager.py` (신규 파일)
  - Expected: Tests FAIL (red) because BrowserManager doesn't exist
  - Details:
    - `test_browser_manager_async_context_manager_starts_browser` — async with 패턴으로 브라우저 시작
    - `test_browser_manager_async_context_manager_closes_on_exit` — 컨텍스트 종료 시 브라우저 닫힘
    - `test_browser_manager_closes_browser_on_exception` — 예외 시에도 정리
    - `test_browser_manager_creates_page_with_viewport` — 페이지 생성 + 뷰포트 설정
    - `test_browser_manager_sets_user_agent` — UA 설정
    - `test_browser_manager_headless_mode` — headless 모드 확인
    - `test_browser_manager_reuses_browser_across_pages` — 브라우저 재사용, 페이지만 새로 생성

**GREEN: Implement to Make Tests Pass**

- [x] **Task 1.3**: 의존성 추가 및 CrawlConfig 확장
  - File(s): `pyproject.toml`, `src/eazy/models/crawl_types.py`
  - Goal: Test 1.1 통과
  - Details:
    - `pyproject.toml`에 `playwright>=1.40` 의존성 추가
    - CrawlConfig에 추가 필드:
      - `headless: bool = True`
      - `wait_until: Literal["networkidle", "domcontentloaded", "load", "commit"] = "networkidle"`
      - `viewport_width: int = 1280`
      - `viewport_height: int = 720`
      - `auto_detect_spa: bool = True`

- [x] **Task 1.4**: BrowserManager 클래스 구현
  - File(s): `src/eazy/crawler/browser_manager.py` (신규 파일)
  - Goal: Test 1.2 통과
  - Details:
    - async context manager (`__aenter__`, `__aexit__`)
    - `launch()` — Chromium 브라우저 시작
    - `new_page()` — 새 페이지 생성 (viewport, UA 설정)
    - `close()` — 브라우저 종료
    - CrawlConfig에서 headless, viewport, user_agent 읽기

**REFACTOR: Clean Up Code**

- [x] **Task 1.5**: 코드 품질 개선
  - Files: `src/eazy/crawler/browser_manager.py`, `src/eazy/models/crawl_types.py`
  - Goal: 테스트 깨지지 않으면서 설계 개선
  - Checklist:
    - [x] Google 스타일 docstring 추가
    - [x] `__all__` export 리스트 정리
    - [x] Playwright conftest fixture — 불필요 (unittest.mock으로 충분)
    - [x] 기존 215개 테스트 전부 통과 재확인 (228 total)

#### Quality Gate

**STOP: Do NOT proceed to Phase 2A until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [x] **Red Phase**: Tests were written FIRST and initially failed
- [x] **Green Phase**: Production code written to make tests pass
- [x] **Refactor Phase**: Code improved while tests still pass
- [x] **Coverage Check**: BrowserManager 97%, crawl_types 100%

**Build & Tests**:
- [x] **All Tests Pass**: 215 existing + 13 new = 228 total passed
- [x] **No Flaky Tests**: 일관된 결과
- [x] **Playwright Install**: `playwright install chromium` 정상 동작

**Code Quality**:
- [x] **Linting**: `uv run ruff check src/ tests/` — All checks passed
- [x] **Formatting**: `uv run ruff format --check src/ tests/` — 40 files already formatted
- [x] **Type Safety**: 모든 함수에 타입 힌트 적용

**Validation Commands**:
```bash
# 의존성 설치 (최초 1회)
uv sync
playwright install chromium

# 테스트 실행
uv run pytest tests/ -v

# 커버리지 확인
uv run pytest tests/ --cov=src/eazy --cov-report=term-missing

# 린팅/포맷팅
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [x] `BrowserManager(config)` async with 패턴으로 브라우저 시작/종료 확인
- [x] 새 CrawlConfig 필드가 기존 코드에 영향 없음 확인 (215 기존 테스트 전부 통과)
- [x] Playwright Chromium 정상 설치 확인

---

### Phase 2A: Page Analyzer - DOM Analysis
**Goal**: 렌더링된 DOM에서 링크, 폼, 버튼을 추출하는 PageAnalyzer 클래스 구현 + SPA 감지
**Estimated Time**: 2 hours
**Status**: ✅ Complete (240 tests, 87% coverage on PageAnalyzer)

#### Tasks

**RED: Write Failing Tests First**

- [x] **Test 2A.1**: PageAnalyzer DOM 추출 단위 테스트
  - File(s): `tests/unit/crawler/test_page_analyzer.py` (신규 파일)
  - Expected: Tests FAIL (red) because PageAnalyzer doesn't exist
  - Details:
    - `test_extract_links_from_rendered_dom_returns_absolute_urls` — <a> 태그에서 링크 추출
    - `test_extract_links_skips_javascript_href` — `href="javascript:void(0)"` 무시
    - `test_extract_links_skips_anchor_only_href` — `href="#section"` 무시
    - `test_extract_forms_from_rendered_page` — <form> 필드 추출 (action, method, inputs)
    - `test_extract_forms_from_spa_dynamic_content` — JS 렌더링 후 동적 폼 추출
    - `test_extract_buttons_with_type_submit` — submit 버튼 추출
    - `test_extract_buttons_with_onclick` — onclick 핸들러 있는 버튼 추출
    - `test_handle_empty_page_returns_empty_results` — 빈 페이지 처리
    - `test_extract_page_title_from_rendered_dom` — <title> 추출

- [x] **Test 2A.2**: SPA 감지 테스트
  - File(s): `tests/unit/crawler/test_page_analyzer.py` (추가)
  - Expected: Tests FAIL (red)
  - Details:
    - `test_detect_spa_static_html_returns_false` — 정적 HTML은 SPA 아님
    - `test_detect_spa_large_dom_diff_returns_true` — JS 렌더링으로 DOM이 크게 변한 경우 SPA
    - `test_detect_spa_react_root_marker_returns_true` — `<div id="root">` 등 SPA 프레임워크 마커 감지

**GREEN: Implement to Make Tests Pass**

- [x] **Task 2A.3**: PageAnalyzer 클래스 구현
  - File(s): `src/eazy/crawler/page_analyzer.py` (신규 파일)
  - Goal: Test 2A.1 + Test 2A.2 통과
  - Details:
    - `extract_links(page) -> list[str]` — Playwright 셀렉터로 <a> 태그 추출, 절대 URL 변환
    - `extract_forms(page) -> list[FormData]` — <form> 태그 + <input> 필드 추출
    - `extract_buttons(page) -> list[ButtonInfo]` — <button> 태그 추출
    - `extract_title(page) -> str | None` — <title> 추출
    - `detect_spa(page) -> bool` — SPA 감지 (DOM 크기 비교 + 프레임워크 마커)
    - `analyze(page) -> PageAnalysisResult` — 위 메서드들을 통합 실행
    - 기존 `FormData`, `ButtonInfo` 모델 재사용

**REFACTOR: Clean Up Code**

- [x] **Task 2A.4**: 코드 품질 개선
  - Files: `src/eazy/crawler/page_analyzer.py`
  - Goal: 테스트 깨지지 않으면서 설계 개선
  - Checklist:
    - [x] Google 스타일 docstring 추가
    - [x] 셀렉터 상수를 모듈 레벨로 추출
    - [x] 에러 처리 (셀렉터 실패 시 빈 결과 반환)
    - [ ] REQ-002B 확장 포인트 주석 (LLM 주입 가능 위치)

#### Quality Gate

**STOP: Do NOT proceed to Phase 2B until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [x] **Red Phase**: Tests were written FIRST and initially failed
- [x] **Green Phase**: Production code written to make tests pass
- [x] **Refactor Phase**: Code improved while tests still pass
- [x] **Coverage Check**: PageAnalyzer 커버리지 87% (>= 80%)

**Build & Tests**:
- [x] **All Tests Pass**: 228 existing + 12 new = 240 total passed
- [x] **No Flaky Tests**: 일관된 결과

**Code Quality**:
- [x] **Linting**: `uv run ruff check src/ tests/` — All checks passed
- [x] **Formatting**: `uv run ruff format --check src/ tests/` — Already formatted

**Validation Commands**:
```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=eazy.crawler.page_analyzer --cov-report=term-missing
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [x] 정적 HTML에서 링크/폼/버튼 정확히 추출 확인
- [x] SPA(JS 렌더링 콘텐츠)에서 동적 요소 추출 확인
- [x] SPA 감지 로직이 정적/동적 페이지를 올바르게 구분

---

### Phase 2B: Network Interceptor - API Endpoint Capture
**Goal**: Playwright의 네트워크 이벤트를 캡처하여 XHR/fetch API 호출을 식별
**Estimated Time**: 2 hours
**Status**: ✅ Complete (248 tests, 100% coverage on NetworkInterceptor)

#### Tasks

**RED: Write Failing Tests First**

- [x] **Test 2B.1**: NetworkInterceptor 단위 테스트
  - File(s): `tests/unit/crawler/test_network_interceptor.py` (신규 파일)
  - Expected: Tests FAIL (red) because NetworkInterceptor doesn't exist
  - Details:
    - `test_capture_xhr_requests_returns_endpoint_info` — XHR 요청 캡처
    - `test_capture_fetch_requests_returns_endpoint_info` — fetch 요청 캡처
    - `test_capture_ignores_static_resources` — CSS, JS, 이미지 등 정적 리소스 무시
    - `test_capture_includes_request_method` — GET, POST 등 메서드 포함
    - `test_capture_includes_request_url` — 요청 URL 포함
    - `test_capture_deduplicates_identical_api_calls` — 동일 API 호출 중복 제거
    - `test_start_capture_before_navigation_captures_initial_requests` — 네비게이션 전 시작하면 초기 요청도 캡처
    - `test_stop_capture_returns_collected_endpoints` — 캡처 중지 후 결과 반환

**GREEN: Implement to Make Tests Pass**

- [x] **Task 2B.2**: NetworkInterceptor 클래스 구현
  - File(s): `src/eazy/crawler/network_interceptor.py` (신규 파일)
  - Goal: Test 2B.1 통과
  - Details:
    - `start(page)` — `page.on("request", handler)` 등록
    - `stop()` — listener 제거 + 결과 반환
    - `get_endpoints() -> list[EndpointInfo]` — 캡처된 API 엔드포인트 반환
    - 필터링: `resource_type`이 `xhr` 또는 `fetch`인 요청만 캡처
    - 정적 리소스 무시: `stylesheet`, `image`, `font`, `script` 타입 제외
    - 기존 `EndpointInfo` 모델 재사용

**REFACTOR: Clean Up Code**

- [x] **Task 2B.3**: 코드 품질 개선
  - Files: `src/eazy/crawler/network_interceptor.py`
  - Goal: 테스트 깨지지 않으면서 설계 개선
  - Checklist:
    - [x] Google 스타일 docstring 추가
    - [x] listener cleanup 보장 (stop()에서 remove_listener 호출)
    - [x] 중복 제거 로직 최적화 (set[tuple[str, str]] + frozenset 필터)

#### Quality Gate

**STOP: Do NOT proceed to Phase 3 until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [x] **Red Phase**: Tests were written FIRST and initially failed
- [x] **Green Phase**: Production code written to make tests pass
- [x] **Refactor Phase**: Code improved while tests still pass
- [x] **Coverage Check**: NetworkInterceptor 커버리지 100% (>= 80%)

**Build & Tests**:
- [x] **All Tests Pass**: 240 existing + 8 new = 248 total passed
- [x] **No Flaky Tests**: 일관된 결과

**Code Quality**:
- [x] **Linting**: `uv run ruff check src/ tests/` — All checks passed
- [x] **Formatting**: `uv run ruff format --check src/ tests/` — Already formatted

**Validation Commands**:
```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=eazy.crawler.network_interceptor --cov-report=term-missing
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [x] XHR 요청이 EndpointInfo로 정확히 캡처됨
- [x] fetch 요청이 EndpointInfo로 정확히 캡처됨
- [x] 이미지/CSS/폰트 등 정적 리소스는 무시됨

---

### Phase 3: Smart Crawler Engine - Core Crawling Logic
**Goal**: SmartCrawlerEngine 클래스 — Playwright 기반 BFS 크롤링, 기존 모듈 재사용
**Estimated Time**: 4 hours
**Status**: ✅ Complete

#### Tasks

**RED: Write Failing Tests First**

- [x] **Test 3.1**: SmartCrawlerEngine 기본 크롤링 테스트
  - File(s): `tests/integration/crawler/test_smart_engine.py` (신규 파일)
  - Expected: Tests FAIL (red) because SmartCrawlerEngine doesn't exist
  - Details:
    - `test_crawl_single_page_returns_page_result` — 단일 페이지 크롤링
    - `test_crawl_follows_links_to_next_page` — 링크 따라가기
    - `test_crawl_extracts_forms_and_buttons` — 폼/버튼 추출
    - `test_crawl_captures_api_endpoints` — API 엔드포인트 캡처
    - `test_crawl_spa_javascript_rendered_content` — SPA 콘텐츠 크롤링
    - `test_crawl_returns_crawl_result_with_statistics` — CrawlResult 반환

- [x] **Test 3.2**: 설정 및 제약 조건 테스트
  - File(s): `tests/integration/crawler/test_smart_engine.py` (추가)
  - Expected: Tests FAIL (red)
  - Details:
    - `test_crawl_respects_max_depth` — 깊이 제한
    - `test_crawl_respects_max_pages` — 페이지 수 제한
    - `test_crawl_respects_robots_txt` — robots.txt 준수
    - `test_crawl_enforces_scope` — 외부 도메인 차단
    - `test_crawl_handles_navigation_timeout` — 타임아웃 처리
    - `test_crawl_handles_page_error` — 페이지 에러 처리 (4xx, 5xx)
    - `test_crawl_deduplicates_with_url_pattern_normalizer` — URL 패턴 정규화 재사용
    - `test_crawl_excludes_urls_matching_exclude_patterns` — 제외 패턴

**GREEN: Implement to Make Tests Pass**

- [x] **Task 3.3**: SmartCrawlerEngine 클래스 구현
  - File(s): `src/eazy/crawler/smart_engine.py` (신규 파일)
  - Goal: Test 3.1 + Test 3.2 통과
  - Details:
    - `__init__(config: CrawlConfig)` — 설정 + BrowserManager + PageAnalyzer + NetworkInterceptor 초기화
    - `async crawl() -> CrawlResult` — BFS 크롤링 실행
    - BFS deque 기반 (url, depth, parent_url) 큐
    - 각 페이지: BrowserManager.new_page() → NetworkInterceptor.start() → page.goto() → PageAnalyzer.analyze() → NetworkInterceptor.stop()
    - 기존 모듈 재사용: `url_resolver.resolve_url()`, `url_resolver.normalize_url()`, `url_resolver.is_in_scope()`, `RobotsParser`, `URLPatternNormalizer`, `Sitemap`
    - CrawlResult 구성 with statistics

- [x] **Task 3.4**: 기존 모듈 통합 검증
  - File(s): `src/eazy/crawler/smart_engine.py`
  - Goal: 기존 url_resolver, robots_parser, url_pattern 모듈과 정상 연동 확인
  - Details:
    - robots.txt는 httpx로 직접 fetch (Playwright 불필요)
    - URL 정규화/스코프 체크는 기존 함수 그대로 사용
    - 패턴 정규화는 기존 URLPatternNormalizer 재사용

**REFACTOR: Clean Up Code**

- [x] **Task 3.5**: 코드 품질 개선
  - Files: `src/eazy/crawler/smart_engine.py`
  - Goal: 테스트 깨지지 않으면서 설계 개선
  - Checklist:
    - [x] Google 스타일 docstring 추가
    - [x] BFS 로직 가독성 개선
    - [x] 에러 처리 통합 (navigation error, timeout, connection error)
    - [x] 리소스 정리 보장 (모든 경로에서 browser close)

#### Quality Gate

**STOP: Do NOT proceed to Phase 4 until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [x] **Red Phase**: Tests were written FIRST and initially failed
- [x] **Green Phase**: Production code written to make tests pass
- [x] **Refactor Phase**: Code improved while tests still pass
- [x] **Coverage Check**: SmartCrawlerEngine 커버리지 96% (>= 80%)

**Build & Tests**:
- [x] **All Tests Pass**: 262 tests passed (248 existing + 14 new)
- [x] **No Flaky Tests**: 일관된 결과

**Code Quality**:
- [x] **Linting**: `uv run ruff check src/ tests/` — 에러 없음
- [x] **Formatting**: `uv run ruff format --check src/ tests/` — 변경 없음
- [x] **Type Safety**: 모든 함수에 타입 힌트 적용

**Security & Performance**:
- [x] **Resource Cleanup**: 모든 경로에서 브라우저/페이지 정상 종료 (try/finally)
- [x] **Memory**: 페이지 방문 후 즉시 닫기로 메모리 관리

**Validation Commands**:
```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src/eazy/crawler/smart_engine --cov-report=term-missing
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Manual Test Checklist** (automated tests cover all):
- [x] 단일 정적 페이지 크롤링 → PageResult 반환 (`test_crawl_single_page_returns_page_result`)
- [x] 링크가 있는 사이트 크롤링 → 여러 페이지 탐색 (`test_crawl_follows_links_to_next_page`)
- [x] SPA 사이트 크롤링 → JS 렌더링 콘텐츠 추출 (`test_crawl_spa_javascript_rendered_content`)
- [x] max_depth=0 → 루트 페이지만 크롤링 (`test_crawl_respects_max_depth`)
- [x] robots.txt 차단 URL → 스킵 (`test_crawl_respects_robots_txt`)

---

### Phase 4: Knowledge Graph & Export
**Goal**: KnowledgeGraph 모델, GraphBuilder 변환기, JSON 내보내기
**Estimated Time**: 3 hours
**Status**: Pending

#### Tasks

**RED: Write Failing Tests First**

- [ ] **Test 4.1**: Knowledge Graph 모델 테스트
  - File(s): `tests/unit/models/test_crawl_types.py` (기존 파일에 추가)
  - Expected: Tests FAIL (red) because graph models don't exist
  - Details:
    - `test_graph_node_type_has_page_api_resource` — GraphNodeType enum 값
    - `test_graph_edge_type_has_hyperlink_form_api_redirect` — GraphEdgeType enum 값
    - `test_graph_node_creation` — GraphNode 생성 (url, type, metadata)
    - `test_graph_node_frozen_immutable` — frozen 모델
    - `test_graph_edge_creation` — GraphEdge 생성 (source, target, type)
    - `test_knowledge_graph_creation` — KnowledgeGraph 빈 생성
    - `test_knowledge_graph_add_node` — 노드 추가
    - `test_knowledge_graph_add_edge` — 엣지 추가
    - `test_knowledge_graph_get_nodes_by_type` — 타입별 노드 조회
    - `test_knowledge_graph_statistics` — 노드/엣지 수 통계

- [ ] **Test 4.2**: GraphBuilder 변환 테스트
  - File(s): `tests/unit/crawler/test_graph_builder.py` (신규 파일)
  - Expected: Tests FAIL (red) because GraphBuilder doesn't exist
  - Details:
    - `test_build_graph_from_crawl_result_creates_page_nodes` — 페이지당 노드 생성
    - `test_build_graph_includes_hyperlink_edges` — 링크 → hyperlink 엣지
    - `test_build_graph_includes_form_action_edges` — 폼 → form_action 엣지
    - `test_build_graph_includes_api_call_edges` — API → api_call 엣지
    - `test_build_graph_deduplicates_nodes_by_url` — URL 중복 노드 제거
    - `test_build_graph_empty_crawl_result_returns_empty_graph` — 빈 결과 처리
    - `test_export_graph_to_json_valid_format` — JSON 직렬화

**GREEN: Implement to Make Tests Pass**

- [ ] **Task 4.3**: Knowledge Graph 모델 추가
  - File(s): `src/eazy/models/crawl_types.py`
  - Goal: Test 4.1 통과
  - Details:
    - `GraphNodeType(str, Enum)` — page, api, resource
    - `GraphEdgeType(str, Enum)` — hyperlink, form_action, api_call, redirect
    - `GraphNode(BaseModel, frozen=True)` — url, node_type, metadata (dict)
    - `GraphEdge(BaseModel, frozen=True)` — source, target, edge_type, metadata (dict)
    - `KnowledgeGraph(BaseModel)` — nodes (dict[str, GraphNode]), edges (list[GraphEdge])
    - `add_node()`, `add_edge()`, `get_nodes_by_type()`, `statistics` property

- [ ] **Task 4.4**: GraphBuilder 클래스 구현
  - File(s): `src/eazy/crawler/graph_builder.py` (신규 파일)
  - Goal: Test 4.2 통과
  - Details:
    - `build(crawl_result: CrawlResult) -> KnowledgeGraph` — 변환 로직
    - 각 PageResult → GraphNode(type=PAGE)
    - 각 link → GraphEdge(type=HYPERLINK)
    - 각 form.action → GraphEdge(type=FORM_ACTION)
    - 각 api_endpoint → GraphNode(type=API) + GraphEdge(type=API_CALL)
    - URL 정규화로 중복 노드 제거
    - `to_json(graph: KnowledgeGraph) -> str` — JSON 내보내기

**REFACTOR: Clean Up Code**

- [ ] **Task 4.5**: 코드 품질 개선
  - Files: `src/eazy/models/crawl_types.py`, `src/eazy/crawler/graph_builder.py`
  - Goal: 테스트 깨지지 않으면서 설계 개선
  - Checklist:
    - [ ] Google 스타일 docstring 추가
    - [ ] `__all__` export 리스트 정리 (models/__init__.py 업데이트)
    - [ ] KnowledgeGraph 메서드 가독성 개선

#### Quality Gate

**STOP: Do NOT proceed to Phase 5 until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: GraphBuilder 커버리지 >= 80%, crawl_types.py 100%

**Build & Tests**:
- [ ] **All Tests Pass**: 기존 + Phase 1~4 테스트 전부 통과
- [ ] **No Flaky Tests**: 일관된 결과

**Code Quality**:
- [ ] **Linting**: `uv run ruff check src/ tests/` — 에러 없음
- [ ] **Formatting**: `uv run ruff format --check src/ tests/` — 변경 없음

**Validation Commands**:
```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src/eazy --cov-report=term-missing
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [ ] CrawlResult → KnowledgeGraph 변환 후 노드/엣지 수 정확
- [ ] JSON 출력에 nodes, edges 포함
- [ ] 중복 노드가 제거됨

---

### Phase 5: Integration & CLI
**Goal**: CLI에 `--smart` 옵션 추가, 전체 통합 테스트, CrawlResult에 KnowledgeGraph 포함
**Estimated Time**: 3 hours
**Status**: Pending

#### Tasks

**RED: Write Failing Tests First**

- [ ] **Test 5.1**: CLI 통합 테스트
  - File(s): `tests/unit/cli/test_crawl_command.py` (기존 파일에 추가)
  - Expected: Tests FAIL (red) because --smart option doesn't exist
  - Details:
    - `test_crawl_command_smart_option_exists` — --smart 옵션 인식
    - `test_crawl_command_smart_invokes_smart_engine` — --smart 시 SmartCrawlerEngine 사용
    - `test_crawl_command_without_smart_uses_regex_engine` — 기본은 기존 CrawlerEngine
    - `test_crawl_command_smart_output_json_includes_graph` — JSON 출력에 knowledge_graph 포함

- [ ] **Test 5.2**: 전체 통합 테스트
  - File(s): `tests/integration/crawler/test_smart_engine.py` (추가)
  - Expected: Tests FAIL (red)
  - Details:
    - `test_smart_crawl_end_to_end_workflow` — 크롤링 → 그래프 빌드 → JSON 내보내기 전체
    - `test_smart_crawl_result_includes_knowledge_graph` — CrawlResult에 KnowledgeGraph 포함
    - `test_smart_crawl_with_pattern_normalization` — URL 패턴 정규화 연동

**GREEN: Implement to Make Tests Pass**

- [ ] **Task 5.3**: CLI 명령어 확장
  - File(s): `src/eazy/cli/` (기존 CLI 파일 수정)
  - Goal: Test 5.1 통과
  - Details:
    - `eazy crawl` 명령에 `--smart` 옵션 추가
    - `--smart` 시 SmartCrawlerEngine 사용, 아니면 기존 CrawlerEngine
    - 결과에 KnowledgeGraph 포함 시 JSON에 `knowledge_graph` 필드 추가

- [ ] **Task 5.4**: CrawlResult에 KnowledgeGraph 통합
  - File(s): `src/eazy/models/crawl_types.py`, `src/eazy/crawler/smart_engine.py`
  - Goal: Test 5.2 통과
  - Details:
    - CrawlResult에 `knowledge_graph: KnowledgeGraph | None = None` 필드 추가
    - SmartCrawlerEngine.crawl()에서 GraphBuilder로 그래프 생성 후 CrawlResult에 포함
    - 기존 exporter가 자동 직렬화 (Pydantic model_dump)

**REFACTOR: Clean Up Code**

- [ ] **Task 5.5**: 최종 코드 품질 개선
  - Files: 전체 신규 파일
  - Goal: 테스트 깨지지 않으면서 최종 정리
  - Checklist:
    - [ ] 모든 `__init__.py` export 정리
    - [ ] 불필요한 import 제거
    - [ ] 전체 코드 린팅/포맷팅 최종 확인
    - [ ] 기존 215개 테스트 + 모든 신규 테스트 전부 통과

#### Quality Gate

**STOP: Do NOT mark complete until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: 전체 커버리지 >= 80%

**Build & Tests**:
- [ ] **Build**: 프로젝트 에러 없이 빌드
- [ ] **All Tests Pass**: 기존 215개 + 모든 신규 테스트 전부 통과
- [ ] **No Flaky Tests**: 일관된 결과 (3회 이상 실행)

**Code Quality**:
- [ ] **Linting**: `uv run ruff check src/ tests/` — 에러 없음
- [ ] **Formatting**: `uv run ruff format --check src/ tests/` — 변경 없음
- [ ] **Type Safety**: 모든 새 함수에 타입 힌트 적용

**Security & Performance**:
- [ ] **Dependencies**: `playwright` 보안 취약점 없음 확인
- [ ] **Resource Cleanup**: 모든 경로에서 브라우저 정상 종료
- [ ] **Memory**: 페이지 방문 후 즉시 닫기

**Documentation**:
- [ ] **Code Comments**: 복잡한 로직에 인라인 주석
- [ ] **Docstring**: 모든 public 함수에 Google 스타일 docstring

**Validation Commands**:
```bash
# 전체 테스트
uv run pytest tests/ -v

# 전체 커버리지
uv run pytest tests/ --cov=src/eazy --cov-report=term-missing

# 린팅/포맷팅
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [ ] `eazy crawl --smart https://example.com` 정상 동작
- [ ] `eazy crawl https://example.com` (기존) 정상 동작 (regression 없음)
- [ ] JSON 출력에 knowledge_graph 필드 포함

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| Playwright 브라우저 설치 CI 이슈 | Medium | High | CI에 `playwright install --with-deps chromium` 추가. 로컬 가이드 제공 |
| SPA 사이트별 로딩 완료 감지 어려움 | High | Medium | configurable wait strategy + SPA 자동 감지 조합. networkidle 기본값 |
| 기존 215 테스트 깨짐 | Low | High | 기존 CrawlConfig에 기본값 필드만 추가. backward compatible |
| Playwright 테스트 flakiness | Medium | Medium | page.route() 기반 네트워크 mock + proper cleanup fixture |
| 메모리 사용량 증가 (headless browser) | Medium | Medium | 단일 브라우저 인스턴스, 페이지 즉시 닫기, max_pages 제한 |
| 지식 그래프 대규모 사이트 성능 | Low | Medium | in-memory Pydantic → 향후 NetworkX/DB로 확장 가능 |

---

## Rollback Strategy

### If Phase 1 Fails
**Steps to revert**:
- `pyproject.toml`에서 playwright 의존성 제거
- `src/eazy/crawler/browser_manager.py` 삭제
- `src/eazy/models/crawl_types.py`에서 추가한 필드 제거
- `tests/unit/crawler/test_browser_manager.py` 삭제

### If Phase 2A/2B Fails
**Steps to revert**:
- Phase 1 완료 상태로 복원
- `src/eazy/crawler/page_analyzer.py` 삭제
- `src/eazy/crawler/network_interceptor.py` 삭제
- 관련 테스트 파일 삭제

### If Phase 3 Fails
**Steps to revert**:
- Phase 2B 완료 상태로 복원
- `src/eazy/crawler/smart_engine.py` 삭제
- `tests/integration/crawler/test_smart_engine.py` 삭제

### If Phase 4 Fails
**Steps to revert**:
- Phase 3 완료 상태로 복원
- `src/eazy/crawler/graph_builder.py` 삭제
- `src/eazy/models/crawl_types.py`에서 Graph 모델 제거
- 관련 테스트 제거

### If Phase 5 Fails
**Steps to revert**:
- Phase 4 완료 상태로 복원
- CLI 변경 복원
- CrawlResult에서 knowledge_graph 필드 제거
- 통합 테스트 제거

---

## Progress Tracking

### Completion Status
- **Phase 1**: 100% ✅
- **Phase 2A**: 100% ✅
- **Phase 2B**: 100% ✅
- **Phase 3**: 100% ✅
- **Phase 4**: 0%
- **Phase 5**: 0%

**Overall Progress**: 67% complete (4/6 phases)

### Time Tracking
| Phase | Estimated | Actual | Variance |
|-------|-----------|--------|----------|
| Phase 1 | 3 hours | ~30 min | -2.5h (faster) |
| Phase 2A | 2 hours | ~15 min | -1.75h (faster) |
| Phase 2B | 2 hours | ~10 min | -1.83h (faster) |
| Phase 3 | 4 hours | ~15 min | -3.75h (faster) |
| Phase 4 | 3 hours | - | - |
| Phase 5 | 3 hours | - | - |
| **Total** | **17 hours** | - | - |

---

## Notes & Learnings

### Implementation Notes
- Phase 1: Playwright mock with `unittest.mock.AsyncMock` + `@patch` — conftest fixture 불필요
- Phase 1: `TYPE_CHECKING` guard로 Playwright import overhead 최소화
- Phase 1: BrowserManager.close()는 idempotent (중복 호출 안전)
- Phase 2A: `_make_element(**attrs)` helper로 Playwright element mock 패턴화
- Phase 2A: `resolve_url()` 재사용으로 URL 변환 중복 제거
- Phase 2A: SPA 감지 = 프레임워크 마커(#root, #app 등) + script count threshold(>=5)
- Phase 2A: 모든 selector 호출을 try/except로 감싸서 실패 시 빈 결과 반환 (87% coverage, 미커버 라인은 except 분기)
- Phase 2B: `page.on()` / `page.remove_listener()` are sync — no async/await needed
- Phase 2B: MagicMock (not AsyncMock) for request handler tests, no `pytest.mark.asyncio`
- Phase 2B: `_API_RESOURCE_TYPES` as `ClassVar[frozenset[str]]` for O(1) membership check
- Phase 2B: Dedup via `set[tuple[str, str]]` keyed on (url, method) — simple and effective

### Blockers Encountered
- (Phase 진행 시 추가)

### Improvements for Future Plans
- (Phase 진행 시 추가)

---

## References

### Documentation
- PRD REQ-002A 스펙: `plan/PRD.md` (lines 115-129)
- Playwright Python docs: https://playwright.dev/python/
- 기존 크롤링 엔진: `src/eazy/crawler/engine.py`
- 기존 데이터 모델: `src/eazy/models/crawl_types.py`

### Related Issues
- Branch: `feature/req-002a-smart-crawling`
- 선행 작업: REQ-001 전체 완료 (feature/req-001-* 브랜치들)

---

## Final Checklist

**Before marking plan as COMPLETE**:
- [ ] All phases completed with quality gates passed
- [ ] Full integration testing performed
- [ ] 기존 215개 테스트 + 모든 신규 테스트 전부 통과
- [ ] 전체 커버리지 80% 이상
- [ ] PRD REQ-002A 6개 AC 모두 체크 완료
- [ ] Plan document archived for future reference
