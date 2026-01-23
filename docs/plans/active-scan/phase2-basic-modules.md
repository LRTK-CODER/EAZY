# Phase 2: 기본 모듈 (Basic Modules)

**Status**: ⏳ Pending
**Started**: -
**Last Updated**: 2026-01-23
**Coverage Target**: 95% (Line), 90% (Branch)

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
웹 애플리케이션에서 자산을 발견하는 기본 모듈들을 구현합니다:
- **Configuration Discovery**: robots.txt, sitemap.xml, well-known 파일 파싱
- **HTML Element Parser**: HTML 요소에서 URL 및 자산 추출
- **Response Analyzer**: HTTP 응답 헤더 및 본문 분석

### Success Criteria
- [ ] robots.txt Disallow 경로 및 Sitemap 참조 추출
- [ ] sitemap.xml에서 URL 목록 추출 (nested sitemap 포함)
- [ ] HTML 폼, 스크립트, 링크, 이미지 등에서 URL 추출
- [ ] HTTP 헤더에서 보안 관련 정보 추출 (CSP, CORS, Cookie)
- [ ] 에러 메시지에서 경로 정보 탐지

### Dependencies
- **Phase 1**: ScanProfile, DiscoveredAsset, BaseDiscoveryModule, DiscoveryContext

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| 개별 Parser 클래스 | 단일 책임, 테스트 용이 | 클래스 수 증가 |
| BeautifulSoup 사용 | 견고한 HTML 파싱, 널리 검증됨 | lxml보다 느림 |
| Regex for headers | 간단한 패턴, 성능 우수 | 복잡한 케이스 제한적 |

---

## 🚀 Implementation Sections

### 2.1 Configuration Discovery

**Goal**: robots.txt, sitemap.xml, well-known 파일에서 자산 발견

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 2.1.1**: `test_robots_txt_disallow_extraction()` - Disallow 경로 추출
  - File: `backend/tests/unit/discovery/test_config_discovery.py`
  - Test Cases:
    - Extract `/admin/` from `Disallow: /admin/`
    - Handle multiple Disallow entries
    - Handle User-agent specific rules
    - Handle wildcard patterns (`*`)

- [ ] **Test 2.1.2**: `test_robots_txt_sitemap_reference()` - Sitemap 참조 추출
  - File: `backend/tests/unit/discovery/test_config_discovery.py`
  - Test Cases:
    - Extract sitemap URL from `Sitemap:` directive
    - Handle multiple sitemap references
    - Handle relative and absolute URLs

- [ ] **Test 2.1.3**: `test_robots_txt_not_found()` - 404 처리
  - File: `backend/tests/unit/discovery/test_config_discovery.py`
  - Test Cases:
    - Gracefully handle 404 response
    - Return empty results, not error
    - Log appropriate warning

- [ ] **Test 2.1.4**: `test_sitemap_url_extraction()` - URL 목록 추출
  - File: `backend/tests/unit/discovery/test_config_discovery.py`
  - Test Cases:
    - Extract `<loc>` URLs from sitemap XML
    - Handle `<lastmod>`, `<changefreq>`, `<priority>`
    - Parse both standard and compressed sitemaps

- [ ] **Test 2.1.5**: `test_sitemap_nested()` - sitemap index 처리
  - File: `backend/tests/unit/discovery/test_config_discovery.py`
  - Test Cases:
    - Detect sitemap index file
    - Recursively fetch referenced sitemaps
    - Handle max depth limit

- [ ] **Test 2.1.6**: `test_well_known_security_txt()` - security.txt 파싱
  - File: `backend/tests/unit/discovery/test_config_discovery.py`
  - Test Cases:
    - Parse `/.well-known/security.txt`
    - Extract Contact, Policy, Hiring URLs
    - Handle PGP signatures

- [ ] **Test 2.1.7**: `test_well_known_openid_config()` - openid-configuration
  - File: `backend/tests/unit/discovery/test_config_discovery.py`
  - Test Cases:
    - Parse `/.well-known/openid-configuration`
    - Extract authorization_endpoint, token_endpoint
    - Extract jwks_uri

- [ ] **Test 2.1.8**: `test_source_map_detection()` - .js.map 파일 발견
  - File: `backend/tests/unit/discovery/test_config_discovery.py`
  - Test Cases:
    - Detect `//# sourceMappingURL=` comment
    - Handle relative and absolute map URLs
    - Flag as potential information disclosure

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 2.1.9**: `ConfigDiscoveryModule` 구현
  - File: `backend/app/services/discovery/modules/config_discovery.py`
  - Goal: Make Tests 2.1.1-2.1.8 pass
  - Components:
    - `RobotsTxtParser`
    - `SitemapParser`
    - `WellKnownParser`
    - `SourceMapDetector`

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 2.1.10**: 에러 핸들링, 타임아웃 처리, HTTP 클라이언트 추상화
  - Checklist:
    - [ ] Connection timeout handling
    - [ ] Rate limiting awareness
    - [ ] Retry logic with exponential backoff
    - [ ] HTTP client interface abstraction

