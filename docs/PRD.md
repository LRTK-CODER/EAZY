# Product Requirements Document (PRD) - MVP

## 1. 프로젝트 개요 (Overview)
**EAZY**는 AI 기반의 지능형 DAST 도구입니다. 이번 MVP 단계에서는 기본적인 **프로젝트 관리** 기능과, 보안 진단의 기초가 되는 **공격 표면 식별(Attack Surface Identification)** 기능을 API 서버로 구현하는 것을 목표로 합니다.

## 2. 목표 (Goals)
*   사용자가 진단 대상(Target)을 등록하고 관리할 수 있어야 한다.
*   등록된 대상에 대해 크롤링(Crawling)을 수행하여 공격 표면(URL, Form, API Endpoint)을 식별할 수 있어야 한다.
*   식별된 데이터는 구조화된 형태로 데이터베이스에 저장되어 추후 취약점 분석에 활용될 수 있어야 한다.

## 3. 핵심 기능 요구사항 (Functional Requirements)

### 3.1. 프로젝트 및 타겟 관리 (Project & Target Management)
| REQ-ID | 기능명 | 설명 | 비고 |
| :--- | :--- | :--- | :--- |
| **REQ-PM-01** | 프로젝트 생성 | 이름, 설명, 진단 정책(Policy)을 포함한 프로젝트를 생성한다. | |
| **REQ-PM-02** | 프로젝트 목록 조회 | 생성된 프로젝트 목록과 기본 정보를 조회한다. | Paging 적용 |
| **REQ-PM-03** | 타겟 등록 | 프로젝트 내에 진단 대상 URL(Scope)을 등록한다. | 단일/다수 URL 지원 |
| **REQ-PM-04** | 타겟 수정/삭제 | 등록된 타겟 정보를 수정하거나 삭제한다. | |

### 3.2. 공격 표면 식별 (Attack Surface Discovery)
**스캔 방식은 두 가지(Active, Passive)로 나뉘며, 결과는 동일한 형식(Asset)으로 저장되어 통합 관리되어야 한다.**

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

## 4. 비기능 요구사항 (Non-Functional Requirements)
*   **Dual View 제공**: "전체 누적 자산(Total)"과 "개별 스캔 결과(History)"를 명확히 구분하여 제공해야 한다.
*   **성능**: 크롤링 작업은 메인 API 서버의 응답 속도에 영향을 주지 않도록 비동기 큐(Work Queue)에서 처리해야 한다.
*   **확장성**: 추후 LLM 분석 모듈 연동을 고려한 DB 스키마 설계를 적용해야 한다.
*   **데이터 무결성**: 동일한 URL/Form에 대한 중복 저장을 방지하고, 최신 상태를 유지해야 한다.

## 5. 데이터 요구사항 (Data Requirements) (See `db_schema.md`)
*   Projects, Targets, Tasks, Assets(Attack Surface) 테이블 필요.
*   JSONB 필드를 활용하여 다양한 형태의 공격 표면(Form Data, Headers 등)을 유연하게 저장.
