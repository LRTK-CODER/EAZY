# Phase 5: 고급 모듈 (Advanced Modules)

**Status**: ⏳ Pending
**Started**: -
**Last Updated**: 2026-01-23
**Coverage Target**: 80% (Line), 75% (Branch)

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
고급 자산 발견 기능을 구현합니다:
- **Dynamic Interaction Engine**: 클릭, 호버 등 상호작용으로 숨겨진 자산 발견
- **기술 스택 핑거프린팅**: 프레임워크, 라이브러리 탐지
- **Third-party 서비스 탐지**: 외부 서비스 연동 탐지
- **API 스키마 자동 생성**: 발견된 API를 OpenAPI 스펙으로 변환

### Success Criteria
- [ ] 클릭/호버로 동적 콘텐츠 발견
- [ ] React, Vue, Angular 등 프레임워크 탐지
- [ ] Google Analytics, Firebase 등 외부 서비스 탐지
- [ ] OpenAPI 3.0 스펙 자동 생성

### Dependencies
- **Phase 1**: 기반 구조
- **Phase 2**: ResponseAnalyzer (for TechFingerprint)
- **Phase 3**: NetworkCapturer (for InteractionEngine, ApiSchema)
- **Phase 4**: JsAnalyzer (for ApiSchema)

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| Playwright for interaction | 실제 브라우저 동작 시뮬레이션 | 리소스 사용량 높음 |
| Signature DB externalization | 쉬운 업데이트, 커뮤니티 기여 | 별도 유지보수 필요 |
| OpenAPI 3.0 | 업계 표준, 도구 생태계 | 복잡한 스키마 추론 필요 |

---

## 🚀 Implementation Sections

### 5.1 Dynamic Interaction Engine

**Goal**: 사용자 상호작용을 시뮬레이션하여 동적 콘텐츠 발견

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 5.1.1**: `test_click_new_url_discovery()` - 클릭 후 새 URL 발견
  - File: `backend/tests/unit/discovery/test_interaction_engine.py`
  - Test Cases:
    - Click button reveals hidden content
    - Click navigation item loads new page
    - Extract URLs from newly rendered content
    - Handle click triggering XHR

- [ ] **Test 5.1.2**: `test_hover_content_reveal()` - 호버로 콘텐츠 표시
  - File: `backend/tests/unit/discovery/test_interaction_engine.py`
  - Test Cases:
    - Hover reveals dropdown menu
    - Hover shows tooltip with links
    - Handle mouseenter/mouseleave events
    - Extract URLs from hover content

- [ ] **Test 5.1.3**: `test_infinite_scroll_handling()` - 무한 스크롤 처리
  - File: `backend/tests/unit/discovery/test_interaction_engine.py`
  - Test Cases:
    - Detect infinite scroll pages
    - Scroll to load more content
    - Stop at max scroll depth
    - Extract newly loaded URLs

- [ ] **Test 5.1.4**: `test_form_submit_readonly()` - Form 제출 (읽기 전용)
  - File: `backend/tests/unit/discovery/test_interaction_engine.py`
  - Test Cases:
    - Analyze form without actual submission
    - Extract action URL and method
    - Identify required fields
    - Flag potential CSRF tokens

- [ ] **Test 5.1.5**: `test_modal_popup_discovery()` - 모달/팝업 내 URL
  - File: `backend/tests/unit/discovery/test_interaction_engine.py`
  - Test Cases:
    - Trigger modal open
    - Extract URLs from modal content
    - Handle multiple modals
    - Close modal after extraction

- [ ] **Test 5.1.6**: `test_max_interaction_limit()` - 최대 상호작용 제한
  - File: `backend/tests/unit/discovery/test_interaction_engine.py`
  - Test Cases:
    - Respect max_interactions config
    - Stop gracefully at limit
    - Report interaction count
    - Handle timeout

- [ ] **Test 5.1.7**: `test_interaction_loop_prevention()` - 무한 루프 방지
  - File: `backend/tests/unit/discovery/test_interaction_engine.py`
  - Test Cases:
    - Detect circular navigation
    - Skip already-visited states
    - Hash page state for comparison
    - Handle infinite modal chains

- [ ] **Test 5.1.8**: `test_state_snapshot_rollback()` - 상태 스냅샷/롤백
  - File: `backend/tests/unit/discovery/test_interaction_engine.py`
  - Test Cases:
    - Save page state before interaction
    - Rollback on error
    - Handle navigation away
    - Restore cookies/localStorage

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 5.1.9**: `InteractionEngineModule` 구현
  - File: `backend/app/services/discovery/modules/interaction_engine.py`
  - Goal: Make Tests 5.1.1-5.1.8 pass
  - Components:
    - `InteractionPlanner`
    - `ClickHandler`
    - `ScrollHandler`
    - `StateManager`

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 5.1.10**: 상태 관리 개선, 병렬 상호작용 최적화
  - Checklist:
    - [ ] State hashing optimization
    - [ ] Parallel interaction exploration
    - [ ] Intelligent element prioritization
    - [ ] Memory-efficient state storage

