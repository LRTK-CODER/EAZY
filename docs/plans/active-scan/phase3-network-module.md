# Phase 3: 네트워크 모듈 (Network Module)

**Status**: ⏳ Pending
**Started**: -
**Last Updated**: 2026-01-23
**Coverage Target**: 85% (Line), 80% (Branch)

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
브라우저 네트워크 트래픽을 캡처하여 동적으로 로드되는 자산을 발견합니다:
- XHR/Fetch 요청 캡처
- CORS preflight 요청 분석
- GraphQL 쿼리/뮤테이션 추출
- WebSocket 연결 탐지

### Success Criteria
- [ ] 모든 XHR/Fetch 요청 URL 캡처
- [ ] CORS preflight 요청에서 허용 Origin 추출
- [ ] GraphQL 쿼리/뮤테이션/인트로스펙션 탐지
- [ ] WebSocket 연결 URL 및 프로토콜 추출

### Dependencies
- **Phase 1**: ScanProfile, DiscoveredAsset, BaseDiscoveryModule, DiscoveryContext
- **External**: Playwright (browser automation)

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| Playwright CDP | Chrome DevTools Protocol 직접 접근 | Chromium 계열만 지원 |
| Request interception | 모든 네트워크 요청 캡처 가능 | 성능 오버헤드 |
| Async streaming | 메모리 효율적 처리 | 복잡도 증가 |

---

## 🚀 Implementation Sections

### 3.1 Network Traffic Capturer

**Goal**: 브라우저 네트워크 트래픽에서 자산 발견

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 3.1.1**: `test_xhr_request_capture()` - XHR 요청 캡처
  - File: `backend/tests/unit/discovery/test_network_capturer.py`
  - Test Cases:
    - Capture XMLHttpRequest to /api/users
    - Extract request URL, method, headers
    - Handle async requests
    - Capture response metadata

- [ ] **Test 3.1.2**: `test_fetch_request_capture()` - Fetch 요청 캡처
  - File: `backend/tests/unit/discovery/test_network_capturer.py`
  - Test Cases:
    - Capture fetch() calls
    - Handle various fetch options (mode, credentials)
    - Extract request/response headers
    - Handle streaming responses

- [ ] **Test 3.1.3**: `test_cors_preflight_detection()` - OPTIONS 요청 탐지
  - File: `backend/tests/unit/discovery/test_network_capturer.py`
  - Test Cases:
    - Detect OPTIONS preflight requests
    - Identify cross-origin requests
    - Extract Origin header
    - Match preflight with actual request

- [ ] **Test 3.1.4**: `test_cors_allowed_origins()` - 허용된 Origin 추출
  - File: `backend/tests/unit/discovery/test_network_capturer.py`
  - Test Cases:
    - Extract Access-Control-Allow-Origin from response
    - Handle wildcard (`*`)
    - Handle multiple origins (via Vary header)
    - Detect overly permissive CORS

- [ ] **Test 3.1.5**: `test_graphql_query_extraction()` - GraphQL Query 추출
  - File: `backend/tests/unit/discovery/test_network_capturer.py`
  - Test Cases:
    - Detect GraphQL endpoint (/graphql)
    - Extract query from POST body
    - Parse query operation name
    - Extract variables

- [ ] **Test 3.1.6**: `test_graphql_mutation_extraction()` - GraphQL Mutation 추출
  - File: `backend/tests/unit/discovery/test_network_capturer.py`
  - Test Cases:
    - Detect mutation operations
    - Extract mutation name
    - Flag potentially dangerous mutations
    - Handle batched queries

- [ ] **Test 3.1.7**: `test_graphql_introspection()` - 인트로스펙션 쿼리 탐지
  - File: `backend/tests/unit/discovery/test_network_capturer.py`
  - Test Cases:
    - Detect __schema query
    - Detect __type query
    - Flag introspection enabled
    - Extract schema information

- [ ] **Test 3.1.8**: `test_websocket_url_capture()` - WebSocket 연결 URL
  - File: `backend/tests/unit/discovery/test_network_capturer.py`
  - Test Cases:
    - Capture WebSocket connection URLs
    - Handle upgrade requests
    - Extract connection parameters
    - Track connection lifecycle

