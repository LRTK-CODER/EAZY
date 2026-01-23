# Phase 7: 성능 및 Edge Case 테스트 (Performance & Edge Cases)

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
대용량 데이터 처리, Edge Case, 에러 상황에 대한 테스트를 구현하여
시스템의 견고성(robustness)을 검증합니다.

### Success Criteria
- [ ] 1MB HTML/JS 파일 처리 성능 기준 충족
- [ ] 난독화된 JS, Shadow DOM 등 Edge Case 처리
- [ ] 네트워크 에러, 타임아웃 등 에러 상황 복구
- [ ] 메모리 사용량 제한 준수

### Dependencies
- **Phase 1-6**: 모든 이전 Phase 완료 필수

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| Streaming processing | 메모리 효율적 대용량 처리 | 구현 복잡도 증가 |
| Graceful degradation | 부분 실패 시에도 결과 제공 | 불완전한 결과 가능 |
| Circuit breaker | 연속 실패 시 빠른 실패 | 일시적 서비스 중단 |

---

## 🚀 Implementation Sections

### 7.1 성능 테스트

**Goal**: 대용량 데이터 처리 성능 검증

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 7.1.1**: `test_large_html_parsing()` - 1MB HTML 파싱 < 2초
  - File: `backend/tests/performance/discovery/test_performance.py`
  - Test Cases:
    - Parse 1MB HTML file in < 2 seconds
    - Memory usage stays under 200MB
    - All URLs are extracted correctly
    - No memory leak after parsing

- [ ] **Test 7.1.2**: `test_large_js_analysis()` - 1MB JS 분석 < 5초
  - File: `backend/tests/performance/discovery/test_performance.py`
  - Test Cases:
    - Analyze 1MB JavaScript file in < 5 seconds
    - Memory usage stays under 500MB
    - Regex analysis completes faster than AST
    - Results are accurate

- [ ] **Test 7.1.3**: `test_concurrent_requests()` - 동시 요청 처리
  - File: `backend/tests/performance/discovery/test_performance.py`
  - Test Cases:
    - Handle 100 concurrent requests
    - No request timeout under normal load
    - Connection pool is properly managed
    - Resource cleanup on completion

- [ ] **Test 7.1.4**: `test_memory_usage_limit()` - 메모리 사용량 제한
  - File: `backend/tests/performance/discovery/test_performance.py`
  - Test Cases:
    - Peak memory under 1GB for full scan
    - Memory is released after scan
    - No memory leak over multiple scans
    - GC is triggered appropriately

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 7.1.5**: 성능 기준 충족
  - Files: All discovery modules
  - Goal: Make Tests 7.1.1-7.1.4 pass
  - Optimizations:
    - Streaming HTML parsing
    - Lazy JS loading
    - Connection pooling
    - Memory profiling integration

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 7.1.6**: 캐싱, 스트리밍 처리 최적화
  - Checklist:
    - [ ] LRU cache for parsed results
    - [ ] Streaming response handling
    - [ ] Batch processing for network requests
    - [ ] Memory-mapped file reading

---

### 7.2 Edge Case 테스트

**Goal**: 비정상적 입력 및 특수 케이스 처리 검증

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 7.2.1**: `test_obfuscated_js()` - 난독화된 JS 처리
  - File: `backend/tests/edge_cases/discovery/test_edge_cases.py`
  - Test Cases:
    - Handle webpack obfuscated bundles
    - Handle terser minified code
    - Extract URLs from obfuscated strings
    - Handle eval() and Function() patterns

- [ ] **Test 7.2.2**: `test_shadow_dom()` - Shadow DOM 내 요소
  - File: `backend/tests/edge_cases/discovery/test_edge_cases.py`
  - Test Cases:
    - Access Shadow DOM content
    - Extract URLs from shadow roots
    - Handle open vs closed shadow DOM
    - Process web components

- [ ] **Test 7.2.3**: `test_iframe_content()` - iframe 내 콘텐츠
  - File: `backend/tests/edge_cases/discovery/test_edge_cases.py`
  - Test Cases:
    - Access same-origin iframe content
    - Detect cross-origin iframes
    - Extract URLs from iframe documents
    - Handle nested iframes

