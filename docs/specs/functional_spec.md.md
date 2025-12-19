# **AI 기반 DAST 도구 기능 명세서 (Functional Specification)**

## **1\. 개요 (Overview)**

본 문서는 Python 3.12(Backend)와 React(Frontend) 기반의 지능형 동적 애플리케이션 보안 테스팅(DAST) 도구 개발을 위한 기능 명세이다.  
웹 애플리케이션의 공격 표면을 자동으로 식별하고, **LLM(ChatGPT, Gemini, Claude)** 을 활용하여 기능의 로직과 흐름을 분석한 뒤, 비즈니스 로직 오류 및 연쇄 공격(Chained Attack) 가능성을 시각적으로 도출하는 것을 목적으로 한다.

## **2\. 시스템 환경 (Environment)**

* **Backend:** Python 3.12.10 (FastAPI), PostgreSQL (JSONB 활용), Redis (Task Queue)  
* **Frontend:** React, Vite, shadcn/ui, React Bit, React Flow (시각화)  
* **AI Engine:** OpenAI API (GPT-4o), Google Gemini API, Anthropic Claude API  
* **Core Modules:** Playwright (Crawling), Mitmproxy (Proxy/Passive Scan), HTTPX (Request)

## **3\. 상세 기능 명세 (Functional Requirements)**

### **3.1. 프로젝트 및 타겟 관리 (Project Management)**

사용자가 진단할 대상을 그룹화하고 관리하는 기능.

| ID | 기능명 | 상세 설명 | 입력 데이터 | 출력/동작 |
| :---- | :---- | :---- | :---- | :---- |
| **REQ-1-1** | **프로젝트 생성** | 진단 단위를 관리하기 위한 프로젝트(컨테이너)를 생성한다. | 프로젝트 명, 설명, 담당자 | Project ID 생성 |
| **REQ-1-2** | **스캔 대상 등록** | 하나의 프로젝트 내에 다수의 스캔 대상(URL)을 등록한다. (1:N 관계) | Project ID, Target URL, 인증 정보(Cookie/Header) | Target ID 생성 |
| **REQ-1-3** | **LLM 설정 관리** | 분석에 사용할 LLM 모델 및 API 키를 설정한다. | API Key, Model Selection (GPT/Gemini/Claude) | 설정 저장 |

### **3.2. 공격 표면 식별 및 파싱 (Attack Surface Discovery)**

애플리케이션의 엔드포인트, 파라미터, 입력 벡터를 수집하고 **의미(Semantics)** 를 파악하는 핵심 엔진.

| ID | 기능명 | 상세 설명 | 기술 요건 |
| :---- | :---- | :---- | :---- |
| **REQ-2-1** | **패턴 기반 크롤링 (Active Crawling)** | 1\. **정적/동적 분석**: HTML 태그 및 JS 실행 후 DOM 변화, AJAX 요청(fetch/XHR) 훅킹. 2\. **Katana 스타일 파싱**: URL 구조 분해 및 파라미터 추출. | Playwright, DOM Parsing |
| **REQ-2-2** | **사용자 주도 프록시 파싱 (Passive Crawling)** | 1\. 내장 브라우저/프록시를 통해 사용자가 직접 웹 서핑. 2\. Mitmproxy로 트래픽(Req/Res)을 실시간 캡처하여 공격 표면 DB에 적재. | Mitmproxy, WebSocket |
| **REQ-2-3** | **기능 흐름 및 의존성 분석 (Logic Flow Analysis)** | 페이지/기능 간의 **선후 관계(Pre-condition)** 와 **데이터 흐름(Data Flow)** 을 추적. 예: '장바구니 담기' \-\> '주문서 작성' \-\> '결제'의 논리적 순서를 식별하여 비즈니스 로직 맵 구성. | Graph Structure, Dependency Parsing |
| **REQ-2-4** | **파라미터 상세 명세화** | 추출된 파라미터의 타입, 필수 여부, 데이터 위치(Query/Body/Header) 등을 JSON 스키마로 구조화. | Type Inference |
| **REQ-2-5** | **LLM 기반 기능 의미 추론 (AI Function Inference)** | 수집된 URL, 파라미터 명(변수명), 주변 텍스트 정보를 LLM에 전달하여 해당 엔드포인트가 수행하는 **기능의 목적(Intent)** 을 자연어로 요약 및 저장. (예: /api/pwd\_reset \-\> "사용자 비밀번호 초기화 기능") | LLM Semantic Analysis |

### **3.3. AI 기반 공격 가능성 식별 (AI Vulnerability Analysis)**

수집된 데이터를 LLM에게 전송하여 비즈니스 로직 및 맥락을 고려한 취약점을 식별하는 단계.

| ID | 기능명 | 상세 설명 | 로직 예시 |
| :---- | :---- | :---- | :---- |
| **REQ-3-1** | **컨텍스트 생성** | 수집된 URL, 파라미터, HTML 스니펫, 파라미터 이름 등을 LLM 프롬프트에 맞게 요약/가공한다. | Prompt Engineering |
| **REQ-3-2** | **LLM 로직 분석 요청** | 선택된 LLM API에 기능 흐름 데이터를 전송하여 **비즈니스 로직의 허점**을 추론. "결제 검증 없이 주문 완료 API 호출 가능성" 등의 시나리오 도출. | **Input:** Flow Data (Cart \-\> Order \-\> Pay) **AI Output:** "Skip 'Pay' step and call 'Order Complete' directly." |
| **REQ-3-3** | **연쇄 공격 벡터 생성** | 단일 취약점이 아닌, 여러 기능을 연계(Chaining)해야 가능한 공격 시나리오와 페이로드를 생성. | Scenario Generation |

