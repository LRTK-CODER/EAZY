# Phase 4: 분석 모듈 (Analysis Modules)

**Status**: ⏳ Pending
**Started**: -
**Last Updated**: 2026-01-23
**Coverage Target**: 90% (Line), 85% (Branch)

---

**⚠️ CRITICAL INSTRUCTIONS**: After completing each section:
1. ✅ Check off completed task checkboxes
2. 🧪 Run all quality gate validation commands
3. ⚠️ Verify ALL quality gate items pass
4. 📅 Update "Last Updated" date above
5. ➡️ Only then proceed to next section

⛔ **DO NOT skip quality gates or proceed with failing checks**

---

## 📋 Overview

### Feature Description
JavaScript 소스 코드를 분석하여 숨겨진 자산(API 엔드포인트, 시크릿 등)을 발견합니다:
- **정규식 기반 분석**: 빠른 패턴 매칭 (QUICK, STANDARD 프로필)
- **AST 기반 분석**: 정밀한 구문 분석 (FULL 프로필)

### Success Criteria
- [ ] URL 문자열 리터럴 및 템플릿 리터럴 추출
- [ ] fetch, axios, jQuery AJAX, XHR 호출 탐지
- [ ] API 키, 시크릿 문자열 탐지
- [ ] React/Vue Router 경로 추출 (AST)
- [ ] 동적 URL 구성 패턴 탐지 (AST)

### Dependencies
- **Phase 1**: ScanProfile, DiscoveredAsset, BaseDiscoveryModule, DiscoveryContext

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| Regex first, AST optional | 성능/정밀도 트레이드오프 | 두 가지 구현 유지 |
| Python regex (re2) | 선형 시간 보장, ReDoS 방지 | 일부 고급 기능 미지원 |
| esprima/pyjsparser | 검증된 JavaScript 파서 | Python 순수 구현, 느림 |

---

## 🚀 Implementation Sections

### 4.1 JavaScript Static Analyzer (정규식)

**Goal**: 정규식 기반 빠른 JavaScript 분석 (QUICK, STANDARD 프로필)

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 4.1.1**: `test_url_string_literal()` - `"/api/users"` 추출
  - File: `backend/tests/unit/discovery/test_js_analyzer_regex.py`
  - Test Cases:
    - Extract single-quoted URL strings
    - Extract double-quoted URL strings
    - Filter non-URL strings
    - Handle escaped quotes

- [ ] **Test 4.1.2**: `test_url_template_literal()` - `` `/api/${id}` `` 추출
  - File: `backend/tests/unit/discovery/test_js_analyzer_regex.py`
  - Test Cases:
    - Extract template literal URLs
    - Identify variable placeholders
    - Handle nested expressions
    - Extract base path pattern

- [ ] **Test 4.1.3**: `test_fetch_call_detection()` - `fetch('/api')` 탐지
  - File: `backend/tests/unit/discovery/test_js_analyzer_regex.py`
  - Test Cases:
    - Detect fetch() calls
    - Extract first argument (URL)
    - Handle fetch with options object
    - Handle chained .then()

- [ ] **Test 4.1.4**: `test_axios_call_detection()` - `axios.get()` 탐지
  - File: `backend/tests/unit/discovery/test_js_analyzer_regex.py`
  - Test Cases:
    - Detect axios.get(), axios.post(), etc.
    - Detect axios() direct call
    - Extract URL argument
    - Handle axios.create() baseURL

- [ ] **Test 4.1.5**: `test_jquery_ajax_detection()` - `$.ajax()` 탐지
  - File: `backend/tests/unit/discovery/test_js_analyzer_regex.py`
  - Test Cases:
    - Detect $.ajax() calls
    - Detect $.get(), $.post() shortcuts
    - Extract url property
    - Handle various jQuery patterns

- [ ] **Test 4.1.6**: `test_xhr_open_detection()` - `xhr.open()` 탐지
  - File: `backend/tests/unit/discovery/test_js_analyzer_regex.py`
  - Test Cases:
    - Detect XMLHttpRequest.open()
    - Extract method and URL arguments
    - Handle various variable names
    - Detect new XMLHttpRequest()

