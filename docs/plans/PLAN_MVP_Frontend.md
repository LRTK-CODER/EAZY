# Implementation Plan: MVP Frontend

**Status**: ✅ Completed
**Started**: 2025-12-28
**Last Updated**: 2025-12-28
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
Build the Frontend for EAZY MVP using **React** (Vite), **TypeScript**, **TailwindCSS**, and **shadcn/ui**.
The frontend will provide a dashboard to manage Projects, Targets, and view Scan Results.

### Success Criteria
- [ ] Project initializes successfully with Vite & TypeScript.
- [ ] Shadcn/UI components configured and working.
- [ ] Users can Create/List Projects and Targets via UI.
- [ ] Users can trigger scans and view results (Assets).
- [ ] **TDD**: Component tests implemented using Vitest & React Testing Library.

### User Impact
- Provides a graphical interface for the DAST tool, replacing raw API calls.
- Visualizes attack surface data for easier analysis.

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| **Vite** | Fast build time, modern ecosystem. | - |
| **shadcn/ui** | Copy-paste components, high customizability, accessible. | Requires manual component management (not an npm package). |
| **Zustand** | Simple global state management (if needed). | Less boilerplate than Redux. |
| **TanStack Query** | Server state management (API cache, loading states). | Adding complexity for simple apps, but essential for data-heavy dashboard. |
| **Atomic Layout** | `components/ui` (atoms), `components/features` (molecules/organisms), `pages` (templates). | Promotes reusability and small component size. |

---

## 📦 Dependencies

### Required Before Starting
- Backend API running (for integration)

### External Dependencies
- `react`, `react-dom`, `react-router-dom`
- `axios` (or `ky` / `fetch`)
- `@tanstack/react-query`
- `tailwindcss`, `postcss`, `autoprefixer`
- `lucide-react` (icons)
- `clsx`, `tailwind-merge` (utils)
- `zod`, `react-hook-form` (forms)
- **Dev**: `vitest`, `@testing-library/react`, `jsdom`

---

## 🧪 Test Strategy

### Testing Approach
**TDD (Test-Driven Development)**:
1.  **RED**: Write a failing test for a component (e.g., "renders project list").
2.  **GREEN**: Implement the component to pass the test.
3.  **REFACTOR**: Improve code structure and styles.

### Test Pyramid for This Feature
| Test Type | Coverage Target | Purpose |
|-----------|-----------------|---------|
| **Unit/Component** | ≥80% | UI components, Hooks, Utils |
| **Integration** | Critical Flows | Page-level interaction (mocked API) |

---

## 🚀 Implementation Phases

### Phase 1: Project Initialization & Infrastructure
**Goal**: Setup React+Vite project with basic tooling and structure.
**Estimated Time**: 2 hours
**Status**: ⏳ Pending

#### Tasks
**🔴 RED: Write Failing Tests First**
- [x] **Test 1.1**: App render test
    - File: `frontend/src/App.test.tsx` (to be created)
    - Content: Verify App component renders "EAZY".

**🟢 GREEN: Implement to Make Tests Pass**
- [x] **Task 1.2**: Initialize Vite Project
    - Command: `npm create vite@latest frontend -- --template react-ts`
    - Setup TailwindCSS.
    - Setup Folder Structure (`src/components`, `src/pages`, `src/lib`, `src/hooks`).
- [x] **Task 1.3**: Configure Test Runner (Vitest)
    - Install `vitest`, `jsdom`, `@testing-library/react`.
    - Create `vitest.setup.ts`.
- [x] **Task 1.4**: Install Basic Dependencies
    - `react-router-dom`, `clsx`, `tailwind-merge`.

#### Quality Gate ✋
- [x] `npm run dev` starts the server.
- [x] `npm run test` passes (App render).

---

### Phase 2: Layout & Design System Base
**Goal**: Implement basic layout (Sidebar, Header) and install core shadcn components.
**Estimated Time**: 3 hours
**Status**: ⏳ Pending

#### Tasks
**🔴 RED: Write Failing Tests First**
- [x] **Test 2.1**: Sidebar Navigation Test
    - Verify "Dashboard", "Projects" links exist.
- [x] **Test 2.2**: Layout Wrapper Test
    - Verify children are rendered within the layout.