---

### 2.2 HTML Element Parser

**Goal**: HTML 문서에서 다양한 요소의 URL 및 자산 추출

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 2.2.1**: `test_form_action_extraction()` - form action URL
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Extract action URL from `<form action="...">`
    - Handle empty action (same page)
    - Handle javascript: protocol (skip)

- [ ] **Test 2.2.2**: `test_form_method_detection()` - GET/POST 메서드
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Detect GET method (default)
    - Detect POST method
    - Detect other methods (PUT, DELETE via hidden field)

- [ ] **Test 2.2.3**: `test_form_hidden_inputs()` - hidden input 추출
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Extract all hidden input names/values
    - Identify potential state parameters
    - Handle multiple forms

- [ ] **Test 2.2.4**: `test_form_csrf_token()` - CSRF 토큰 발견
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Detect common CSRF token names (_token, csrf_token, etc.)
    - Extract token values
    - Flag CSRF protection presence

- [ ] **Test 2.2.5**: `test_script_src_extraction()` - script src 추출
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Extract external script URLs
    - Handle async/defer attributes
    - Handle integrity/crossorigin attributes

- [ ] **Test 2.2.6**: `test_script_inline_url()` - 인라인 스크립트 내 URL
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Extract URLs from inline JavaScript
    - Handle string literals and template literals
    - Filter false positives (comments, etc.)

- [ ] **Test 2.2.7**: `test_link_href_extraction()` - link href 추출
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Extract stylesheet URLs
    - Extract preload/prefetch URLs
    - Handle different rel types

- [ ] **Test 2.2.8**: `test_link_rel_types()` - stylesheet, preload 구분
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Categorize by rel attribute
    - Handle multiple rel values
    - Extract as attribute

- [ ] **Test 2.2.9**: `test_img_src_extraction()` - img src, srcset
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Extract src attribute
    - Parse srcset with multiple URLs
    - Handle data: URLs (skip)

- [ ] **Test 2.2.10**: `test_video_audio_source()` - video, audio, source 태그
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Extract video src
    - Extract audio src
    - Extract source tags within media elements

- [ ] **Test 2.2.11**: `test_meta_refresh_url()` - meta refresh URL 추출
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Parse `<meta http-equiv="refresh" content="0;url=...">`
    - Handle various content formats
    - Extract redirect URL

- [ ] **Test 2.2.12**: `test_meta_og_tags()` - Open Graph 태그
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Extract og:image, og:url
    - Extract twitter:image, twitter:url
    - Handle relative URLs

- [ ] **Test 2.2.13**: `test_data_attr_url_pattern()` - data-url, data-api 등
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Extract data-* attributes containing URLs
    - Filter URL-like patterns
    - Handle JSON in data attributes

- [ ] **Test 2.2.14**: `test_base_href_resolution()` - base href 기준 URL 해결
  - File: `backend/tests/unit/discovery/test_html_parser.py`
  - Test Cases:
    - Detect `<base href="...">`
    - Resolve relative URLs against base
    - Handle missing base tag

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 2.2.15**: `HtmlParserModule` + 개별 Parser 클래스 구현
  - File: `backend/app/services/discovery/modules/html_parser.py`
  - Goal: Make Tests 2.2.1-2.2.14 pass
  - Components:
    - `FormParser`
    - `ScriptParser`
    - `LinkParser`
    - `MediaParser`
    - `MetaParser`
    - `DataAttrParser`

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 2.2.16**: Parser 체인 최적화, BeautifulSoup/lxml 선택
  - Checklist:
    - [ ] Parser chain pattern 적용
    - [ ] Lazy parsing for large documents
    - [ ] Performance benchmarks
    - [ ] Memory usage optimization

---

### 2.3 Response Analyzer

**Goal**: HTTP 응답 헤더 및 본문에서 보안 관련 정보 추출

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 2.3.1**: `test_server_header_extraction()` - Server 헤더
  - File: `backend/tests/unit/discovery/test_response_analyzer.py`
  - Test Cases:
    - Extract server name/version
    - Handle missing Server header
    - Parse complex server strings

- [ ] **Test 2.3.2**: `test_x_powered_by_extraction()` - X-Powered-By 헤더
  - File: `backend/tests/unit/discovery/test_response_analyzer.py`
  - Test Cases:
    - Extract technology stack info
    - Handle multiple X-Powered-By headers
    - Parse version information

