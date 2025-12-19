# Implementation Plan

## Project Setup
- [x] Initialize Git repository (Already done)
- [x] Create `README.md` and `task.md`
- [x] **Backend: Environment Setup**
    - [x] Install `uv` (if not installed)
    - [x] Initialize project with `uv init`
    - [x] Pin Python version to 3.12: `uv python pin 3.12`
    - [x] Create `backend/app` directory structure
    - [x] Add dependencies: `uv add fastapi uvicorn pydantic-settings`
    - [x] Create `backend/app/main.py` (Hello World)
    - [x] Configure Environment Variables (`.env`, `config.py`)
- [x] **Backend: Database & Redis**
    - [x] Install Drivers & ORM: `uv add sqlalchemy psycopg2-binary alembic redis`
    - [x] Setup Database Engine (`backend/app/core/db.py`)
    - [x] Setup Declarative Base (`backend/app/models/base.py`)
    - [x] Configure Session Local (`backend/app/core/db.py`)
    - [x] Initialize Alembic: `uv run alembic init backend/alembic`
    - [x] Configure `alembic.ini` and `env.py` for async/sync
    - [x] Setup Redis Client (`backend/app/core/redis.py`)
- [x] **Backend: Logging & Middleware**
    - [x] Install `structlog` or configure standard `logging` to JSON
    - [x] Create Logging Config (`backend/app/core/logging.py`)
    - [x] Implement Request/Response Logging Middleware
    - [x] Setup CORS Middleware (`backend/app/core/middleware.py`)
    - [x] Create Global Exception Handler (`backend/app/core/exceptions.py`)
- [x] **Frontend: Environment Setup**
    - [x] Initialize Vite Project (React + TypeScript): `npm create vite@latest frontend`
    - [x] Install dependencies: `npm install`
    - [x] Setup TailwindCSS & PostCSS
    - [x] Initialize shadcn/ui: `npx shadcn@latest init`
    - [x] Install Core Libraries: `reactflow`, `framer-motion`, `lucide-react`, `axios`, `zustand`

## REQ-1 Project Management
- [ ] **REQ-1-1** Project Creation API & UI
- [ ] **REQ-1-2** Scan Target Registration API & UI
- [ ] **REQ-1-3** LLM Settings Management

## REQ-2 Attack Surface Discovery
- [ ] **REQ-2-1** Pattern-based Active Crawling (Playwright)
- [ ] **REQ-2-2** User-driven Passive Crawling (Mitmproxy)
- [ ] **REQ-2-3** Logic Flow Analysis Module
- [ ] **REQ-2-4** Parameter Specification Parsing
- [ ] **REQ-2-5** LLM-based Function Intent Inference

## REQ-3 AI Vulnerability Analysis
- [ ] **REQ-3-1** Context Generation for LLM
- [ ] **REQ-3-2** Business Logic Vulnerability Analysis
- [ ] **REQ-3-3** Chained Attack Vector Generation

## REQ-4 Attack Execution
- [ ] **REQ-4-1** Intelligent Attack Scheduling
- [ ] **REQ-4-2** Scenario-based Attack Verification (Stateful Fuzzing)
- [ ] **REQ-4-3** False Positive Filtering

## REQ-5 Visualization & Reporting
- [ ] **REQ-5-1** Business Logic Visualization (React Flow)
- [ ] **REQ-5-2** Scan Result Logging & CVSS Calculation
- [ ] **REQ-5-3** Detailed Report Generation
- [ ] **REQ-5-4** Attack Data Curation
- [ ] **REQ-5-5** RAG Knowledge Base Construction
- [ ] **REQ-5-6** Evolutionary Learning Pipeline

## UI/UX Implementation
- [ ] Apply shadcn/ui Dark Theme
- [ ] Implement Dynamic Interactions (Framer Motion/React Bit)