- [ ] **Test 3.1.9**: `test_websocket_protocol_detection()` - ws/wss 프로토콜
  - File: `backend/tests/unit/discovery/test_network_capturer.py`
  - Test Cases:
    - Detect ws:// vs wss:// protocol
    - Flag insecure WebSocket on HTTPS page
    - Extract Sec-WebSocket-Protocol header
    - Handle custom subprotocols

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 3.1.10**: `NetworkCapturerModule` 구현
  - File: `backend/app/services/discovery/modules/network_capturer.py`
  - Goal: Make Tests 3.1.1-3.1.9 pass
  - Components:
    - `RequestInterceptor`
    - `CorsAnalyzer`
    - `GraphQLDetector`
    - `WebSocketTracker`
  - Implementation Notes:
    ```python
    class NetworkCapturerModule(BaseDiscoveryModule):
        name = "network_capturer"
        profiles = {ScanProfile.STANDARD, ScanProfile.FULL}

        async def discover(self, context: DiscoveryContext) -> AsyncIterator[DiscoveredAsset]:
            async with context.browser.new_context() as browser_context:
                page = await browser_context.new_page()

                # Enable request interception
                await page.route("**/*", self._intercept_request)

                # Listen for WebSocket connections
                page.on("websocket", self._handle_websocket)

                # Navigate and collect
                await page.goto(context.target_url)
                await page.wait_for_load_state("networkidle")

                # Yield discovered assets
                for asset in self._collected_assets:
                    yield asset
    ```

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 3.1.11**: 중복 요청 필터링, 성능 최적화, 배치 처리
  - Checklist:
    - [ ] Request deduplication by URL + method
    - [ ] Batch yield for efficiency
    - [ ] Memory-efficient streaming
    - [ ] Timeout handling
    - [ ] Connection pooling

---

## ✋ Quality Gate

**⚠️ STOP: Do NOT proceed to Phase 4 until ALL checks pass**

### TDD Compliance (CRITICAL)
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Line coverage ≥ 85%, Branch ≥ 80%

### Build & Tests
- [ ] **All Tests Pass**: `cd backend && pytest tests/unit/discovery/test_network_capturer.py`
- [ ] **Coverage**: `cd backend && pytest --cov=app/services/discovery/modules/network_capturer --cov-report=term-missing`
- [ ] **Integration Test**: Test with real browser context
- [ ] **No Flaky Tests**: Run tests 3+ times consistently

### Code Quality
- [ ] **Linting**: `cd backend && ruff check app/services/discovery/modules/network_capturer.py`
- [ ] **Formatting**: `cd backend && black --check app/services/discovery/modules/`
- [ ] **Type Check**: `cd backend && mypy app/services/discovery/modules/network_capturer.py`

### Performance
- [ ] **Request Processing**: < 10ms per request
- [ ] **Memory Usage**: < 100MB for 1000 requests
- [ ] **No Memory Leaks**: Stable over extended runs

### Manual Verification
- [ ] XHR/Fetch captured from real SPA
- [ ] GraphQL operations correctly identified
- [ ] WebSocket connections tracked
- [ ] CORS configurations detected

---

## 📊 Progress Tracking

| Section | Items | Completed | Progress |
|---------|-------|-----------|----------|
| 3.1 Network Capturer | 11 | 0 | 0% |
| **Total** | **11** | **0** | **0%** |

---

## 🔗 Navigation

| Previous | Current | Next |
|----------|---------|------|
| [Phase 2: Basic Modules](./phase2-basic-modules.md) | **Phase 3: Network Module** | [Phase 4: Analysis Modules](./phase4-analysis-modules.md) |

[← Back to Index](./README.md)

---

## 📝 Notes

### Parallel Execution
Phase 3은 Phase 2, Phase 4와 **병렬로 실행 가능**합니다.
Phase 1만 완료되면 독립적으로 개발을 시작할 수 있습니다.

### Downstream Dependencies
- **Phase 5.1 InteractionEngine**: NetworkCapturer 결과 소비
- **Phase 5.4 ApiSchemaGenerator**: NetworkCapturer + JsAnalyzer 복합 의존