### **3.4. 공격 수행 (Attack Execution)**

식별된 취약점 후보군에 실제 페이로드를 전송하여 검증하는 단계.

| ID | 기능명 | 상세 설명 | 기술 요건 |
| :---- | :---- | :---- | :---- |
| **REQ-4-1** | **지능형 공격 스케줄링** | AI가 제안한 중요도(Priority)가 높은 취약점부터 우선적으로 스캔을 수행한다. | Priority Queue |
| **REQ-4-2** | **시나리오 기반 공격 검증** | 단순 페이로드 전송이 아닌, **다단계(Multi-step) 요청**을 수행하여 비즈니스 로직 우회 여부를 검증. (예: A요청 후 획득한 값으로 B요청 시도) | Stateful Fuzzing, Session Management |
| **REQ-4-3** | **거짓 양성(False Positive) 필터링** | 공격 성공으로 판단된 건에 대해 다시 한번 AI에게 검증(Re-check)을 요청하여 오탐율을 낮춤. (옵션) | AI Verification |

### **3.5. 결과 시각화 및 리포팅 (Visualization & Reporting)**

진단 결과를 시각화하고, 성공 데이터를 지식화(Knowledge Base)하여 도구를 진화시키는 기능.

| ID | 기능명 | 상세 설명 | UI/기술 요건 |
| :---- | :---- | :---- | :---- |
| **REQ-5-1** | **비즈니스 로직 시각화 (Strategic View)** | **기능 간의 논리적 연결 관계(Dependency)**와 데이터 흐름을 시각화. 사용자가 직관적으로 비즈니스 로직의 허점을 발견하고, 여러 기능을 연계한 공격 표면을 한눈에 파악할 수 있는 맵 제공. | React Flow, Custom Nodes |
| **REQ-5-2** | **스캔 결과 저장 및 위험도 산정 (Result Logging & CVSS)** | 1\. **로그 저장:** 스캔 중 발생한 모든 요청/응답(성공 및 실패 포함)을 로그로 저장. 2\. **CVSS 3.1 평가:** 공격에 성공한 취약점에 대해 AI/Rule 엔진이 CVSS 3.1 벡터(AV, AC, PR, UI, S, C, I, A)를 추정하고 Base Score(0.0\~10.0)를 산정. | Log Storage (NoSQL/JSONB), CVSS 3.1 Calculator |
| **REQ-5-3** | **상세 리포트** | 취약점의 상세 내용, 성공한 페이로드, HTTP 패킷, **CVSS 점수**, AI의 분석 코멘트, 해결 방안 등을 포함한 리포트 제공. | shadcn/ui Card, Accordion |
| **REQ-5-4** | **공격 데이터 큐레이션 (Curation)** | 사용자가 성공한 공격 로그 중 **'유의미한 케이스'**를 직접 선별(Check/Select)하고 태깅(Tagging)하여 지식 저장소로 보낼 수 있는 기능. | Checkbox, Tag Input |
| **REQ-5-5** | **RAG 지식 베이스 구축 (Scored Knowledge Base)** | 선별된 공격 데이터를 벡터화하여 DB에 저장 시, **가중치 점수(Weight Score)**를 부여함. \- 점수 기준: 사용자 평가(Star), 취약점 파급력(CVSS), 공격 성공 빈도 등. \- 검색 시 고득점 데이터 우선 노출. | Vector DB, Weighted Scoring Algorithm |
| **REQ-5-6** | **지능형 진화 (Evolutionary Learning)** | 새로운 타겟 분석 시, RAG DB에서 **유사한 과거 성공 사례**를 검색(Retrieve)하여 LLM 프롬프트에 포함(Augment). 시간이 지날수록 공격 성공률이 향상되는 선순환 구조 구축. | RAG Pipeline, Context Injection |

## **4\. UI/UX 가이드라인 (Frontend)**

* **테마:** shadcn/ui의 Dark 테마를 기본으로 하여 사이버보안 도구의 전문적인 느낌 강조.  
* **동적 인터랙션 (Dynamic Interaction):**  
  * **React Bit** 또는 **Framer Motion**과 같은 애니메이션 라이브러리를 적극 활용하여 정적인 대시보드가 아닌, **살아있는 듯한(Alive) 동적 UI** 구현.  
  * 스캔 진행 상태(Progress), 공격 패킷 전송, 취약점 발견 알림 등에 **마이크로 인터랙션(Micro-interactions)**을 적용하여 사용자 몰입감 극대화.  
  * 페이지 전환 시 부드러운 트랜지션 및 데이터 로딩 시 스켈레톤 UI와 미려한 로딩 애니메이션 제공.  
* **비즈니스 로직 맵 (React Flow):**  
  * **Node:** 단순 URL이 아닌 **'기능 단위(Function Unit)'** (예: 회원가입, 결제, 게시글 작성).  
    * *Tip:* REQ-2-5에서 분석한 '기능 의미'를 노드 라벨로 사용 (예: "비밀번호 변경").  
  * **Edge:** 논리적 흐름 및 데이터 전달 경로 (Solid: 정상 흐름, Dashed: 우회 가능 경로).  
  * **Features:**  
    * 노드를 드래그하여 가상의 공격 경로를 그려볼 수 있는 시뮬레이션 모드 지원.  
    * AI가 분석한 'Logic Gap'(예: 인증 누락 구간)을 하이라이팅.