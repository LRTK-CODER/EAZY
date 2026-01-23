# Phase 6: 통합 테스트 (Integration)

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
모든 Discovery 모듈을 crawler_service.py에 통합하고,
프로필별 전체 플로우를 검증하는 E2E 테스트를 구현합니다.

### Success Criteria
- [ ] 모든 모듈이 crawler_service에 통합됨
- [ ] 프로필별 모듈 활성화가 올바르게 동작
- [ ] 모듈 간 에러 격리가 보장됨
- [ ] QUICK, STANDARD, FULL 프로필 E2E 테스트 통과

### Dependencies
- **Phase 1-5**: 모든 이전 Phase 완료 필수

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| asyncio.gather for parallel | 병렬 모듈 실행, 성능 최적화 | 에러 처리 복잡 |
| Error isolation | 단일 모듈 실패가 전체 실패로 이어지지 않음 | 부분 결과 처리 필요 |
| Profile-based activation | 스캔 속도/정밀도 트레이드오프 | 모듈 선택 로직 필요 |

---

## 🚀 Implementation Sections

### 6.1 crawler_service.py 통합

**Goal**: 모든 Discovery 모듈을 crawler_service에 통합

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 6.1.1**: `test_discovery_module_integration()` - 모듈 통합 실행
  - File: `backend/tests/integration/discovery/test_crawler_integration.py`
  - Test Cases:
    - All registered modules are invoked
    - Results from all modules are collected
    - Module execution is orchestrated correctly
    - Discovery results are passed to next stage

- [ ] **Test 6.1.2**: `test_profile_based_module_activation()` - 프로필별 모듈 활성화
  - File: `backend/tests/integration/discovery/test_crawler_integration.py`
  - Test Cases:
    - QUICK profile activates only fast modules
    - STANDARD profile activates core modules
    - FULL profile activates all modules
    - Module.is_active_for(profile) is respected

- [ ] **Test 6.1.3**: `test_asset_deduplication()` - 중복 Asset 제거
  - File: `backend/tests/integration/discovery/test_crawler_integration.py`
  - Test Cases:
    - Same URL discovered by multiple modules is deduplicated
    - Deduplication uses DiscoveredAsset.__hash__
    - Metadata is merged or latest is kept
    - Count is accurate after deduplication

- [ ] **Test 6.1.4**: `test_module_error_isolation()` - 모듈 에러 격리
  - File: `backend/tests/integration/discovery/test_crawler_integration.py`
  - Test Cases:
    - Single module failure doesn't crash scan
    - Error is logged with module name
    - Other modules continue execution
    - Partial results are returned

- [ ] **Test 6.1.5**: `test_parallel_module_execution()` - 병렬 모듈 실행
  - File: `backend/tests/integration/discovery/test_crawler_integration.py`
  - Test Cases:
    - Independent modules run in parallel
    - asyncio.gather is used for parallelization
    - Dependent modules wait for prerequisites
    - Execution time is optimized

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 6.1.6**: `crawler_service.py` Discovery 통합
  - File: `backend/app/services/crawler_service.py`
  - Goal: Make Tests 6.1.1-6.1.5 pass
  - Implementation:
    ```python
    class CrawlerService:
        def __init__(self, discovery_registry: DiscoveryModuleRegistry):
            self._discovery_registry = discovery_registry

        async def run_discovery(
            self,
            context: DiscoveryContext,
            profile: ScanProfile
        ) -> set[DiscoveredAsset]:
            modules = self._discovery_registry.get_by_profile(profile)

            async def run_module_safe(module: BaseDiscoveryModule):
                try:
                    return [asset async for asset in module.discover(context)]
                except Exception as e:
                    logger.error(f"Module {module.name} failed: {e}")
                    return []

            results = await asyncio.gather(
                *[run_module_safe(m) for m in modules],
                return_exceptions=False
            )

            all_assets = set()
            for module_assets in results:
                all_assets.update(module_assets)

            return all_assets
    ```

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 6.1.7**: 병렬 실행 최적화, 에러 복구 전략
  - Checklist:
    - [ ] Semaphore for concurrent limit
    - [ ] Retry logic for transient failures
    - [ ] Progress tracking/reporting
    - [ ] Graceful shutdown on cancel

---

### 6.2 E2E 테스트

**Goal**: 프로필별 전체 스캔 플로우 검증

#### 🔴 RED: Write Failing Tests First