- [ ] **Test 7.2.4**: `test_svg_links()` - SVG 내 링크
  - File: `backend/tests/edge_cases/discovery/test_edge_cases.py`
  - Test Cases:
    - Extract xlink:href from SVG
    - Extract href from SVG links
    - Handle inline SVG
    - Handle external SVG files

- [ ] **Test 7.2.5**: `test_unicode_urls()` - 유니코드 URL 처리
  - File: `backend/tests/edge_cases/discovery/test_edge_cases.py`
  - Test Cases:
    - Handle IDN (internationalized domain names)
    - Handle UTF-8 encoded paths
    - Handle percent-encoded Unicode
    - Normalize URL encoding

- [ ] **Test 7.2.6**: `test_relative_url_resolution()` - 상대 URL 해결
  - File: `backend/tests/edge_cases/discovery/test_edge_cases.py`
  - Test Cases:
    - Resolve `../` paths correctly
    - Handle `//` protocol-relative URLs
    - Handle query string only URLs (`?page=2`)
    - Handle fragment only URLs (`#section`)

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 7.2.7**: Edge Case 처리 완료
  - Files: All discovery modules
  - Goal: Make Tests 7.2.1-7.2.6 pass
  - Implementations:
    - Shadow DOM traversal
    - iframe content access
    - SVG parser enhancement
    - URL normalization library

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 7.2.8**: 예외 케이스 문서화
  - Checklist:
    - [ ] Document all edge cases handled
    - [ ] Document known limitations
    - [ ] Add warning logs for skipped content
    - [ ] Update user documentation

---

### 7.3 에러 핸들링 테스트

**Goal**: 네트워크 및 시스템 에러 상황에서의 복구 검증

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 7.3.1**: `test_connection_error_recovery()` - 연결 에러 복구
  - File: `backend/tests/error_handling/discovery/test_error_handling.py`
  - Test Cases:
    - Recover from connection refused
    - Recover from DNS resolution failure
    - Continue scan after single host failure
    - Report partial results

- [ ] **Test 7.3.2**: `test_timeout_handling()` - 타임아웃 처리
  - File: `backend/tests/error_handling/discovery/test_error_handling.py`
  - Test Cases:
    - Handle connection timeout
    - Handle read timeout
    - Handle overall scan timeout
    - Graceful shutdown on timeout

- [ ] **Test 7.3.3**: `test_ssl_error_handling()` - SSL 에러 처리
  - File: `backend/tests/error_handling/discovery/test_error_handling.py`
  - Test Cases:
    - Handle invalid SSL certificate
    - Handle SSL handshake failure
    - Option to skip SSL verification
    - Log SSL errors for review

- [ ] **Test 7.3.4**: `test_rate_limit_backoff()` - Rate Limit 백오프
  - File: `backend/tests/error_handling/discovery/test_error_handling.py`
  - Test Cases:
    - Detect 429 Too Many Requests
    - Implement exponential backoff
    - Respect Retry-After header
    - Continue after rate limit clears

- [ ] **Test 7.3.5**: `test_malformed_html_handling()` - 잘못된 HTML 처리
  - File: `backend/tests/error_handling/discovery/test_error_handling.py`
  - Test Cases:
    - Handle unclosed tags
    - Handle invalid nesting
    - Handle encoding errors
    - Extract what's possible

- [ ] **Test 7.3.6**: `test_invalid_js_handling()` - 잘못된 JS 처리
  - File: `backend/tests/error_handling/discovery/test_error_handling.py`
  - Test Cases:
    - Handle syntax errors
    - Fallback from AST to regex
    - Handle partial parsing
    - Log parse failures

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 7.3.7**: 에러 핸들링 완료
  - Files: All discovery modules, HTTP client wrapper
  - Goal: Make Tests 7.3.1-7.3.6 pass
  - Implementations:
    - Retry decorator with backoff
    - Circuit breaker pattern
    - Graceful degradation
    - Comprehensive error logging

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 7.3.8**: 에러 로깅, 모니터링 통합
  - Checklist:
    - [ ] Structured error logging
    - [ ] Error categorization
    - [ ] Metrics for error rates
    - [ ] Alerting integration

