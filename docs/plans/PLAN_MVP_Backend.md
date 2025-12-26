# Implementation Plan: MVP Backend (Project Management & Attack Surface)

**Status**: 🔄 In Progress
**Started**: 2025-12-25
**Last Updated**: 2025-12-25
**Estimated Completion**: 2025-12-31

---

**⚠️ CRITICAL INSTRUCTIONS**: After completing each phase:
1. ✅ Check off completed task checkboxes
2. 🧪 Run all quality gate validation commands
3. ⚠️ Verify ALL quality gate items pass
4. 📅 Update "Last Updated" date above
5. 📝 Document learnings in Notes section
6. ➡️ Only then proceed to next phase

⛔ **DO NOT skip quality gates or proceed with failing checks**

---

## 📋 Overview

### Feature Description
Build the core Backend API for EAZY MVP.
This includes setting up the FastAPI server, Database (PostgreSQL), and implementing two key features:
1. **Project Management**: CRUD for Projects and Targets.
2. **Attack Surface Discovery**: Async crawling engine using Playwright to identify URLs and Forms.

### Success Criteria
- [ ] Backend server runs successfully and connects to DB (PostgreSQL) and Redis.
- [ ] Can create/read/update/delete Projects and Targets via REST API.
- [ ] Can trigger a crawl task for a Target and view its status.
- [ ] Crawl results (URLs, Forms) are correctly parsed and stored in the DB.
- [ ] Test coverage > 80% for core modules.

### User Impact
Users will be able to register their assets and automatically identify attack surfaces, creating the foundation for security analysis.

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| **FastAPI** | High performance, async support, auto-generated docs (Swagger). | Slightly steeper learning curve than Flask. |
| **SQLModel** | Combines Pydantic & SQLAlchemy. Great DX for FastAPI. | Newer ecosystem than pure SQLAlchemy. |
| **Playwright** | Better support for modern SPA crawling than Selenium. | Browser binary management required. |
| **Redis Queue (ARQ or Celery)** | Simple async task processing. | Adds infrastructure dependency (Redis). |

---

## 📦 Dependencies

### Required Before Starting
- [ ] Python 3.12+
- [ ] PostgreSQL installed
- [ ] Redis installed

### External Dependencies
- fastapi
- uvicorn
- sqlmodel
- alembic
- playwright
- redis
- pydantic-settings
- **uv** (Package Manager)

---

## 🧪 Test Strategy

### Testing Approach
**TDD Principle**: Write tests FIRST, then implement to make them pass.
Use `pytest` and `httpx` for testing.

### Test Pyramid for This Feature
| Test Type | Coverage Target | Purpose |
|-----------|-----------------|---------|
| **Unit Tests** | ≥80% | Models, Utils, Service logic |
| **Integration Tests** | Critical paths | API Endpoints <-> DB |
| **E2E Tests** | Key user flows | Full flow (Create Project -> Trigger Crawl -> Check Result) |

---

## 🚀 Implementation Phases

### Phase 1: Backend Core & Infrastructure
**Goal**: Initialize FastAPI project, DB connection, and core configurations.
**Estimated Time**: 4 hours
**Status**: ✅ Completed

#### Tasks
**🔴 RED: Write Failing Tests First**
- [x] **Test 1.1**: Test App Health Check
  - File: `backend/tests/api/test_health.py`
  - Content: Request `GET /health` and expect 200 OK.
  - Expected: Fail (Endpoint not exists).

**🟢 GREEN: Implement to Make Tests Pass**
- [x] **Task 1.2**: Initialize Project Structure
  - `backend/app/main.py`, `backend/app/core/config.py`
  - Implement `/health` endpoint.
- [x] **Task 1.3**: Configure Database (SQLModel + AsyncEngine)
  - `backend/app/core/db.py`
- [x] **Task 1.4**: Configure Dependencies
  - `pyproject.toml` (UV / PEP 621)

#### Quality Gate ✋
- [x] Project installs and runs (`uv run uvicorn app.main:app`).
- [x] `pytest` passes.
- [x] DB connection verified.

---

### Phase 2: Project Management API
**Goal**: CRUD APIs for Projects and Targets.
**Estimated Time**: 6 hours
**Status**: ✅ Completed

#### Tasks
**🔴 RED: Write Failing Tests First**
- [x] **Test 2.1**: Project CRUD Tests
  - File: `backend/tests/api/test_projects.py`
  - Content: Create, List, Get Single Project.
- [x] **Test 2.2**: Target CRUD Tests
  - File: `backend/tests/api/test_targets.py`
  - Content: Create Target under Project, List Targets.