- [ ] **Test 6.2.1**: `test_quick_scan_e2e()` - Quick 프로필 전체 플로우
  - File: `backend/tests/e2e/discovery/test_scan_e2e.py`
  - Test Cases:
    - Complete scan with QUICK profile
    - Only fast modules are executed
    - Results are within expected bounds
    - Execution time is under limit

- [ ] **Test 6.2.2**: `test_standard_scan_e2e()` - Standard 프로필 전체 플로우
  - File: `backend/tests/e2e/discovery/test_scan_e2e.py`
  - Test Cases:
    - Complete scan with STANDARD profile
    - Core modules are executed
    - Network traffic is captured
    - HTML and config are parsed

- [ ] **Test 6.2.3**: `test_full_scan_e2e()` - Full 프로필 전체 플로우
  - File: `backend/tests/e2e/discovery/test_scan_e2e.py`
  - Test Cases:
    - Complete scan with FULL profile
    - All modules are executed
    - AST analysis is performed
    - Dynamic interaction is tested

- [ ] **Test 6.2.4**: `test_scan_time_limits()` - 프로필별 시간 제한 검증
  - File: `backend/tests/e2e/discovery/test_scan_e2e.py`
  - Test Cases:
    - QUICK scan completes in < 30 seconds
    - STANDARD scan completes in < 2 minutes
    - FULL scan completes in < 5 minutes
    - Timeout is respected and scan stops gracefully

#### 🟢 GREEN: Implement to Make Tests Pass

- [ ] **Task 6.2.5**: E2E 테스트 통과
  - Files: E2E test fixtures, test server setup
  - Goal: Make Tests 6.2.1-6.2.4 pass
  - Components:
    - Test target web application (fixtures)
    - Test data with known URLs
    - Expected results for verification
    - Time measurement utilities

#### 🔵 REFACTOR: Clean Up Code

- [ ] **Task 6.2.6**: 성능 벤치마크, 메모리 프로파일링
  - Checklist:
    - [ ] Benchmark test framework setup
    - [ ] Memory profiling with memray
    - [ ] Performance regression detection
    - [ ] CI integration for E2E tests

---

## ✋ Quality Gate

**⚠️ STOP: Do NOT proceed to Phase 7 until ALL checks pass**

### TDD Compliance (CRITICAL)
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Line coverage ≥ 80%, Branch ≥ 75%

### Build & Tests
- [ ] **Unit Tests**: `cd backend && pytest tests/unit/discovery/ -v`
- [ ] **Integration Tests**: `cd backend && pytest tests/integration/discovery/ -v`
- [ ] **E2E Tests**: `cd backend && pytest tests/e2e/discovery/ -v`
- [ ] **All Profiles**: QUICK, STANDARD, FULL all pass

### Code Quality
- [ ] **Linting**: `cd backend && ruff check app/services/`
- [ ] **Formatting**: `cd backend && black --check app/services/`
- [ ] **Type Check**: `cd backend && mypy app/services/`

### Performance
- [ ] **QUICK Profile**: < 30 seconds on test target
- [ ] **STANDARD Profile**: < 2 minutes on test target
- [ ] **FULL Profile**: < 5 minutes on test target
- [ ] **Memory**: < 500MB peak usage

### Manual Verification
- [ ] Run QUICK scan against real website
- [ ] Run STANDARD scan against real website
- [ ] Verify all expected URLs discovered
- [ ] Check for no false positives in results

---

## 📊 Progress Tracking

| Section | Items | Completed | Progress |
|---------|-------|-----------|----------|
| 6.1 crawler_service Integration | 7 | 0 | 0% |
| 6.2 E2E Tests | 6 | 0 | 0% |
| **Total** | **13** | **0** | **0%** |

---

## 🔗 Navigation

| Previous | Current | Next |
|----------|---------|------|
| [Phase 5: Advanced Modules](./phase5-advanced-modules.md) | **Phase 6: Integration** | [Phase 7: Performance](./phase7-performance.md) |

[← Back to Index](./README.md)

---

## 📝 Notes

### E2E Test Infrastructure
E2E 테스트를 위해 테스트용 웹 애플리케이션이 필요합니다:
- 알려진 URL 패턴을 포함한 정적 사이트
- Dynamic content를 포함한 SPA
- 다양한 기술 스택 사용

```
backend/tests/e2e/fixtures/
├── static_site/          # 정적 HTML/JS/CSS
├── spa_react/            # React SPA 샘플
└── expected_results/     # 예상 결과 JSON
```

### Profile Time Limits
| Profile | Target Time | Hard Limit |
|---------|-------------|------------|
| QUICK | < 30s | 60s |
| STANDARD | < 2m | 5m |
| FULL | < 5m | 15m |
