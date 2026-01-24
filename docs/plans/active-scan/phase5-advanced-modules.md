# Phase 5: 고급 모듈 (Advanced Modules)

**Status**: ✅ Completed
**Started**: 2026-01-25
**Completed**: 2026-01-25
**Last Updated**: 2026-01-25
**Coverage Achieved**: 92% (Line)

---

## 📋 Overview

### Feature Description
고급 자산 발견 기능을 구현합니다:
- **Dynamic Interaction Engine**: 클릭, 호버 등 상호작용으로 숨겨진 자산 발견
- **기술 스택 핑거프린팅**: 프레임워크, 라이브러리 탐지
- **Third-party 서비스 탐지**: 외부 서비스 연동 탐지
- **API 스키마 자동 생성**: 발견된 API를 OpenAPI 스펙으로 변환

### Success Criteria
- [x] 클릭/호버로 동적 콘텐츠 발견
- [x] React, Vue, Angular 등 프레임워크 탐지
- [x] Google Analytics, Firebase 등 외부 서비스 탐지
- [x] OpenAPI 3.0 스펙 자동 생성

### Dependencies
- **Phase 1**: 기반 구조 ✅
- **Phase 2**: ResponseAnalyzer (for TechFingerprint) ✅
- **Phase 3**: NetworkCapturer (for InteractionEngine, ApiSchema) ✅
- **Phase 4**: JsAnalyzer (for ApiSchema) ✅

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| Playwright for interaction | 실제 브라우저 동작 시뮬레이션 | 리소스 사용량 높음 |
| Signature DB externalization | 쉬운 업데이트, 커뮤니티 기여 | 별도 유지보수 필요 |
| OpenAPI 3.0 | 업계 표준, 도구 생태계 | 복잡한 스키마 추론 필요 |

---

## 🚀 Implementation Sections

### 5.1 Dynamic Interaction Engine ✅

**Goal**: 사용자 상호작용을 시뮬레이션하여 동적 콘텐츠 발견

**Implementation**: `backend/app/services/discovery/modules/interaction_engine.py` (673 lines)

**Components**:
- `ClickHandler`: 버튼/링크 클릭 시뮬레이션
- `HoverHandler`: 드롭다운/툴팁 트리거
- `ScrollHandler`: 무한 스크롤/지연 로딩 탐지
- `StateTracker`: DOM 상태 변화 추적
- `InteractionEngineModule`: FULL 프로필 전용

**Tests**: 37 tests passed | Coverage: 87%

#### Completed Tasks

- [x] **Test 5.1.1**: `test_click_new_url_discovery()` - 클릭 후 새 URL 발견
- [x] **Test 5.1.2**: `test_hover_content_reveal()` - 호버로 콘텐츠 표시
- [x] **Test 5.1.3**: `test_infinite_scroll_handling()` - 무한 스크롤 처리
- [x] **Test 5.1.4**: `test_form_submit_readonly()` - Form 제출 (읽기 전용)
- [x] **Test 5.1.5**: `test_modal_popup_discovery()` - 모달/팝업 내 URL
- [x] **Test 5.1.6**: `test_max_interaction_limit()` - 최대 상호작용 제한
- [x] **Test 5.1.7**: `test_interaction_loop_prevention()` - 무한 루프 방지
- [x] **Test 5.1.8**: `test_state_snapshot_rollback()` - 상태 스냅샷/롤백
- [x] **Task 5.1.9**: `InteractionEngineModule` 구현
- [x] **Task 5.1.10**: 상태 관리 개선, 병렬 상호작용 최적화

---

### 5.2 기술 스택 핑거프린팅 ✅

**Goal**: 웹 애플리케이션에서 사용하는 기술 스택 탐지

**Implementation**: `backend/app/services/discovery/modules/tech_fingerprint.py` (634 lines)

**Signature File**: `backend/app/services/discovery/data/tech_signatures.yaml` (27 시그니처)