---

### 5.2 기술 스택 핑거프린팅

**Goal**: 웹 애플리케이션에서 사용하는 기술 스택 탐지

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 5.2.1**: `test_react_detection()` - React 시그니처 탐지
  - File: `backend/tests/unit/discovery/test_tech_fingerprint.py`
  - Test Cases:
    - Detect `data-reactroot` attribute
    - Detect `__REACT_DEVTOOLS_GLOBAL_HOOK__`
    - Detect `_reactRootContainer`
    - Extract React version if available

- [ ] **Test 5.2.2**: `test_vue_detection()` - Vue.js 시그니처 탐지
  - File: `backend/tests/unit/discovery/test_tech_fingerprint.py`
  - Test Cases:
    - Detect `__VUE__` global
    - Detect `data-v-*` attributes
    - Detect Vue devtools hook
    - Differentiate Vue 2 vs Vue 3

- [ ] **Test 5.2.3**: `test_angular_detection()` - Angular 시그니처 탐지
  - File: `backend/tests/unit/discovery/test_tech_fingerprint.py`
  - Test Cases:
    - Detect `ng-version` attribute
    - Detect `ng-*` directives
    - Detect Zone.js presence
    - Differentiate AngularJS vs Angular

- [ ] **Test 5.2.4**: `test_jquery_detection()` - jQuery 시그니처 탐지
  - File: `backend/tests/unit/discovery/test_tech_fingerprint.py`
  - Test Cases:
    - Detect `window.jQuery` or `window.$`
    - Extract jQuery version
    - Detect jQuery plugins
    - Handle noConflict mode

- [ ] **Test 5.2.5**: `test_wordpress_detection()` - WordPress 시그니처 탐지
  - File: `backend/tests/unit/discovery/test_tech_fingerprint.py`
  - Test Cases:
    - Detect `/wp-content/` paths
    - Detect `wp-json` API
    - Extract WordPress version
    - Detect common plugins

- [ ] **Test 5.2.6**: `test_nginx_detection()` - Nginx 서버 탐지
  - File: `backend/tests/unit/discovery/test_tech_fingerprint.py`
  - Test Cases:
    - Detect `Server: nginx` header
    - Extract nginx version
    - Detect nginx-specific headers
    - Handle reverse proxy setup

- [ ] **Test 5.2.7**: `test_cloudflare_detection()` - Cloudflare CDN 탐지
  - File: `backend/tests/unit/discovery/test_tech_fingerprint.py`
  - Test Cases:
    - Detect `cf-ray` header
    - Detect `cf-cache-status` header
    - Detect Cloudflare challenge pages
    - Extract Cloudflare features in use

- [ ] **Test 5.2.8**: `test_multiple_tech_stack()` - 복합 기술 스택 탐지
  - File: `backend/tests/unit/discovery/test_tech_fingerprint.py`
  - Test Cases:
    - Detect multiple technologies
    - Report confidence levels
    - Handle tech stack combinations
    - Avoid false positives from similar signatures

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 5.2.9**: `TechFingerprintModule` 구현
  - File: `backend/app/services/discovery/modules/tech_fingerprint.py`
  - Goal: Make Tests 5.2.1-5.2.8 pass
  - Components:
    - `SignatureDatabase`
    - `HeaderAnalyzer` (depends on Phase 2)
    - `DomAnalyzer`
    - `ScriptAnalyzer`

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 5.2.10**: 시그니처 DB 확장성, 버전 탐지 추가
  - Checklist:
    - [ ] External signature file (YAML/JSON)
    - [ ] Version extraction patterns
    - [ ] Confidence scoring
    - [ ] Community contribution workflow

---

### 5.3 Third-party 서비스 탐지

**Goal**: 외부 서비스 연동 탐지 (Analytics, Auth, Payment 등)

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 5.3.1**: `test_google_analytics_detection()` - GA 탐지
  - File: `backend/tests/unit/discovery/test_thirdparty_detector.py`
  - Test Cases:
    - Detect gtag.js
    - Detect analytics.js (legacy)
    - Extract tracking ID (UA-*, G-*)
    - Detect GA4 vs Universal Analytics