- [ ] **Test 4.1.7**: `test_hardcoded_api_key()` - API 키 탐지
  - File: `backend/tests/unit/discovery/test_js_analyzer_regex.py`
  - Test Cases:
    - Detect common API key patterns (api_key, apiKey, API_KEY)
    - Detect service-specific patterns (sk-..., pk_...)
    - Filter false positives (placeholders, examples)
    - Flag high-entropy strings

- [ ] **Test 4.1.8**: `test_hardcoded_secret()` - 시크릿 문자열 탐지
  - File: `backend/tests/unit/discovery/test_js_analyzer_regex.py`
  - Test Cases:
    - Detect password, secret, token variables
    - Detect AWS credentials pattern
    - Detect private key patterns
    - Calculate Shannon entropy

- [ ] **Test 4.1.9**: `test_minified_code_handling()` - 미니파이 코드 처리
  - File: `backend/tests/unit/discovery/test_js_analyzer_regex.py`
  - Test Cases:
    - Handle single-line minified JS
    - Handle webpack bundles
    - Extract URLs from compressed code
    - Performance on large bundles

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 4.1.10**: `JsAnalyzerModule` (정규식 버전) 구현
  - File: `backend/app/services/discovery/modules/js_analyzer_regex.py`
  - Goal: Make Tests 4.1.1-4.1.9 pass
  - Components:
    - `UrlPatternMatcher`
    - `HttpClientDetector`
    - `SecretDetector`
    - `EntropyCalculator`
  - Implementation Notes:
    ```python
    class JsAnalyzerRegexModule(BaseDiscoveryModule):
        name = "js_analyzer_regex"
        profiles = {ScanProfile.QUICK, ScanProfile.STANDARD, ScanProfile.FULL}

        # Patterns
        URL_PATTERN = re.compile(r'''["'`](/[a-zA-Z0-9_/\-\.]+)["'`]''')
        FETCH_PATTERN = re.compile(r'''fetch\s*\(\s*["'`]([^"'`]+)["'`]''')
        # ... more patterns
    ```

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 4.1.11**: 정규식 최적화, False Positive 감소
  - Checklist:
    - [ ] Compile patterns once
    - [ ] Use non-capturing groups
    - [ ] Add URL validation
    - [ ] Whitelist/blacklist common false positives
    - [ ] Performance benchmarking

---

### 4.2 JavaScript Static Analyzer (AST) - Full 프로필

**Goal**: AST 기반 정밀 JavaScript 분석 (FULL 프로필)

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 4.2.1**: `test_react_router_extraction()` - React Router 경로
  - File: `backend/tests/unit/discovery/test_js_analyzer_ast.py`
  - Test Cases:
    - Extract `<Route path="/users">`
    - Extract `useNavigate()` targets
    - Handle nested routes
    - Extract from react-router-dom v6

- [ ] **Test 4.2.2**: `test_vue_router_extraction()` - Vue Router 경로
  - File: `backend/tests/unit/discovery/test_js_analyzer_ast.py`
  - Test Cases:
    - Extract routes array configuration
    - Extract `router.push()` targets
    - Handle dynamic routes (`:id`)
    - Extract from Vue Router 4

- [ ] **Test 4.2.3**: `test_dynamic_url_construction()` - `'/api/' + endpoint`
  - File: `backend/tests/unit/discovery/test_js_analyzer_ast.py`
  - Test Cases:
    - Detect string concatenation for URLs
    - Track variable values where possible
    - Handle URL construction in functions
    - Identify base URL patterns

- [ ] **Test 4.2.4**: `test_config_object_urls()` - 설정 객체 내 URL
  - File: `backend/tests/unit/discovery/test_js_analyzer_ast.py`
  - Test Cases:
    - Extract URLs from config objects
    - Handle nested configurations
    - Detect apiBaseUrl, endpoints objects
    - Handle environment-specific configs

- [ ] **Test 4.2.5**: `test_env_variable_reference()` - `process.env.API_URL`
  - File: `backend/tests/unit/discovery/test_js_analyzer_ast.py`
  - Test Cases:
    - Detect process.env references
    - Detect import.meta.env references
    - Flag environment variable names
    - Handle destructured env access

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 4.2.6**: `JsAnalyzerModule` (AST 버전) 구현
  - File: `backend/app/services/discovery/modules/js_analyzer_ast.py`
  - Goal: Make Tests 4.2.1-4.2.5 pass
  - Components:
    - `AstParser` (pyjsparser wrapper)
    - `RouterExtractor`
    - `UrlConstructionTracker`
    - `ConfigObjectAnalyzer`
  - Implementation Notes:
    ```python
    class JsAnalyzerAstModule(BaseDiscoveryModule):
        name = "js_analyzer_ast"
        profiles = {ScanProfile.FULL}  # Full profile only

        async def discover(self, context: DiscoveryContext) -> AsyncIterator[DiscoveredAsset]:
            for script in context.scripts:
                try:
                    ast = pyjsparser.parse(script.content)
                    yield from self._analyze_ast(ast)
                except Exception as e:
                    # Fallback to regex analyzer
                    logger.warning(f"AST parse failed, using regex: {e}")
    ```

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 4.2.7**: AST 파서 선택 (esprima/acorn), 메모리 최적화
  - Checklist:
    - [ ] Parser fallback chain
    - [ ] Incremental parsing for large files
    - [ ] AST caching
    - [ ] Memory limit enforcement
    - [ ] Timeout for complex files

---

## ✋ Quality Gate

**⚠️ STOP: Do NOT proceed to Phase 5 until ALL checks pass**

### TDD Compliance (CRITICAL)
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Line coverage ≥ 90%, Branch ≥ 85%

### Build & Tests
- [ ] **All Tests Pass**: `cd backend && pytest tests/unit/discovery/test_js_analyzer_*.py`
- [ ] **Coverage**: `cd backend && pytest --cov=app/services/discovery/modules/js_analyzer --cov-report=term-missing`
- [ ] **No Flaky Tests**: Run tests 3+ times consistently

### Code Quality
- [ ] **Linting**: `cd backend && ruff check app/services/discovery/modules/js_analyzer*.py`
- [ ] **Formatting**: `cd backend && black --check app/services/discovery/modules/`
- [ ] **Type Check**: `cd backend && mypy app/services/discovery/modules/js_analyzer*.py`

### Security-Specific (CRITICAL for Analysis Module)
- [ ] **False Positive Rate**: < 10% on test corpus
- [ ] **False Negative Rate**: < 5% for known patterns
- [ ] **Secret Detection**: All test secrets detected
- [ ] **No ReDoS**: Regex patterns tested for catastrophic backtracking

### Performance
- [ ] **Regex Analysis**: < 100ms per 100KB JS file
- [ ] **AST Analysis**: < 500ms per 100KB JS file
- [ ] **Memory**: < 200MB for 1MB JS file

### Manual Verification
- [ ] Test on real React/Vue applications
- [ ] Test on minified production bundles
- [ ] Verify secret detection accuracy
- [ ] Verify URL extraction completeness

---

## 📊 Progress Tracking

| Section | Items | Completed | Progress |
|---------|-------|-----------|----------|
| 4.1 JS Analyzer (Regex) | 11 | 0 | 0% |
| 4.2 JS Analyzer (AST) | 7 | 0 | 0% |
| **Total** | **18** | **0** | **0%** |

---

## 🔗 Navigation

| Previous | Current | Next |
|----------|---------|------|
| [Phase 3: Network Module](./phase3-network-module.md) | **Phase 4: Analysis Modules** | [Phase 5: Advanced Modules](./phase5-advanced-modules.md) |

[← Back to Index](./README.md)

---

## 📝 Notes

### Parallel Execution
Phase 4는 Phase 2, Phase 3과 **병렬로 실행 가능**합니다.
Phase 1만 완료되면 독립적으로 개발을 시작할 수 있습니다.

### Downstream Dependencies
- **Phase 5.4 ApiSchemaGenerator**: JsAnalyzer 결과 소비

### Secret Detection Considerations
- 시크릿 탐지는 보안 도구의 핵심 기능입니다
- False Negative는 보안 위험, False Positive는 사용자 피로
- 엔트로피 기반 탐지와 패턴 기반 탐지 조합 권장
