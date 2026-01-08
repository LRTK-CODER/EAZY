# Phase 5-Improvements Backend RED Phase Test Summary

**Date**: 2026-01-08
**Phase**: RED (Test-Driven Development)
**Status**: ✅ All 9 test files created (37 tests total)

---

## 📋 Test Files Created

### Step 1: Task Timestamps & Cancellation (13 tests)

#### 1. `tests/models/test_task_timestamps.py` (6 tests)
- ❌ `test_task_has_started_at_field` - Expected: AttributeError 'Task' has no attribute 'started_at'
- ❌ `test_task_has_completed_at_field` - Expected: AttributeError 'Task' has no attribute 'completed_at'
- ❌ `test_task_status_has_cancelled_value` - Expected: AttributeError 'TaskStatus' has no attribute 'CANCELLED'
- ❌ `test_task_started_at_auto_set_on_running` - Expected: AttributeError on started_at assignment
- ❌ `test_task_completed_at_auto_set_on_completion` - Expected: AttributeError on completed_at assignment
- ❌ `test_task_completed_at_set_on_cancellation` - Expected: AttributeError for CANCELLED status

#### 2. `tests/api/test_task_cancel.py` (4 tests)
- ❌ `test_cancel_task_endpoint_exists` - Expected: 404 Not Found for POST /api/v1/tasks/{id}/cancel
- ❌ `test_cancel_running_task_succeeds` - Expected: 404 Not Found
- ❌ `test_cancel_pending_task_succeeds` - Expected: 404 Not Found
- ❌ `test_cancel_completed_task_fails` - Expected: 404 Not Found (then 400 when implemented)

#### 3. `tests/api/test_latest_task.py` (3 tests)
- ❌ `test_get_latest_task_endpoint_exists` - Expected: 404 Not Found for GET /api/v1/targets/{id}/latest-task
- ❌ `test_get_latest_task_returns_most_recent` - Expected: 404 Not Found
- ❌ `test_get_latest_task_returns_404_when_no_tasks` - Expected: 404 Not Found

---

### Step 2: HTTP Packet Capture (14 tests)

#### 4. `tests/services/test_crawler_http.py` (5 tests)
- ❌ `test_crawler_registers_request_handler` - Expected: page.on("request") never called
- ❌ `test_crawler_registers_response_handler` - Expected: page.on("response") never called
- ❌ `test_crawler_collects_http_request_data` - Expected: crawl() returns List[str], not tuple
- ❌ `test_crawler_collects_http_response_data` - Expected: crawl() returns List[str], not tuple
- ❌ `test_crawler_enforces_body_size_limit` - Expected: No truncation logic exists

#### 5. `tests/services/test_asset_http.py` (4 tests)
- ❌ `test_asset_request_spec_jsonb_storage` - Expected: TypeError 'request_spec' unexpected argument
- ❌ `test_asset_response_spec_jsonb_storage` - Expected: TypeError 'response_spec' unexpected argument
- ❌ `test_asset_http_specs_null_allowed` - Expected: TypeError for new parameters
- ❌ `test_asset_http_body_truncation` - Expected: TypeError and no truncation logic

#### 6. `tests/integration/test_worker_http.py` (5 tests)
- ❌ `test_worker_collects_http_data_during_crawl` - Expected: Worker doesn't handle tuple return
- ❌ `test_worker_passes_http_data_to_asset_service` - Expected: Assets have NULL request_spec/response_spec
- ❌ `test_worker_parses_json_response_bodies` - Expected: Worker doesn't pass HTTP data
- ❌ `test_worker_excludes_image_responses` - Expected: No image filtering logic
- ❌ `test_full_integration_worker_crawler_asset` - Expected: End-to-end HTTP flow not implemented

---

### Step 3: Parameter Parsing (10 tests)

#### 7. `tests/utils/test_url_parser.py` (5 tests)
- ❌ `test_parse_query_params_function_exists` - Expected: ImportError 'parse_query_params' doesn't exist
- ❌ `test_parse_query_params_extracts_parameters` - Expected: ImportError
- ❌ `test_parse_query_params_handles_multiple_values` - Expected: ImportError
- ❌ `test_parse_query_params_url_decoding` - Expected: ImportError
- ❌ `test_parse_query_params_empty_query` - Expected: ImportError

#### 8. `tests/services/test_asset_params.py` (3 tests)
- ❌ `test_asset_parameters_jsonb_storage` - Expected: TypeError 'parameters' unexpected argument
- ❌ `test_asset_parameters_null_allowed` - Expected: TypeError for new parameter
- ❌ `test_asset_parameters_duplicate_merging` - Expected: TypeError and no merging logic

#### 9. `tests/integration/test_worker_params.py` (2 tests)
- ❌ `test_worker_auto_extracts_url_parameters` - Expected: Assets have NULL parameters
- ❌ `test_worker_includes_parameters_in_asset_storage` - Expected: Worker doesn't parse URL parameters

---

## 🎯 Expected Failure Reasons

