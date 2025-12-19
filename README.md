# EAZY: AI-Powered DAST Tool

## 1. 개요 (Overview)

**EAZY**는 Python 3.12(Backend)와 React(Frontend)를 기반으로 하는 **지능형 동적 애플리케이션 보안 테스팅(DAST)** 도구입니다.
단순한 웹 스캐너를 넘어, **LLM(ChatGPT, Gemini, Claude)**을 활용하여 웹 애플리케이션의 비즈니스 로직과 흐름을 심층 분석합니다. 이를 통해 기존 도구가 탐지하기 어려운 **비즈니스 로직 오류(Business Logic Vulnerabilities)** 및 **연쇄 공격(Chained Attacks)** 가능성을 식별하고 시각적으로 제공하는 것을 목표로 합니다.

## 2. 주요 기능 (Key Features)

*   **프로젝트 및 타겟 관리:** 진단 대상 그룹화 및 관리, LLM 설정.
*   **공격 표면 식별 (Attack Surface Discovery):** Playwright 기반의 패턴 크롤링 및 Mitmproxy 기반의 사용자 주도 패시브 스캔.
*   **AI 기반 취약점 분석 (AI Vulnerability Analysis):** 기능 흐름(Flow)을 LLM에 주입하여 논리적 허점 및 연쇄 공격 시나리오 도출.
*   **공격 수행 (Attack Execution):** 시나리오 기반의 다단계(Multi-step) 공격 검증 및 오탐(False Positive) 필터링.
*   **결과 시각화 (Visualization):** React Flow를 활용한 비즈니스 로직 및 공격 경로 시각화 (Business Logic Map).

## 3. 시스템 구성 (System Environment)

*   **Backend:**
    *   Python 3.12.10
    *   FastAPI (Web Framework)
    *   PostgreSQL (JSONB supported)
    *   Redis (Task Queue)
*   **Frontend:**
    *   React, Vite
    *   shadcn/ui (UI Components)
    *   React Flow (Visualization)
    *   React Bit / Framer Motion (Animations)
*   **AI Engine:** OpenAI (GPT-4o), Google Gemini, Anthropic Claude
*   **Core Modules:** Playwright, Mitmproxy, HTTPX

## 4. 프로젝트 구조 (Project Structure)

```
EAZY/
├── backend/            # FastAPI Backend Application
│   ├── app/
│   │   ├── api/        # API Endpoints
│   │   ├── core/       # Core Configurations
│   │   ├── models/     # Database Models
│   │   ├── services/   # Business Logic
│   │   └── engine/     # Crawling & Attack Engines
│   └── tests/          # Pytest Suites
├── frontend/           # React Frontend Application
│   ├── src/
│   │   ├── components/ # Reusable UI Components
│   │   ├── pages/      # Page Components
│   │   ├── lib/        # Utilities
│   │   └── store/      # State Management (Zustand)
│   └── public/
├── docs/               # Project Documentation
│   └── specs/          # Functional Specs, API Specs, etc.
└── README.md           # Project Overview (This file)
```