- [ ] **Test 5.3.2**: `test_mixpanel_detection()` - Mixpanel 탐지
  - File: `backend/tests/unit/discovery/test_thirdparty_detector.py`
  - Test Cases:
    - Detect mixpanel.init()
    - Extract project token
    - Detect event tracking calls
    - Handle bundled SDK

- [ ] **Test 5.3.3**: `test_auth0_detection()` - Auth0 탐지
  - File: `backend/tests/unit/discovery/test_thirdparty_detector.py`
  - Test Cases:
    - Detect auth0.js SDK
    - Extract Auth0 domain
    - Detect login/logout flows
    - Identify Auth0 endpoints

- [ ] **Test 5.3.4**: `test_firebase_detection()` - Firebase 탐지
  - File: `backend/tests/unit/discovery/test_thirdparty_detector.py`
  - Test Cases:
    - Detect firebase SDK
    - Extract project ID
    - Detect Firestore/Realtime DB usage
    - Detect Firebase Auth

- [ ] **Test 5.3.5**: `test_stripe_detection()` - Stripe 탐지
  - File: `backend/tests/unit/discovery/test_thirdparty_detector.py`
  - Test Cases:
    - Detect Stripe.js
    - Extract publishable key (pk_*)
    - Detect Stripe Elements
    - Identify payment forms

- [ ] **Test 5.3.6**: `test_sentry_detection()` - Sentry 탐지
  - File: `backend/tests/unit/discovery/test_thirdparty_detector.py`
  - Test Cases:
    - Detect Sentry SDK
    - Extract DSN (if exposed)
    - Detect error tracking
    - Identify Sentry project

- [ ] **Test 5.3.7**: `test_intercom_detection()` - Intercom 탐지
  - File: `backend/tests/unit/discovery/test_thirdparty_detector.py`
  - Test Cases:
    - Detect Intercom messenger
    - Extract app_id
    - Detect user identification
    - Handle custom launcher

- [ ] **Test 5.3.8**: `test_multiple_services()` - 복수 서비스 탐지
  - File: `backend/tests/unit/discovery/test_thirdparty_detector.py`
  - Test Cases:
    - Detect multiple third-party services
    - Categorize by type (analytics, auth, etc.)
    - Report all configurations found
    - Handle embedded services

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 5.3.9**: `ThirdPartyDetectorModule` 구현
  - File: `backend/app/services/discovery/modules/thirdparty_detector.py`
  - Goal: Make Tests 5.3.1-5.3.8 pass
  - Components:
    - `ServicePatternDatabase`
    - `ScriptUrlMatcher`
    - `ConfigExtractor`
    - `ServiceCategorizer`

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 5.3.10**: 패턴 DB 관리, 자동 업데이트 메커니즘
  - Checklist:
    - [ ] Versioned pattern database
    - [ ] Auto-update from remote
    - [ ] Service category taxonomy
    - [ ] Security risk annotations

---

### 5.4 API 스키마 자동 생성

**Goal**: 발견된 API 엔드포인트를 OpenAPI 3.0 스펙으로 변환

**⚠️ NOTE**: 이 섹션은 Phase 3 (NetworkCapturer)와 Phase 4 (JsAnalyzer)에 복합 의존합니다. Phase 5의 마지막에 구현하세요.

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 5.4.1**: `test_endpoint_path_grouping()` - 경로별 그룹화
  - File: `backend/tests/unit/discovery/test_api_schema_generator.py`
  - Test Cases:
    - Group `/api/users/1`, `/api/users/2` → `/api/users/{id}`
    - Handle multiple path parameters
    - Preserve static path segments
    - Handle nested resources

- [ ] **Test 5.4.2**: `test_http_method_inference()` - HTTP 메서드 추론
  - File: `backend/tests/unit/discovery/test_api_schema_generator.py`
  - Test Cases:
    - Map observed methods to operations
    - Handle multiple methods per endpoint
    - Infer from request patterns
    - Handle custom methods (PATCH, etc.)

- [ ] **Test 5.4.3**: `test_path_parameter_extraction()` - `/users/{id}` 추출
  - File: `backend/tests/unit/discovery/test_api_schema_generator.py`
  - Test Cases:
    - Detect numeric IDs
    - Detect UUID patterns
    - Detect slug patterns
    - Generate parameter names

- [ ] **Test 5.4.4**: `test_query_parameter_inference()` - 쿼리 파라미터 추론
  - File: `backend/tests/unit/discovery/test_api_schema_generator.py`
  - Test Cases:
    - Extract query parameter names
    - Infer parameter types
    - Detect pagination params (page, limit)
    - Handle array parameters

- [ ] **Test 5.4.5**: `test_request_body_inference()` - Request Body 추론
  - File: `backend/tests/unit/discovery/test_api_schema_generator.py`
  - Test Cases:
    - Infer JSON schema from observed bodies
    - Handle form data
    - Merge multiple body examples
    - Generate required fields list

