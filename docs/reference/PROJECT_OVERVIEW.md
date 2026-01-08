# 프로젝트 개요

[← 메인 문서로 돌아가기](../README.md)

---

## 목차

1. [프로젝트명](#프로젝트명)
2. [목표](#목표)
3. [핵심 차별점](#핵심-차별점)
4. [핵심 기능](#핵심-기능)
5. [MVP 범위](#mvp-범위)
6. [제품 요구사항](#제품-요구사항)
7. [라이선스](#라이선스)

---

## 프로젝트명

**EAZY** - AI-Powered Dynamic Application Security Testing Tool

---

## 목표

단순한 웹 스캐너를 넘어 **LLM(ChatGPT, Gemini, Claude)**을 활용하여 웹 애플리케이션의 **비즈니스 로직과 흐름을 심층 분석**하는 지능형 DAST 도구 개발

---

## 핵심 차별점

### 비즈니스 로직 취약점(Business Logic Vulnerabilities) 탐지

기존 DAST 도구가 발견하기 어려운 논리적 허점을 식별합니다.

- 인증 우회 (Authentication Bypass)
- 권한 상승 (Privilege Escalation)
- 비즈니스 프로세스 악용 (Business Process Abuse)
- 불충분한 검증 로직 (Insufficient Validation)

### 연쇄 공격(Chained Attacks) 가능성 탐지

다단계 공격 시나리오를 LLM이 자동으로 생성하고 검증합니다.

- Step 1: 정보 수집 → Step 2: 권한 획득 → Step 3: 핵심 기능 악용
- 각 단계별 성공/실패 확률 분석
- 공격 경로 시각화

### React Flow 기반 비즈니스 로직 맵 시각화

웹 애플리케이션의 페이지 흐름과 비즈니스 로직을 그래프로 표현합니다.

- 노드: 페이지, API 엔드포인트, Form
- 엣지: 사용자 액션, API 호출, 리다이렉트
- 취약점 위치 강조 표시

---

## 핵심 기능

EAZY는 5대 모듈로 구성됩니다.

### 1. 프로젝트 및 타겟 관리

**목적**: 진단 대상을 그룹화하고 LLM 설정을 관리합니다.

**기능**:
- 프로젝트 CRUD (Create, Read, Update, Delete)
- Archive/Restore (Soft Delete 패턴)
- Target CRUD (URL, Scope 설정)
- 일괄 작업 (Bulk Operations)

**컴포넌트**:
- 프로젝트 생성/수정/삭제 폼
- Archive/Restore 다이얼로그
- Target 관리 테이블
- 스캔 트리거 버튼

**상세 정보**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

### 2. 공격 표면 식별 (Attack Surface Discovery)

**목적**: 웹 애플리케이션의 모든 진입점(URL, Form, API)을 자동으로 식별합니다.

#### 2.1. Active Scan (액티브 스캔)

**방식**: Playwright 기반 패턴 크롤링

- Chromium 브라우저로 JavaScript 렌더링
- `<a>` 태그, `<form>` 태그 추출
- XHR/Fetch 요청 감지
- 동적 콘텐츠 대응

**특징**:
- 자동화된 탐색
- Scope 범위 제어 (DOMAIN/SUBDOMAIN/URL_ONLY)
- Depth 제한 설정 가능

#### 2.2. Passive Scan (패시브 스캔)

**방식**: Mitmproxy 기반 사용자 주도 패시브 스캔

- 사용자 브라우저 트래픽을 프록시로 감청
- HTTP/HTTPS 요청/응답 전체 패킷 기록
- WebSocket 통신 추적

**특징**:
- 사용자가 직접 탐색한 경로만 기록
- 인증이 필요한 페이지 접근 가능
- 실제 사용자 시나리오 기반

**상세 정보**: [ARCHITECTURE.md](ARCHITECTURE.md#비동기-처리-패턴)

---

### 3. AI 기반 취약점 분석

**목적**: 기능 흐름(Flow)을 LLM에 주입하여 논리적 허점을 도출합니다.

**분석 프로세스**:
1. 공격 표면 데이터를 LLM 프롬프트로 변환
2. 비즈니스 로직 맵 생성 (React Flow)
3. LLM이 잠재적 취약점 시나리오 생성
4. 위험도 평가 (High/Medium/Low)

**지원 LLM**:
- OpenAI GPT-4
- Google Gemini
- Anthropic Claude

**결과물**:
- 취약점 목록 (CVE 매핑)
- 공격 시나리오 (Step-by-Step)
- 권장 조치사항 (Remediation)

> **Note**: 이 모듈은 MVP 이후 단계에서 구현됩니다.

---

### 4. 공격 수행 (Attack Execution)

**목적**: 시나리오 기반 다단계 공격을 실제로 검증합니다.

**기능**:
- LLM이 생성한 공격 시나리오 자동 실행
- Playwright를 활용한 브라우저 자동화
- 각 Step별 성공/실패 결과 기록
- 거짓 양성(False Positive) 필터링

**안전 장치**:
- Sandbox 환경 권장
- Rate Limiting (서버 부하 방지)
- 사용자 승인 필수 (자동 실행 금지)

> **Note**: 이 모듈은 MVP 이후 단계에서 구현됩니다.

---

### 5. 결과 시각화

**목적**: React Flow를 활용한 공격 경로 시각화

**기능**:
- 비즈니스 로직 맵 (Interactive Graph)
- 취약점 위치 강조 (노드 색상 변경)
- 공격 경로 애니메이션
- 필터링 (취약점 등급별, 타입별)

**기술 스택**:
- React Flow (노드 기반 그래프)
- D3.js (데이터 시각화)
- TailwindCSS (스타일링)

> **Note**: MVP에서는 Asset 테이블 형식으로 표시하며, React Flow는 Phase 5에서 구현됩니다.

**상세 정보**: [TECH_STACK.md](TECH_STACK.md#frontend)

---

## MVP 범위

현재 MVP는 **프로젝트 관리**와 **공격 표면 식별** 기능에 집중합니다.

### MVP 포함 기능

**Phase 1-4 완료**:
- ✅ Backend 인프라 구축 (FastAPI, PostgreSQL, Redis)
- ✅ 프로젝트 CRUD API
- ✅ Target 관리 API
- ✅ 비동기 크롤링 엔진 (Playwright)
- ✅ Asset 중복 제거 및 저장
- ✅ Task Queue & Worker
- ✅ Frontend 프로젝트 관리 UI (168개 테스트 통과)
- ✅ Target 관리 UI + 스캔 트리거

**Phase 5 진행 중**:
- 🔄 Asset 결과 조회 API
- 🔄 대시보드 & Asset 테이블 시각화

### MVP 제외 기능 (추후 개발)

- LLM 기반 취약점 분석 (Phase 6)
- 공격 시나리오 자동 실행 (Phase 7)
- React Flow 비즈니스 로직 맵 (Phase 8)
- Passive Scan (Mitmproxy 연동) (Phase 9)

**상세 정보**: [../plans/frontend/INDEX.md](../plans/frontend/INDEX.md)

---

## 제품 요구사항

### 기능 요구사항 (Functional Requirements)

#### 프로젝트 및 타겟 관리 (Project & Target Management)

| REQ-ID | 기능명 | 설명 | 비고 |
| :--- | :--- | :--- | :--- |
| **REQ-PM-01** | 프로젝트 생성 | 이름, 설명, 진단 정책(Policy)을 포함한 프로젝트를 생성한다. | |
| **REQ-PM-02** | 프로젝트 목록 조회 | 생성된 프로젝트 목록과 기본 정보를 조회한다. | Paging 적용 |
| **REQ-PM-03** | 타겟 등록 | 프로젝트 내에 진단 대상 URL(Scope)을 등록한다. | 단일/다수 URL 지원 |
| **REQ-PM-04** | 타겟 수정/삭제 | 등록된 타겟 정보를 수정하거나 삭제한다. | |

#### 공격 표면 식별 (Attack Surface Discovery)

스캔 방식은 두 가지(Active, Passive)로 나뉘며, 결과는 동일한 형식(Asset)으로 저장되어 통합 관리되어야 합니다.

| REQ-ID | 기능명 | 설명 | 비고 |
| :--- | :--- | :--- | :--- |
| **REQ-ASD-01** | 액티브 스캔 (Active Scan) | Playwright를 이용해 HTML/JS를 재귀적으로 탐색/파싱하여 공격 표면을 수집한다. | 자동화된 크롤링 |
| **REQ-ASD-02** | 패시브 스캔 (Passive Scan) | proxy(Mitmproxy)를 통해 사용자 브라우저 트래픽을 감청하여 공격 표면을 수집한다. | 사용자 주도 탐색 |
| **REQ-ASD-03** | 작업 상태 조회 | 실행 중인 스캔 작업의 상태(Pending, Running, Completed)를 조회한다. | |
| **REQ-ASD-04** | 공격 표면 추출 및 정규화 | HTML, JS, Network 트래픽에서 URL, Form, API를 식별하고 공통 포맷으로 파싱한다. | **출처(Source) 기록 필수** (HTML/JS/Network) |
| **REQ-ASD-05** | 중복 제거 및 저장 (Total View) | 동일한 타겟 내에서 식별된 자산은 중복을 제거하여 저장한다. (Upsert) | Method + URL + Params 기준 |
| **REQ-ASD-06** | 패킷 데이터 저장 | 식별된 자산의 요청(Request) 및 응답(Response) 전체 패킷 데이터를 저장한다. | Headers, Body 포함 |
| **REQ-ASD-07** | 스캔 이력 관리 | 각 스캔(Task) 별로 발견된 자산 목록을 개별적으로 조회할 수 있어야 한다. | Total View와 별개 |
| **REQ-ASD-08** | 파라미터 상세 분석 | URL Query, Form Body, JSON Body 등에서 파라미터 명과 데이터 타입(Int, Str, Bool 등)을 추론하여 저장한다. **JSON의 경우 중첩된 필드(Dot)와 배열(Index)을 모두 Flattening하여 저장한다.** (예: `user.id[0]`, `user.id[1]`) | Fuzzing 기초 데이터 |
| **REQ-ASD-09** | 페이지 연결 추적 (Flow) | 자산 식별 시, 어떤 페이지나 자산에서 유입되었는지(Initiator/Referer) 관계를 저장한다. | Sitemap/Graph 시각화용 |

**상세 정보**: [db_schema.md](db_schema.md), [api_spec.md](api_spec.md)

---

### 비기능 요구사항 (Non-Functional Requirements)

#### Dual View 제공

"전체 누적 자산(Total)"과 "개별 스캔 결과(History)"를 명확히 구분하여 제공해야 합니다.

- **Total View**: `assets` 테이블 (유니크한 공격 표면의 최신 상태)
- **History View**: `asset_discoveries` 테이블 (각 스캔 작업별 발견 이력)

#### 성능

크롤링 작업은 메인 API 서버의 응답 속도에 영향을 주지 않도록 비동기 큐(Work Queue)에서 처리해야 합니다.

- Redis Queue + Worker Process (ARQ 패턴)
- API 서버와 크롤링 작업 분리
- Worker는 독립 프로세스로 실행

**상세 정보**: [ARCHITECTURE.md](ARCHITECTURE.md#비동기-처리-패턴)

#### 확장성

추후 LLM 분석 모듈 연동을 고려한 DB 스키마 설계를 적용해야 합니다.

- JSONB 필드를 활용한 유연한 데이터 저장
- 파라미터 분석 결과 Flattening
- 페이지 연결 추적 (parent_asset_id)

#### 데이터 무결성

동일한 URL/Form에 대한 중복 저장을 방지하고, 최신 상태를 유지해야 합니다.

- content_hash 기반 중복 제거 (SHA256 of "METHOD:URL")
- UNIQUE INDEX on content_hash
- Upsert 로직 (기존 자산 존재 시 last_seen_at만 업데이트)

**상세 정보**: [db_schema.md](db_schema.md#assets-공격-표면)

---

## 라이선스

**Apache License 2.0**

```
Copyright 2026 EAZY Project

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

**다음 문서**: [TECH_STACK.md](TECH_STACK.md)

[← 메인 문서로 돌아가기](../README.md)
