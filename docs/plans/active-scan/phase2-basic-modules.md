# Phase 2: 기본 모듈 (Basic Modules)

**Status**: ✅ Completed
**Started**: 2026-01-23
**Last Updated**: 2026-01-23
**Coverage Achieved**: 93% (Line)

---

**✅ PHASE COMPLETED**: 모든 항목이 구현되고 Quality Gate를 통과했습니다.

---

## 📋 Overview

### Feature Description
웹 애플리케이션에서 자산을 발견하는 기본 모듈들을 구현합니다:
- **Configuration Discovery**: robots.txt, sitemap.xml, well-known 파일 파싱
- **HTML Element Parser**: HTML 요소에서 URL 및 자산 추출
- **Response Analyzer**: HTTP 응답 헤더 및 본문 분석

### Success Criteria
- [x] robots.txt Disallow 경로 및 Sitemap 참조 추출
- [x] sitemap.xml에서 URL 목록 추출 (nested sitemap 포함)
- [x] HTML 폼, 스크립트, 링크, 이미지 등에서 URL 추출
- [x] HTTP 헤더에서 보안 관련 정보 추출 (CSP, CORS, Cookie)
- [x] 에러 메시지에서 경로 정보 탐지

### Dependencies
- **Phase 1**: ScanProfile, DiscoveredAsset, BaseDiscoveryModule, DiscoveryContext ✅

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

- [x] **Test 2.1.1**: `test_robots_txt_disallow_extraction()` - Disallow 경로 추출
- [x] **Test 2.1.2**: `test_robots_txt_sitemap_reference()` - Sitemap 참조 추출
- [x] **Test 2.1.3**: `test_robots_txt_not_found()` - 404 처리
- [x] **Test 2.1.4**: `test_sitemap_url_extraction()` - URL 목록 추출
- [x] **Test 2.1.5**: `test_sitemap_nested()` - sitemap index 처리
- [x] **Test 2.1.6**: `test_well_known_security_txt()` - security.txt 파싱
- [x] **Test 2.1.7**: `test_well_known_openid_config()` - openid-configuration
- [x] **Test 2.1.8**: `test_source_map_detection()` - .js.map 파일 발견

#### 🟢 GREEN: Implement to Make Tests Pass

- [x] **Task 2.1.9**: `ConfigDiscoveryModule` 구현
  - File: `backend/app/services/discovery/modules/config_discovery.py`
  - Components:
    - `RobotsTxtParser` ✅
    - `SitemapParser` ✅
    - `WellKnownParser` ✅
    - `SourceMapDetector` ✅

#### 🔵 REFACTOR: Clean Up Code

- [x] **Task 2.1.10**: 에러 핸들링, 타임아웃 처리, HTTP 클라이언트 추상화

---

### 2.2 HTML Element Parser

**Goal**: HTML 문서에서 다양한 요소의 URL 및 자산 추출

#### 🔴 RED: Write Failing Tests First

- [x] **Test 2.2.1**: `test_form_action_extraction()` - form action URL
- [x] **Test 2.2.2**: `test_form_method_detection()` - GET/POST 메서드
- [x] **Test 2.2.3**: `test_form_hidden_inputs()` - hidden input 추출
- [x] **Test 2.2.4**: `test_form_csrf_token()` - CSRF 토큰 발견
- [x] **Test 2.2.5**: `test_script_src_extraction()` - script src 추출
- [x] **Test 2.2.6**: `test_script_inline_url()` - 인라인 스크립트 내 URL
- [x] **Test 2.2.7**: `test_link_href_extraction()` - link href 추출
- [x] **Test 2.2.8**: `test_link_rel_types()` - stylesheet, preload 구분
- [x] **Test 2.2.9**: `test_img_src_extraction()` - img src, srcset
- [x] **Test 2.2.10**: `test_video_audio_source()` - video, audio, source 태그
- [x] **Test 2.2.11**: `test_meta_refresh_url()` - meta refresh URL 추출
- [x] **Test 2.2.12**: `test_meta_og_tags()` - Open Graph 태그
- [x] **Test 2.2.13**: `test_data_attr_url_pattern()` - data-url, data-api 등
- [x] **Test 2.2.14**: `test_base_href_resolution()` - base href 기준 URL 해결

#### 🟢 GREEN: Implement to Make Tests Pass

- [x] **Task 2.2.15**: `HtmlElementParserModule` + 개별 Parser 클래스 구현
  - File: `backend/app/services/discovery/modules/html_element_parser.py`
  - Components:
    - `FormParser` ✅
    - `ScriptParser` ✅
    - `LinkParser` ✅
    - `MediaParser` ✅
    - `MetaParser` ✅
    - `DataAttrParser` ✅