- [ ] **Test 5.4.6**: `test_response_schema_inference()` - Response 스키마 추론
  - File: `backend/tests/unit/discovery/test_api_schema_generator.py`
  - Test Cases:
    - Infer schema from response bodies
    - Handle different status codes
    - Detect common response patterns
    - Handle pagination wrappers

- [ ] **Test 5.4.7**: `test_openapi_3_output()` - OpenAPI 3.0 스펙 출력
  - File: `backend/tests/unit/discovery/test_api_schema_generator.py`
  - Test Cases:
    - Generate valid OpenAPI 3.0 YAML
    - Include info, servers, paths sections
    - Generate component schemas
    - Pass OpenAPI validator

- [ ] **Test 5.4.8**: `test_schema_merge_conflict()` - 스키마 병합 충돌 해결
  - File: `backend/tests/unit/discovery/test_api_schema_generator.py`
  - Test Cases:
    - Handle conflicting type observations
    - Merge arrays with different items
    - Handle optional vs required conflicts
    - Generate union types when needed

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 5.4.9**: `ApiSchemaGeneratorModule` 구현
  - File: `backend/app/services/discovery/modules/api_schema_generator.py`
  - Goal: Make Tests 5.4.1-5.4.8 pass
  - Components:
    - `PathNormalizer`
    - `SchemaInferrer`
    - `OpenApiBuilder`
    - `SchemaMerger`

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 5.4.10**: 스키마 추론 정확도 개선, JSON Schema 지원
  - Checklist:
    - [ ] Multiple inference strategies
    - [ ] Confidence scoring for schemas
    - [ ] JSON Schema draft-07 support
    - [ ] Schema validation integration

---

## ✋ Quality Gate

**⚠️ STOP: Do NOT proceed to Phase 6 until ALL checks pass**

### TDD Compliance (CRITICAL)
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Line coverage ≥ 80%, Branch ≥ 75%

### Build & Tests
- [ ] **All Tests Pass**: `cd backend && pytest tests/unit/discovery/test_interaction_engine.py tests/unit/discovery/test_tech_fingerprint.py tests/unit/discovery/test_thirdparty_detector.py tests/unit/discovery/test_api_schema_generator.py`
- [ ] **Coverage**: `cd backend && pytest --cov=app/services/discovery/modules --cov-report=term-missing`
- [ ] **No Flaky Tests**: Run tests 3+ times consistently

### Code Quality
- [ ] **Linting**: `cd backend && ruff check app/services/discovery/modules/`
- [ ] **Formatting**: `cd backend && black --check app/services/discovery/modules/`
- [ ] **Type Check**: `cd backend && mypy app/services/discovery/modules/`

### Integration
- [ ] **InteractionEngine + NetworkCapturer**: Works together
- [ ] **TechFingerprint + ResponseAnalyzer**: Dependency satisfied
- [ ] **ApiSchemaGenerator + All Sources**: Comprehensive schema generation

### Manual Verification
- [ ] Interaction engine discovers hidden content
- [ ] Technology detection works on real sites
- [ ] Third-party service detection is accurate
- [ ] Generated OpenAPI spec is valid

---

## 📊 Progress Tracking

| Section | Items | Completed | Progress |
|---------|-------|-----------|----------|
| 5.1 Interaction Engine | 10 | 0 | 0% |
| 5.2 Tech Fingerprint | 10 | 0 | 0% |
| 5.3 Third-party Detector | 10 | 0 | 0% |
| 5.4 API Schema Generator | 10 | 0 | 0% |
| **Total** | **40** | **0** | **0%** |

---

## 🔗 Navigation

| Previous | Current | Next |
|----------|---------|------|
| [Phase 4: Analysis Modules](./phase4-analysis-modules.md) | **Phase 5: Advanced Modules** | [Phase 6: Integration](./phase6-integration.md) |

[← Back to Index](./README.md)

---

## 📝 Notes

### Implementation Order
Phase 5 내에서 권장 구현 순서:
1. **5.2 TechFingerprint** (Phase 2 의존)
2. **5.3 ThirdPartyDetector** (독립적)
3. **5.1 InteractionEngine** (Phase 3 의존)
4. **5.4 ApiSchemaGenerator** (Phase 3 + 4 의존, 마지막)

### Signature Database
기술 스택 및 서드파티 서비스 시그니처는 외부 파일로 관리하여
코드 변경 없이 새로운 패턴을 추가할 수 있도록 합니다:
```
backend/app/services/discovery/data/
├── tech_signatures.yaml
└── thirdparty_signatures.yaml
```