- [ ] **Test 2.3.3**: `test_csp_domain_extraction()` - CSP 허용 도메인
  - File: `backend/tests/unit/discovery/test_response_analyzer.py`
  - Test Cases:
    - Parse Content-Security-Policy header
    - Extract allowed domains per directive
    - Handle wildcards and special values

- [ ] **Test 2.3.4**: `test_cors_origin_extraction()` - CORS 허용 Origin
  - File: `backend/tests/unit/discovery/test_response_analyzer.py`
  - Test Cases:
    - Extract Access-Control-Allow-Origin
    - Handle wildcard (`*`)
    - Extract from preflight responses

- [ ] **Test 2.3.5**: `test_cookie_domain_extraction()` - Set-Cookie 도메인
  - File: `backend/tests/unit/discovery/test_response_analyzer.py`
  - Test Cases:
    - Extract Domain attribute
    - Handle missing Domain (implicit)
    - Detect subdomain cookies

- [ ] **Test 2.3.6**: `test_cookie_path_extraction()` - Set-Cookie 경로
  - File: `backend/tests/unit/discovery/test_response_analyzer.py`
  - Test Cases:
    - Extract Path attribute
    - Handle default path
    - Identify restricted paths

- [ ] **Test 2.3.7**: `test_cookie_security_flags()` - Secure, HttpOnly 플래그
  - File: `backend/tests/unit/discovery/test_response_analyzer.py`
  - Test Cases:
    - Detect Secure flag presence
    - Detect HttpOnly flag presence
    - Detect SameSite attribute
    - Flag missing security attributes

- [ ] **Test 2.3.8**: `test_error_message_path_leakage()` - 에러 메시지 내 경로
  - File: `backend/tests/unit/discovery/test_response_analyzer.py`
  - Test Cases:
    - Detect file paths in error messages
    - Detect absolute paths (Unix/Windows)
    - Handle common frameworks' error formats

- [ ] **Test 2.3.9**: `test_stack_trace_detection()` - 스택 트레이스 탐지
  - File: `backend/tests/unit/discovery/test_response_analyzer.py`
  - Test Cases:
    - Detect Python traceback
    - Detect Java stack trace
    - Detect PHP/Node.js errors
    - Flag information disclosure risk

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 2.3.10**: `ResponseAnalyzerModule` + Analyzer 클래스 구현
  - File: `backend/app/services/discovery/modules/response_analyzer.py`
  - Goal: Make Tests 2.3.1-2.3.9 pass
  - Components:
    - `HeaderAnalyzer`
    - `CspParser`
    - `CookieAnalyzer`
    - `ErrorDetector`

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 2.3.11**: 헤더 정규화, 중복 제거, 캐싱
  - Checklist:
    - [ ] Header name normalization
    - [ ] Deduplication of findings
    - [ ] Result caching per response
    - [ ] Pattern database externalization

---

## ✋ Quality Gate

**⚠️ STOP: Do NOT proceed to Phase 3 until ALL checks pass**

### TDD Compliance (CRITICAL)
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Line coverage ≥ 95%, Branch ≥ 90%

### Build & Tests
- [ ] **All Tests Pass**: `cd backend && pytest tests/unit/discovery/test_config_discovery.py tests/unit/discovery/test_html_parser.py tests/unit/discovery/test_response_analyzer.py`
- [ ] **Coverage**: `cd backend && pytest --cov=app/services/discovery/modules --cov-report=term-missing`
- [ ] **No Flaky Tests**: Run tests 3+ times consistently

### Code Quality
- [ ] **Linting**: `cd backend && ruff check app/services/discovery/modules/`
- [ ] **Formatting**: `cd backend && black --check app/services/discovery/modules/`
- [ ] **Type Check**: `cd backend && mypy app/services/discovery/modules/`

### Security-Specific
- [ ] **False Positive Test**: Normal content not flagged incorrectly
- [ ] **False Negative Test**: Known patterns always detected
- [ ] **Edge Cases**: Malformed inputs handled gracefully

### Manual Verification
- [ ] robots.txt parsing works with real sites
- [ ] HTML parser handles malformed HTML
- [ ] Header analyzer works with various server responses

---

## 📊 Progress Tracking

| Section | Items | Completed | Progress |
|---------|-------|-----------|----------|
| 2.1 Config Discovery | 10 | 0 | 0% |
| 2.2 HTML Parser | 16 | 0 | 0% |
| 2.3 Response Analyzer | 11 | 0 | 0% |
| **Total** | **37** | **0** | **0%** |

---

## 🔗 Navigation

| Previous | Current | Next |
|----------|---------|------|
| [Phase 1: Foundation](./phase1-foundation.md) | **Phase 2: Basic Modules** | [Phase 3: Network Module](./phase3-network-module.md) |

[← Back to Index](./README.md)