---

## ✋ Quality Gate

**⚠️ STOP: This is the final phase - ensure ALL checks pass before completion**

### TDD Compliance (CRITICAL)
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Line coverage ≥ 80%, Branch ≥ 75%

### Build & Tests
- [ ] **Unit Tests**: `cd backend && pytest tests/unit/discovery/ -v`
- [ ] **Integration Tests**: `cd backend && pytest tests/integration/discovery/ -v`
- [ ] **E2E Tests**: `cd backend && pytest tests/e2e/discovery/ -v`
- [ ] **Performance Tests**: `cd backend && pytest tests/performance/discovery/ -v`
- [ ] **Edge Case Tests**: `cd backend && pytest tests/edge_cases/discovery/ -v`
- [ ] **Error Handling Tests**: `cd backend && pytest tests/error_handling/discovery/ -v`

### Code Quality
- [ ] **Linting**: `cd backend && ruff check .`
- [ ] **Formatting**: `cd backend && black --check .`
- [ ] **Type Check**: `cd backend && mypy app/`

### Performance Benchmarks
| Test | Target | Actual |
|------|--------|--------|
| 1MB HTML parsing | < 2s | ___ |
| 1MB JS analysis | < 5s | ___ |
| 100 concurrent requests | handled | ___ |
| Peak memory (full scan) | < 1GB | ___ |

### Final Verification
- [ ] All 173+ tasks completed across all phases
- [ ] Total coverage ≥ 85%
- [ ] No critical/high security issues
- [ ] Documentation complete
- [ ] Ready for production deployment

---

## 📊 Progress Tracking

| Section | Items | Completed | Progress |
|---------|-------|-----------|----------|
| 7.1 Performance Tests | 6 | 0 | 0% |
| 7.2 Edge Case Tests | 8 | 0 | 0% |
| 7.3 Error Handling Tests | 8 | 0 | 0% |
| **Total** | **22** | **0** | **0%** |

---

## 🔗 Navigation

| Previous | Current | Next |
|----------|---------|------|
| [Phase 6: Integration](./phase6-integration.md) | **Phase 7: Performance** | - (Final Phase) |

[← Back to Index](./README.md)

---

## 📝 Notes

### Performance Testing Tools
```bash
# 메모리 프로파일링
pip install memray
memray run -o output.bin pytest tests/performance/
memray flamegraph output.bin

# 시간 측정
pytest --durations=10 tests/performance/

# 부하 테스트
pip install locust
locust -f tests/load/locustfile.py
```

### Test Data Generation
대용량 테스트 데이터 생성:
```bash
# 1MB HTML 생성
python scripts/generate_test_html.py --size 1MB --output tests/fixtures/large.html

# 1MB JS 생성
python scripts/generate_test_js.py --size 1MB --output tests/fixtures/large.js
```

### Known Limitations (Document)
Phase 7 완료 시 다음 항목을 문서화:
- 지원되지 않는 Edge Cases
- 성능 제한 사항
- 에러 복구 불가능한 상황
- 권장 설정 값

---

## ✅ Final Checklist

**Active Scan 개편 완료 전 최종 확인:**

- [ ] Phase 1: 기반 구조 - 100% 완료
- [ ] Phase 2: 기본 모듈 - 100% 완료
- [ ] Phase 3: 네트워크 모듈 - 100% 완료
- [ ] Phase 4: 분석 모듈 - 100% 완료
- [ ] Phase 5: 고급 모듈 - 100% 완료
- [ ] Phase 6: 통합 테스트 - 100% 완료
- [ ] Phase 7: 성능/Edge Case - 100% 완료
- [ ] 전체 커버리지 ≥ 85%
- [ ] 모든 Quality Gate 통과
- [ ] 문서화 완료
- [ ] 코드 리뷰 완료
- [ ] Production 배포 준비 완료