**Components**:
- `HeaderMatcher`: HTTP 헤더 기반 기술 탐지
- `ScriptMatcher`: 스크립트 URL 패턴 매칭
- `GlobalVariableMatcher`: 전역 변수 탐지 (React, Vue, Angular)
- `DomSignatureMatcher`: DOM 속성 기반 탐지
- `TechFingerprintModule`: STANDARD, FULL 프로필

**Tests**: 47 tests passed | Coverage: 98%

#### Completed Tasks

- [x] **Test 5.2.1**: `test_react_detection()` - React 시그니처 탐지
- [x] **Test 5.2.2**: `test_vue_detection()` - Vue.js 시그니처 탐지
- [x] **Test 5.2.3**: `test_angular_detection()` - Angular 시그니처 탐지
- [x] **Test 5.2.4**: `test_jquery_detection()` - jQuery 시그니처 탐지
- [x] **Test 5.2.5**: `test_wordpress_detection()` - WordPress 시그니처 탐지
- [x] **Test 5.2.6**: `test_nginx_detection()` - Nginx 서버 탐지
- [x] **Test 5.2.7**: `test_cloudflare_detection()` - Cloudflare CDN 탐지
- [x] **Test 5.2.8**: `test_multiple_tech_stack()` - 복합 기술 스택 탐지
- [x] **Task 5.2.9**: `TechFingerprintModule` 구현
- [x] **Task 5.2.10**: 시그니처 DB 확장성, 버전 탐지 추가

---

### 5.3 Third-party 서비스 탐지 ✅

**Goal**: 외부 서비스 연동 탐지 (Analytics, Auth, Payment 등)

**Implementation**: `backend/app/services/discovery/modules/thirdparty_detector.py` (528 lines)

**Signature File**: `backend/app/services/discovery/data/thirdparty_signatures.yaml` (25 서비스)

**Components**:
- `ScriptPatternMatcher`: 외부 스크립트 탐지
- `GlobalVariableMatcher`: 전역 변수 탐지
- `CookieMatcher`: 쿠키 패턴 탐지
- `ThirdPartyDetectorModule`: STANDARD, FULL 프로필

**Tests**: 40 tests passed | Coverage: 93%

#### Completed Tasks

- [x] **Test 5.3.1**: `test_google_analytics_detection()` - GA 탐지
- [x] **Test 5.3.2**: `test_mixpanel_detection()` - Mixpanel 탐지
- [x] **Test 5.3.3**: `test_auth0_detection()` - Auth0 탐지
- [x] **Test 5.3.4**: `test_firebase_detection()` - Firebase 탐지
- [x] **Test 5.3.5**: `test_stripe_detection()` - Stripe 탐지
- [x] **Test 5.3.6**: `test_sentry_detection()` - Sentry 탐지
- [x] **Test 5.3.7**: `test_intercom_detection()` - Intercom 탐지
- [x] **Test 5.3.8**: `test_multiple_services()` - 복수 서비스 탐지
- [x] **Task 5.3.9**: `ThirdPartyDetectorModule` 구현
- [x] **Task 5.3.10**: 패턴 DB 관리, 자동 업데이트 메커니즘

---

### 5.4 API 스키마 자동 생성 ✅

**Goal**: 발견된 API 엔드포인트를 OpenAPI 3.0 스펙으로 변환

**Implementation**: `backend/app/services/discovery/modules/api_schema_generator.py` (760 lines)

**Components**:
- `PathNormalizer`: /users/123 → /users/{id}
- `SchemaInferrer`: JSON → JSON Schema 추론
- `OperationGrouper`: 같은 경로 메서드 그룹화
- `OpenApiBuilder`: OpenAPI 3.0 스펙 생성
- `ApiSchemaGeneratorModule`: FULL 프로필 전용

**Tests**: 52 tests passed | Coverage: 92%

#### Completed Tasks