**🟢 GREEN: Implement to Make Tests Pass**
- [x] **Task 2.3**: Install Shadcn/UI CLI & Init
    - Configure `components.json`.
- [ ] **Task 2.4**: Add Base Components
    - `button`, `card`, `input`, `table` (via shadcn).
    - `components/ui/...`
- [ ] **Task 2.5**: Create Layout Components
    - `components/layout/Sidebar.tsx`
    - `components/layout/Header.tsx`
    - `components/layout/MainLayout.tsx`
- [ ] **Task 2.6**: Setup Routing
    - `App.tsx` with `ReactRouter`.
    
**🔵 REFACTOR: Improve Code Quality**
- [ ] **Task 2.7**: Refactor Sidebar Components
    - Extract NavItems to config.
    - optimize re-renders.

#### Quality Gate ✋
- [ ] All UI components compile.
- [ ] Layout tests pass.

---

### Phase 3: Project Management Feature
**Goal**: CRUD for Projects (List, Create).
**Estimated Time**: 4 hours
**Status**: ⏳ Pending

#### Tasks
**🔴 RED: Write Failing Tests First**
- [ ] **Test 3.1**: Project List Component Test
    - Mock API response.
    - Verify list of projects is displayed.
- [ ] **Test 3.2**: Create Project Form Test
    - Verify input fields (Name, Desc) and Submit button.
    - Verify form submission triggers API call.

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 3.3**: API Client Setup
    - `lib/api.ts` (Axios instance).
    - `services/projectService.ts`.
- [ ] **Task 3.4**: Project List Page
    - `pages/projects/ProjectList.tsx`
    - Use TanStack Query (`useQuery`).
- [ ] **Task 3.5**: Create Project Modal/Page
    - `components/features/project/CreateProjectForm.tsx`
    - Use React Hook Form + Zod.

**🔵 REFACTOR: Improve Code Quality**
- [ ] **Task 3.6**: Abstract Form Logic
    - Create generic `useForm` wrapper if needed.
    - Ensure clear separation of API logic (`hooks/useProjects`) and UI.

#### Quality Gate ✋
- [ ] Can view projects from backend.
- [ ] Can create a new project.
- [ ] Tests pass with mocked API.

---

### Phase 4: Target Management & Scanner Integration
**Goal**: Manage Targets within a Project and Trigger Scans.
**Estimated Time**: 4 hours
**Status**: ⏳ Pending

#### Tasks
**🔴 RED: Write Failing Tests First**
- [ ] **Test 4.1**: Target List Test
    - Mock Projects/{id}/Targets.
- [ ] **Test 4.2**: Scan Trigger Test
    - Verify "Scan" button calls API.

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 4.3**: Target List Component
    - `components/features/target/TargetList.tsx`
- [ ] **Task 4.4**: Add Target Form
    - `components/features/target/CreateTargetForm.tsx` (Name, URL, Scope).
- [ ] **Task 4.5**: Trigger Scan Logic
    - Connect `POST /projects/{id}/targets/{id}/scan`.

**🔵 REFACTOR: Improve Code Quality**
- [ ] **Task 4.6**: Optimistic Updates
    - Update UI immediately after Scan Trigger (optional).
    - Extract Target-related components.

#### Quality Gate ✋
- [ ] Can add a target to a project.
- [ ] Can click "Scan" and see toast/response.

---

### Phase 5: Dashboard & Scan Results
**Goal**: Visualize scan results (Assets).
**Estimated Time**: 3 hours
**Status**: ⏳ Pending

#### Tasks
**🔴 RED: Write Failing Tests First**
- [ ] **Test 5.1**: Asset Table Test
    - Verify rendering of Method, URL, Type.

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 5.2**: Asset Service & Query
    - `GET /tasks/{id}/assets`.
    - (Optional) `GET /projects/{id}/assets` (Total View) - *Needs Backend Support or derived view*.
- [ ] **Task 5.3**: Asset Table Component
    - `components/features/asset/AssetTable.tsx`.
    - Columns: Hash, Method, URL, Type, Last Seen.

**🔵 REFACTOR: Improve Code Quality**
- [ ] **Task 5.4**: Optimize Data Table
    - Implement pagination/sorting if data is large.
    - Memoize expensive rows.

#### Quality Gate ✋
- [ ] Can view results of a scan.

---

## 📝 Notes & Learnings
*   (To be filled during implementation)