#### 🔵 REFACTOR: Clean Up Code

- [x] **Task 2.2.16**: Parser 체인 최적화, BeautifulSoup/lxml 선택

---

### 2.3 Response Analyzer

**Goal**: HTTP 응답 헤더 및 본문에서 보안 관련 정보 추출

#### 🔴 RED: Write Failing Tests First

- [x] **Test 2.3.1**: `test_server_header_extraction()` - Server 헤더
- [x] **Test 2.3.2**: `test_x_powered_by_extraction()` - X-Powered-By 헤더
- [x] **Test 2.3.3**: `test_csp_domain_extraction()` - CSP 허용 도메인
- [x] **Test 2.3.4**: `test_cors_origin_extraction()` - CORS 허용 Origin
- [x] **Test 2.3.5**: `test_cookie_domain_extraction()` - Set-Cookie 도메인
- [x] **Test 2.3.6**: `test_cookie_path_extraction()` - Set-Cookie 경로
- [x] **Test 2.3.7**: `test_cookie_security_flags()` - Secure, HttpOnly 플래그
- [x] **Test 2.3.8**: `test_error_message_path_leakage()` - 에러 메시지 내 경로
- [x] **Test 2.3.9**: `test_stack_trace_detection()` - 스택 트레이스 탐지

#### 🟢 GREEN: Implement to Make Tests Pass

- [x] **Task 2.3.10**: `ResponseAnalyzerModule` + Analyzer 클래스 구현
  - File: `backend/app/services/discovery/modules/response_analyzer.py`
  - Components:
    - `HeaderAnalyzer` ✅
    - `CspParser` ✅
    - `CookieAnalyzer` ✅
    - `ErrorDetector` ✅

#### 🔵 REFACTOR: Clean Up Code

- [x] **Task 2.3.11**: 헤더 정규화, 중복 제거, 캐싱

---

## ✋ Quality Gate

**✅ ALL CHECKS PASSED**

### TDD Compliance (CRITICAL)
- [x] **Red Phase**: Tests were written FIRST and initially failed
- [x] **Green Phase**: Production code written to make tests pass
- [x] **Refactor Phase**: Code improved while tests still pass
- [x] **Coverage Check**: Line coverage 93%

### Build & Tests
- [x] **All Tests Pass**: 151 tests passed (97 new in Phase 2)
- [x] **Coverage**: 93% line coverage
- [x] **No Flaky Tests**: Run tests 3+ times consistently

### Code Quality
- [x] **Linting**: `uv run ruff check app/services/discovery/modules/` ✅
- [x] **Formatting**: `uv run black --check app/services/discovery/modules/` ✅
- [x] **Import Sort**: `uv run isort --check app/services/discovery/modules/` ✅
- [x] **Type Check**: `uv run mypy app/services/discovery/modules/` ✅

### Security-Specific
- [x] **False Positive Test**: Normal content not flagged incorrectly
- [x] **False Negative Test**: Known patterns always detected
- [x] **Edge Cases**: Malformed inputs handled gracefully

### Manual Verification
- [x] robots.txt parsing works with real sites
- [x] HTML parser handles malformed HTML
- [x] Header analyzer works with various server responses

---

## 📊 Progress Tracking

| Section | Items | Completed | Progress |
|---------|-------|-----------|----------|
| 2.1 Config Discovery | 10 | 10 | ✅ 100% |
| 2.2 HTML Parser | 16 | 16 | ✅ 100% |
| 2.3 Response Analyzer | 11 | 11 | ✅ 100% |
| **Total** | **37** | **37** | **✅ 100%** |

---

## 📁 Generated Files

### Implementation
```
backend/app/services/discovery/modules/
├── __init__.py
├── config_discovery.py      # 27 tests, 268 lines
├── html_element_parser.py   # 31 tests, 486 lines
└── response_analyzer.py     # 39 tests, 280 lines
```

### Tests
```
backend/tests/services/discovery/modules/
├── __init__.py
├── test_config_discovery.py
├── test_html_element_parser.py
└── test_response_analyzer.py
```

---

## 🔗 Navigation

| Previous | Current | Next |
|----------|---------|------|
| [Phase 1: Foundation](./phase1-foundation.md) ✅ | **Phase 2: Basic Modules** ✅ | [Phase 3: Network Module](./phase3-network-module.md) |

[← Back to Index](./README.md)