**🟢 GREEN: Implement to Make Tests Pass**
- [x] **Task 2.3**: Define Models & Migrations
  - `Project` & `Target` SQLModel classes.
  - `alembic revision --autogenerate`.
- [x] **Task 2.4**: Implement Services
  - `ProjectService`, `TargetService` (CRUD logic).
- [x] **Task 2.5**: API Endpoints
  - `POST /projects/`, `GET /projects/`
  - `POST /projects/{id}/targets/`, `GET /targets/`

#### Quality Gate ✋
- [x] All Tests passed.
- [x] API Swagger (`/docs`) verified. successfully.
- [x] API Docs (Swagger) visible and working.

---

### Phase 3: Attack Surface Discovery Engine (Crawler)
**Goal**: Build the engine that crawls targets and discovers assets.
**Estimated Time**: 8 hours
**Status**: ✅ Completed

#### Tasks
**🔴 RED: Write Failing Tests First**
- [x] **Test 3.1**: Task Queue Logic
  - `backend/tests/core/test_task_manager.py`
  - Content: Enqueue task, Dequeue task, status updates.
- [x] **Test 3.2**: Crawler Execution
  - `backend/tests/services/test_crawler.py`
  - Content: Mock Playwright, verify URL extraction.
- [x] **Test 3.3**: Asset Service Deduplication
  - `backend/tests/services/test_asset_service.py`

**🟢 GREEN: Implement to Make Tests Pass**
- [x] **Task 3.3**: Task Model & Migrations
  - `Task` model (id, project_id, type, status, result).
  - Alembic migration.
- [x] **Task 3.4**: Redis Queue Implementation
  - `backend/app/core/queue.py`: `enqueue`, `dequeue`.
- [x] **Task 3.5**: Crawler Service (Playwright)
  - `backend/app/services/crawler_service.py`
  - Headless browser navigation, link extraction.
- [x] **Task 3.6**: Asset Processing Logic
  - Save discovered URLs to `Assets` table.
- [x] **Task 3.7**: Target Scope Update
  - Added `scope` to Target model.

#### Quality Gate ✋
- [x] Task queuing works in Redis.
- [x] Crawler can fetch a page and extract links.
- [x] Discovered assets are saved to DB.

---

### Phase 4: Async Task & Result API
**Goal**: Connect API with Crawler via Redis Queue.
**Estimated Time**: 6 hours
**Status**: 🔄 In Progress

#### Tasks
**🔴 RED: Write Failing Tests First**
- [x] **Test 4.1**: Task Trigger API Test
  - File: `backend/tests/api/test_tasks.py`
  - Content: `POST /projects/{id}/targets/{id}/scan`, expect Task ID.

**🟢 GREEN: Implement to Make Tests Pass**
- [x] **Task 4.2**: Setup Async Worker (ARQ/Celery)
  - `backend/app/worker.py`
- [x] **Task 4.3**: Implement Task Service
  - Enqueue crawl job.
  - Store results to DB (Assets).
- [x] **Task 4.4**: Task Status & Result API
  - `GET /tasks/{id}`, `GET /tasks/{id}/assets` (Impl implicitly via POST return for now, strict GET comes later)

#### Quality Gate ✋
- [x] Full Flow: API -> Redis -> Worker -> Crawler -> DB -> API works.
- [x] Integration tests pass.

---

### Phase 5: Target Management Refinement (REQ-PM-04)
**Goal**: Implement Delete and Update operations for Targets.
**Estimated Time**: 2 hours
**Status**: ⏳ Pending

#### Tasks
**🔴 RED: Write Failing Tests First**
- [x] **Test 5.1**: Target Delete Verification
  - File: `backend/tests/api/test_targets.py`
  - Content: `DELETE /projects/{id}/targets/{target_id}`.
  - Verify Cascade Delete (or prevention).
- [x] **Test 5.2**: Target Update Verification
  - `PATCH /projects/{id}/targets/{target_id}`.
  - Verify name/url updates.

**🟢 GREEN: Implement to Make Tests Pass**
- [x] **Task 5.3**: Update TargetService
  - Add `delete_target` and `update_target` methods.
- [x] **Task 5.4**: Add API Endpoints
  - Implement DELETE and PATCH routes.

#### Quality Gate ✋
- [x] `pytest tests/api/test_targets.py` passes.
- [x] Swagger Docs show Delete/Patch options.

---

## 📝 Notes & Learnings
*   (To be filled during implementation)