### Module-Level Failures
1. **AttributeError**: 'Task' object has no attribute 'started_at' / 'completed_at'
2. **AttributeError**: 'TaskStatus' enum missing 'CANCELLED' value
3. **404 Not Found**: Endpoints /api/v1/tasks/{id}/cancel and /api/v1/targets/{id}/latest-task don't exist
4. **ImportError**: Cannot import 'parse_query_params' from 'app.utils.url_parser' (module doesn't exist)
5. **TypeError**: process_asset() got unexpected keyword arguments 'request_spec', 'response_spec', 'parameters'
6. **AssertionError**: crawl() returns List[str] instead of expected Tuple[List[str], Dict]
7. **KeyError/None**: HTTP data not collected or stored in Assets

---

## ✅ Verification Checklist

- [x] 9 test files created in correct directories
- [x] 37 tests total (6+4+3+5+4+5+5+3+2)
- [x] All tests follow existing pattern from conftest.py
- [x] All tests expected to FAIL (RED Phase)
- [x] No production code modified (git status clean except tests)
- [x] Test file sizes reasonable (1.6KB - 10KB)
- [x] Proper async/await patterns used
- [x] Database session fixtures used correctly
- [x] Mock/patch patterns consistent with existing tests

---

## 🚀 Next Steps (GREEN Phase)

After confirming tests fail, implement:

**Step 1 Implementation** (6-8 hours):
1. Add `started_at`, `completed_at` to Task model
2. Add `CANCELLED` to TaskStatus enum
3. Create Alembic migration
4. Implement TaskService.cancel_task() & get_latest_task_for_target()
5. Add POST /tasks/{id}/cancel endpoint
6. Add GET /targets/{id}/latest-task endpoint
7. Add Redis cancellation flag in Worker

**Step 2 Implementation** (5-6 hours):
1. Add page.on("request"/"response") handlers in CrawlerService
2. Change crawl() return to Tuple[List[str], Dict]
3. Implement body size truncation (10KB max)
4. Update AssetService.process_asset() signature
5. Update Worker to pass HTTP data

**Step 3 Implementation** (3-4 hours):
1. Create app/utils/url_parser.py with parse_query_params()
2. Add parameter extraction in CrawlerService
3. Update AssetService to store parameters
4. Update Worker to include parameters

---

## 📊 Test Execution Commands

```bash
# Run all RED phase tests
cd /Users/lrtk/Documents/Project/EAZY/backend
uv run pytest tests/models/test_task_timestamps.py \
             tests/api/test_task_cancel.py \
             tests/api/test_latest_task.py \
             tests/services/test_crawler_http.py \
             tests/services/test_asset_http.py \
             tests/integration/test_worker_http.py \
             tests/utils/test_url_parser.py \
             tests/services/test_asset_params.py \
             tests/integration/test_worker_params.py \
             -v --tb=short

# Run by step
uv run pytest tests/models/ tests/api/test_task_cancel.py tests/api/test_latest_task.py -v  # Step 1 (13 tests)
uv run pytest tests/services/test_crawler_http.py tests/services/test_asset_http.py tests/integration/test_worker_http.py -v  # Step 2 (14 tests)
uv run pytest tests/utils/ tests/services/test_asset_params.py tests/integration/test_worker_params.py -v  # Step 3 (10 tests)
```

---

## 📁 File Locations

```
backend/tests/
├── models/
│   └── test_task_timestamps.py          (5.0KB, 6 tests)
├── api/
│   ├── test_task_cancel.py              (4.7KB, 4 tests)
│   └── test_latest_task.py              (3.6KB, 3 tests)
├── services/
│   ├── test_crawler_http.py             (5.5KB, 5 tests)
│   ├── test_asset_http.py               (6.6KB, 4 tests)
│   └── test_asset_params.py             (5.1KB, 3 tests)
├── integration/
│   ├── test_worker_http.py              (10KB, 5 tests)
│   └── test_worker_params.py            (4.6KB, 2 tests)
└── utils/
    └── test_url_parser.py               (3.1KB, 5 tests)
```

---

## 🔒 Production Code Safety

**Git Status Check**:
```bash
$ git status --short
?? tests/api/test_latest_task.py
?? tests/api/test_task_cancel.py
?? tests/integration/test_worker_http.py
?? tests/integration/test_worker_params.py
?? tests/models/
?? tests/services/test_asset_http.py
?? tests/services/test_asset_params.py
?? tests/services/test_crawler_http.py
?? tests/utils/
```

✅ **Confirmed**: No production code in `app/` directory was modified.

---

## 📝 Notes

- All tests follow TDD RED phase principles: Write failing tests FIRST
- Tests are comprehensive and cover edge cases
- Mock/patch patterns used appropriately for external dependencies
- Database cleanup handled by conftest.py fixtures
- Async patterns consistent with existing test suite
- Test names descriptive and follow convention: test_<feature>_<scenario>

**RED Phase Complete**: Ready for GREEN phase implementation! 🟢