- [x] **Test 5.4.1**: `test_endpoint_path_grouping()` - 경로별 그룹화
- [x] **Test 5.4.2**: `test_http_method_inference()` - HTTP 메서드 추론
- [x] **Test 5.4.3**: `test_path_parameter_extraction()` - `/users/{id}` 추출
- [x] **Test 5.4.4**: `test_query_parameter_inference()` - 쿼리 파라미터 추론
- [x] **Test 5.4.5**: `test_request_body_inference()` - Request Body 추론
- [x] **Test 5.4.6**: `test_response_schema_inference()` - Response 스키마 추론
- [x] **Test 5.4.7**: `test_openapi_3_output()` - OpenAPI 3.0 스펙 출력
- [x] **Test 5.4.8**: `test_schema_merge_conflict()` - 스키마 병합 충돌 해결
- [x] **Task 5.4.9**: `ApiSchemaGeneratorModule` 구현
- [x] **Task 5.4.10**: 스키마 추론 정확도 개선, JSON Schema 지원

---

## ✋ Quality Gate ✅

### TDD Compliance (CRITICAL)
- [x] **Red Phase**: Tests were written FIRST and initially failed
- [x] **Green Phase**: Production code written to make tests pass
- [x] **Refactor Phase**: Code improved while tests still pass
- [x] **Coverage Check**: Line coverage ≥ 80% (Achieved: 92%)

### Build & Tests
- [x] **All Tests Pass**: 499 passed in 0.41s
- [x] **Coverage**: 92% overall
- [x] **No Flaky Tests**: All tests consistent

### Code Quality
- [x] **Linting**: `ruff check` - All checks passed
- [x] **Formatting**: `black --check` - Passed
- [x] **Import Sort**: `isort --check` - Passed
- [x] **Type Check**: `mypy` - Success: no issues found

### Integration
- [x] **InteractionEngine + NetworkCapturer**: Works together
- [x] **TechFingerprint + ResponseAnalyzer**: Dependency satisfied
- [x] **ApiSchemaGenerator + All Sources**: Comprehensive schema generation

---

## 📊 Progress Tracking

| Section | Items | Completed | Progress |
|---------|-------|-----------|----------|
| 5.1 Interaction Engine | 10 | 10 | ✅ 100% |
| 5.2 Tech Fingerprint | 10 | 10 | ✅ 100% |
| 5.3 Third-party Detector | 10 | 10 | ✅ 100% |
| 5.4 API Schema Generator | 10 | 10 | ✅ 100% |
| **Total** | **40** | **40** | **✅ 100%** |

---

## 📁 Created Files

### Implementation
- `app/services/discovery/modules/interaction_engine.py`
- `app/services/discovery/modules/tech_fingerprint.py`
- `app/services/discovery/modules/thirdparty_detector.py`
- `app/services/discovery/modules/api_schema_generator.py`

### Signature Data
- `app/services/discovery/data/tech_signatures.yaml`
- `app/services/discovery/data/thirdparty_signatures.yaml`

### Tests
- `tests/services/discovery/modules/test_interaction_engine.py`
- `tests/services/discovery/modules/test_tech_fingerprint.py`
- `tests/services/discovery/modules/test_thirdparty_detector.py`
- `tests/services/discovery/modules/test_api_schema_generator.py`

---

## 🔗 Navigation

| Previous | Current | Next |
|----------|---------|------|
| [Phase 4: Analysis Modules](./phase4-analysis-modules.md) ✅ | **Phase 5: Advanced Modules** ✅ | [Phase 6: Integration](./phase6-integration.md) |

[← Back to Index](./README.md)

---

## 📝 Notes

### Implementation Order (Completed)
1. **5.2 TechFingerprint** (Phase 2 의존) ✅
2. **5.3 ThirdPartyDetector** (독립적) ✅
3. **5.1 InteractionEngine** (Phase 3 의존) ✅
4. **5.4 ApiSchemaGenerator** (Phase 3 + 4 의존, 마지막) ✅

### Parallel Execution Strategy
- Wave 1: 3 agents parallel (InteractionEngine, TechFingerprint, ThirdPartyDetector)
- Wave 2: Sequential (ApiSchemaGenerator - all dependencies complete)

### Dependencies Added
```bash
uv add --dev types-PyYAML
```
