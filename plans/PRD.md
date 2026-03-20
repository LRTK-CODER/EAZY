## 개요

**한 줄 설명:** 웹 애플리케이션의 API 흐름·데이터 플로·비즈니스 로직을 Knowledge Graph로 구조화하고, 발견된 취약점들을 자동으로 연계하여 시나리오 기반 공격 체인을 구성·실행하는 LLM 기반 모의해킹 에이전트

**문제:** 현재 웹 모의해킹은 수동 작업에 의존한다. 보안 전문가가 개별 취약점을 하나씩 발견하고, 머릿속에서 "이 SQLi로 크레덴셜을 뽑고, 그걸로 OTP를 우회하고, 관리자 세션을 탈취하면..."이라는 공격 체인을 구상한다. 이 과정이 수일~수주 소요되며, 전문가의 경험과 직관에 전적으로 의존한다. 기존 자동화 도구(sqlmap, Nuclei)는 단일 취약점 탐지에 특화되어 있어 취약점 간 연계(체이닝)를 수행하지 못한다. 더 근본적으로, 기존 도구는 엔드포인트를 플랫한 리스트로만 나열할 뿐, "이 API가 저 API를 호출한다", "사용자 입력이 여기서 들어가서 저기서 나온다"는 관계를 이해하지 못한다. 이 때문에 비즈니스 로직 취약점(가격 변조, 결제 단계 건너뛰기, 레이스 컨디션 등)은 자동 탐지가 불가능했다.

**타겟 사용자:**

- **주요 사용자:** 웹 애플리케이션 모의해킹을 수행하는 보안 전문가 (OSCP/OSCE 수준)
- **기술 수준:** Burp Suite, sqlmap 등 보안 도구에 익숙하며, HTTP 프로토콜과 웹 취약점(OWASP Top 10)을 이해하는 실무자
- **고충점:** 취약점 체이닝은 경험과 시간이 필요한 고급 작업이며, 수동으로 하면 누락되는 경로가 많다
- **사용 환경:** CLI 우선, 웹 대시보드는 선택적

**성공 지표:**

- 단일 취약점 탐지를 넘어 2개 이상의 취약점을 연계한 공격 체인 시나리오 자동 생성
- CVSS 단독 점수 vs 체인 점수의 차이를 정량적으로 산출
- 보안 전문가가 수동으로 수행하는 체이닝 분석 시간 대비 70% 이상 단축
- Knowledge Graph 기반으로 API 흐름, 데이터 플로, 비즈니스 프로세스를 자동 구조화
- 비즈니스 로직 취약점(가격 변조, 단계 건너뛰기, 레이스 컨디션 등) 가설 자동 생성

---

## 기술 제약

### 스택

- **언어:** Python 3.11+
- **에이전트 프레임워크:** LangChain + LangGraph (StateGraph 기반 파이프라인)
- **LLM 추상화:** LiteLLM (Claude, GPT, Gemini, Ollama, vLLM 등 모든 프로바이더 지원)
- **백엔드 API:** FastAPI + uvicorn
- **프론트엔드:** React + TypeScript
- **실시간 통신:** WebSocket
- **HTTP 클라이언트:** httpx (async)
- **헤드리스 브라우저:** Playwright
- **Knowledge Graph:** NetworkX (Python 인메모리 그래프 · 경로 탐색 알고리즘 내장 · JSON 직렬화)
- **벡터 DB:** ChromaDB
- **암복호화:** pycryptodome
- **데이터 검증:** Pydantic
- **CLI:** rich
- **테스트:** pytest + pytest-asyncio

### 사용 금지

- Deep Agents (deepagents) — 신규 출시, 브레이킹 체인지 위험, 추상화 과잉
- LangSmith — SaaS 특성상 모의해킹 데이터(크레덴셜, 취약점 증거)가 외부로 유출되므로, 프로덕션 환경에서 사용 금지. 개발 환경에서 테스트 데이터로만 선택적 사용 가능
- requests 라이브러리 — httpx 사용 (async 필수)
- SQLite/PostgreSQL — 세션 데이터는 파일 기반(JSON/YAML)으로 관리

---

## 커맨드

- 개발 서버: `uvicorn src.backend.app:app --reload`
- CLI 실행: `python cli.py --workspace {session_id}`
- 테스트: `pytest tests/ -v`
- 린트: `ruff check src/`
- 타입 체크: `mypy src/`

---

## 데이터 모델

### Knowledge Graph (Stage 1 핵심 출력)

플랫한 엔드포인트 리스트가 아닌, API 간 관계·데이터 흐름·비즈니스 프로세스를 그래프로 구조화한다. Stage 2 플래너가 이 그래프를 탐색하여 공격 경로를 발견한다.

```yaml
KnowledgeGraph:
  nodes: list[GraphNode]
  edges: list[GraphEdge]
  business_flows: list[BusinessFlow]
  metadata: GraphMetadata

GraphNode:
  id: string (고유 식별자)
  type: enum [endpoint, data_object, auth_level, business_process]
  properties: dict
  # type별 properties 예시:
  #   endpoint: { url, method, parameters, auth_required, content_type }
  #   data_object: { name, fields, sensitive }    # 예: User, Order, Payment
  #   auth_level: { role, permissions }            # 예: guest, user, admin
  #   business_process: { name, description }      # 예: 결제, 회원가입

GraphEdge:
  source: string (node id)
  target: string (node id)
  type: enum [calls, sends_data, requires_auth, depends_on, validates, creates, reads, updates, deletes]
  properties: dict
  # type별 properties 예시:
  #   calls: { sequence_order }                    # API A가 API B를 호출
  #   sends_data: { param_name, data_type }        # 파라미터가 A에서 B로 전달
  #   requires_auth: { min_role }                  # 이 엔드포인트는 특정 권한 필요
  #   depends_on: { condition }                    # 이 단계는 이전 완료 후 가능
  #   validates: { validation_type }               # 이 엔드포인트가 해당 데이터를 검증

BusinessFlow:
  name: string (예: "결제 프로세스")
  type: enum [payment, auth, registration, data_management, privilege, reward]
  steps: list[FlowStep]
  critical_data_paths: list[DataPath]     # 민감 데이터가 흘러가는 경로

FlowStep:
  order: int
  node_id: string (GraphNode 참조)
  description: string
  depends_on_previous: bool

DataPath:
  param_name: string (예: "price", "amount")
  source_node: string (데이터 생성 지점)
  intermediate_nodes: list[string] (경유 지점)
  sink_node: string (데이터 최종 사용 지점)
  manipulation_risk: enum [price_tampering, step_bypass, duplicate_use, race_condition, idor, privilege_escalation]

GraphMetadata:
  target_url: string
  auth_flow: AuthFlow
  waf_profile: WafProfile | null
  tech_stack: list[Technology]
  crypto_context: CryptoContext | null
  total_nodes: int
  total_edges: int
```

### 공격 표면 요약 (Knowledge Graph에서 파생)

```yaml
AttackSurface:
  target_url: string (필수)
  endpoints: list[Endpoint]           # KG의 endpoint 노드에서 추출
  auth_flow: AuthFlow
  waf_profile: WafProfile | null
  tech_stack: list[Technology]
  crypto_context: CryptoContext | null

Endpoint:
  url: string (필수)
  method: enum [GET, POST, PUT, DELETE, PATCH]
  parameters: list[Parameter]
  auth_required: bool
  content_type: string

Parameter:
  name: string (필수)
  location: enum [query, body, header, cookie, path]
  type: string
  sample_value: string | null

CryptoContext:
  detected: bool
  algorithm: string (예: AES-CBC)
  key: string
  iv: string
  padding: string
  encryption_scope: enum [full_body, partial]
  encrypted_endpoints: list[string]
```

### 공격 체인 (Stage 2 출력)

```yaml
AttackChain:
  id: UUID (자동 생성)
  name: string (예: "SQLi→OTP우회→관리자탈취")
  steps: list[ChainStep]
  estimated_success_rate: float
  estimated_impact: float

ChainStep:
  order: int
  vulnerability_type: string (CWE 코드)
  target_endpoint: string
  preconditions: list[string]
  postconditions: list[string]
  skill_ref: string (Skill 파일명)
```

### 취약점 발견 (Stage 3 출력)

```yaml
Finding:
  id: UUID (자동 생성)
  chain_id: UUID (소속 체인)
  step_order: int
  vulnerability_type: string
  endpoint: string
  evidence: list[Evidence]
  success: bool
  cvss_standalone: float
  cvss_chained: float | null

Evidence:
  type: enum [http_request, http_response, screenshot, data_sample]
  content: string
  timestamp: datetime
  sensitive_data_masked: bool (기본 true)
```

### 세션 설정

```yaml
SessionConfig:
  session_name: string (필수)
  created: datetime (자동)
  target_url: string (필수)
  scope: list[string] (와일드카드 지원)
  exclude: list[string]
  tool_enabled: bool (기본 false)
  auto_approve_low: bool (기본 true)
  max_retries: int (기본 3)
  reflexion_memory_size: int (기본 3)
  llm_model: string (기본 전역 설정 상속)
  llm_temperature: float (기본 0.1)
```

---

## 기능

### 기능 1: 자동 정찰 + Knowledge Graph 구축 (Stage 1) — 우선순위 P0

**유저 스토리:** 보안 전문가로서, 타겟 URL을 입력하면 공격 표면이 자동으로 매핑되고, API 간 관계·데이터 흐름·비즈니스 로직이 Knowledge Graph로 구조화되길 원한다. 엔드포인트 리스트만으로는 보이지 않는 데이터 플로와 비즈니스 로직 취약점을 발견하기 위해.

**트리거:** 사용자가 CLI에서 타겟 URL과 크레덴셜을 입력하여 세션 시작

**동작:**

1. 인증 흐름 자동 매핑 (로그인 → OTP → 세션 발급 등 단계 식별)
2. 6개 카테고리 스캐너 병렬 실행 (JS 분석, OSINT, 디렉토리, WAF 지문, 기술 스택, 에러 패턴)
3. LLM이 스캐너 결과를 종합 해석 (1회 호출)
4. 인증된 상태로 웹 앱 내부 크롤링
5. 암호화된 파라미터 탐지 시 JS에서 키/IV/알고리즘 자동 추출
6. **Knowledge Graph 구축:**
    - 크롤링 중 발견된 API 호출 관계를 엣지로 기록 (A가 B를 호출 → `calls` 엣지)
    - 파라미터가 어디서 생성되어 어디로 전달되는지 데이터 플로 추적 (`sends_data` 엣지)
    - 각 엔드포인트의 인증 요구사항 매핑 (`requires_auth` 엣지)
    - LLM이 비즈니스 프로세스를 식별하고 단계 간 의존성 구조화 (결제 흐름, 회원가입 등)
    - 민감 데이터(가격, 수량, 사용자 ID)가 흘러가는 경로(DataPath) 추출

**사용자 화면:** CLI에 정찰 진행 상태 표시, 완료 시 Knowledge Graph 요약 출력 (노드 수, 엣지 수, 식별된 비즈니스 흐름, 민감 데이터 경로)

**수락 기준:**

- Given 유효한 타겟 URL과 크레덴셜, When 정찰 시작, Then Knowledge Graph(JSON)가 워크스페이스에 저장됨
- Given WAF가 존재하는 타겟, When 정찰 완료, Then WAF 벤더와 규칙셋이 식별됨
- Given 클라이언트 사이드 암호화가 적용된 타겟, When JS 분석 완료, Then crypto_context에 알고리즘/키/IV/대상 엔드포인트가 추출됨
- Given 스캐너 플러그인이 미등록, When 해당 카테고리 스캔, Then 에러 없이 건너뛰고 나머지 카테고리는 정상 실행
- Given 결제 기능이 있는 웹 앱, When KG 구축 완료, Then 결제 프로세스의 API 호출 순서와 price 데이터 경로가 그래프에 포함됨
- Given 다수의 API 엔드포인트, When KG 구축 완료, Then API 간 호출 관계(`calls`), 데이터 전달(`sends_data`), 인증 요구(`requires_auth`) 엣지가 생성됨

### 기능 2: Knowledge Graph 기반 공격 경로 계획 (Stage 2) — 우선순위 P0

**유저 스토리:** 보안 전문가로서, Knowledge Graph를 탐색하여 가능한 모든 공격 경로(기술적 취약점 + 비즈니스 로직 취약점)가 자동 발견되길 원한다. 플랫 리스트에서는 보이지 않는 데이터 플로 기반 공격 경로를 찾기 위해.

**트리거:** Stage 1 정찰 + Knowledge Graph 구축 완료

**동작:**

1. **그래프 탐색으로 공격 경로 발견:**
    - Knowledge Graph에서 진입점(guest 접근 가능 엔드포인트)부터 목표(admin API, 민감 데이터)까지의 경로 탐색
    - `calls` + `sends_data` 엣지를 따라가며 데이터가 흘러가는 체인 발견
    - `requires_auth` 엣지에서 권한 상승 필요 지점 식별
2. **기술적 취약점 가설 생성:** 파라미터를 CWE 유형에 매핑
3. **비즈니스 로직 취약점 가설 생성:**
    - DataPath 분석: 민감 데이터(가격, 수량)가 흘러가는 경로에서 변조 가능 지점 식별
    - 의존성 분석: `depends_on` 엣지에서 단계 건너뛰기 가능성 판단
    - 권한 분석: user 세션으로 admin 전용 노드에 접근 가능한 경로 탐색
4. **기술적 + 비즈니스 로직 복합 체인 생성:** 예) SQLi로 크레덴셜 탈취 → 관리자 로그인 → 가격 변조 API 접근
5. 성공률 × 영향도 기준으로 시나리오 우선순위 결정
6. Skill의 체이닝 레시피 + RAG의 최신 CVE/과거 보고서 참조

**사용자 화면:** CLI에 생성된 공격 체인 목록 표시 (순위, 예상 영향도, 단계 수, 유형: 기술적/비즈니스 로직/복합)

**수락 기준:**

- Given Knowledge Graph 존재, When 계획 실행, Then 최소 1개 이상의 공격 체인 시나리오 생성
- Given Knowledge Graph에 `calls` 엣지 존재, When 경로 탐색, Then API 호출 체인이 시나리오에 반영됨
- Given Knowledge Graph에 `sends_data` 엣지 + price 데이터 경로 존재, When 가설 생성, Then 가격 변조 가설이 포함됨
- Given Knowledge Graph에 admin 권한 노드 존재, When 경로 탐색, Then guest/user → admin 도달 경로가 식별됨
- Given RAG에 타겟 기술 스택 관련 최신 CVE 존재, When 가설 생성, Then 해당 CVE가 가설에 포함됨
- Given 결제 흐름의 `depends_on` 엣지 존재, When 계획 실행, Then 단계 건너뛰기 가설이 포함됨

### 기능 3: 익스플로잇 실행 (Stage 3) — 우선순위 P0

**유저 스토리:** 보안 전문가로서, 계획된 공격 체인이 실제로 동작하는지 자동으로 검증되길 원한다. 다만 모든 공격 실행 전에 내 승인이 필요하다.

**트리거:** 사용자가 공격 체인 시나리오를 선택하여 실행 명령

**동작:**

1. L1 통제: 각 단계별 페이로드와 영향도(H/M/L)를 사용자에게 표시, 승인 대기
2. L2 실행: 승인된 페이로드 전송 (경로 A: 커스텀 페이로드 / 경로 B: 도구 — 사용자 선택)
3. L3 검증: 결정론적 규칙으로 성공/실패 판정 (LLM 미사용)
4. L4 적응: 실패 시 전술적 재시도(3회) → 전략적 벡터 전환 → Reflexion 성찰
5. 체인의 모든 단계에 대해 L1→L2→L3→L4 사이클 반복
6. 비즈니스 로직 테스트: 비즈니스 흐름의 여러 단계를 순서대로 진행하면서 중간에 파라미터 변조 (가격 변경, 단계 건너뛰기, 동시 요청 등)

**사용자 화면:** CLI에서 승인 프롬프트 (y/n/수정), 각 단계 성공/실패 실시간 표시

**수락 기준:**

- Given High 영향도 페이로드, When 실행 시도, Then 반드시 사용자 수동 승인 후 실행
- Given Low 영향도 + auto_approve_low=true, When 실행 시도, Then 자동 승인 후 실행
- Given SQLi 페이로드 전송, When 응답에 DB 데이터 포함, Then L3 검증기가 success=true 판정
- Given WAF가 페이로드 차단, When L4 적응 작동, Then 인코딩 변경 후 재시도
- Given 3회 전술 재시도 모두 실패, When OR 분해, Then 공격 벡터 전환 (에러→블라인드→타임 기반)
- Given 도구 사용 비활성화(tool_enabled=false), When 실행, Then 경로 A(커스텀)만으로 동작
- Given 암호화된 엔드포인트, When 페이로드 생성, Then Skill의 encrypt()로 바디 전체 암호화 후 전송
- Given 결제 흐름의 가격 파라미터, When price=-100으로 변조 후 결제 진행, Then 서버 응답에서 음수 결제 허용 여부 확인
- Given 다단계 프로세스, When 중간 단계를 건너뛰고 최종 API 직접 호출, Then 단계 우회 가능 여부 확인

### 기능 4: 분석 + 리포트 (Stage 4) — 우선순위 P1

**유저 스토리:** 보안 전문가로서, 발견된 취약점과 공격 체인의 영향도가 정량적으로 분석된 리포트를 자동으로 받고 싶다. 고객사에 제출할 보고서 작성 시간을 줄이기 위해.

**트리거:** Stage 3 익스플로잇 완료

**동작:**

1. 개별 취약점 CVSS 산정
2. 체인 전체의 CVSS 산정 (단독 vs 체인 비교)
3. 비즈니스 영향 분석 (데이터 규모, 규정 위반 여부)
4. 리포트 생성 (체인 경로 + HTTP PoC + 대응방안)

**사용자 화면:** 워크스페이스에 report.md 생성, CLI에 요약 출력

**수락 기준:**

- Given 성공한 체인 존재, When 분석 실행, Then CVSS 단독 점수와 체인 점수가 모두 산출됨
- Given 민감 데이터 유출 확인, When 리포트 생성, Then 실제 값은 마스킹되어 포함됨
- Given 리포트 생성 완료, When 리포트 확인, Then HTTP 요청/응답 PoC가 각 단계별로 포함됨

### 기능 5: 세션 관리 (워크스페이스) — 우선순위 P0

**유저 스토리:** 보안 전문가로서, 고객사별로 독립된 세션을 관리하고, 중단된 테스트를 이어서 진행하고 싶다.

**트리거:** CLI에서 새 세션 생성 또는 기존 세션 재개 명령

**동작:**

1. 랜덤 ID로 워크스페이스 디렉토리 생성
2. config.yaml에 타겟/설정/LLM 모델 저장
3. 각 Stage 결과를 워크스페이스 하위 디렉토리에 저장
4. 모든 HTTP 요청/응답을 history.jsonl에 append-only 기록
5. 승인/거부 이력을 audit.jsonl에 기록

**사용자 화면:** CLI에서 세션 목록 조회, 세션 전환, 세션 삭제

**수락 기준:**

- Given 새 세션 생성, When 타겟 URL 입력, Then 랜덤 ID 디렉토리 + config.yaml 생성됨
- Given 진행 중인 세션 종료 후 재시작, When 세션 재개, Then chain_progress.json 기반으로 마지막 단계부터 이어서 진행 (Knowledge Graph도 재로드)
- Given 세션 A와 세션 B 동시 존재, When 세션 A 실행, Then 세션 B의 데이터에 영향 없음 (Knowledge Graph 포함)
- Given 세션 삭제 명령, When 실행, Then 해당 워크스페이스 디렉토리 전체 삭제

### 기능 6: 웹 대시보드 — 우선순위 P2

**유저 스토리:** 보안 전문가로서, 에이전트의 실행 상태를 실시간으로 모니터링하고, 승인/거부를 웹 UI에서 하고 싶다.

**트리거:** 대시보드 서버 시작 후 브라우저 접속

**동작:**

1. WebSocket으로 코어 엔진과 실시간 연결
2. 7개 패널 표시: 세션 모니터링, HTTP 히스토리, 공격 진행 현황, 승인 게이트 UI, Skill/RAG 상태, Reflexion 로그, 리포트 미리보기
3. 승인/거부/설정 변경을 대시보드에서 코어로 전송

**사용자 화면:** 7개 패널이 포함된 웹 대시보드

**수락 기준:**

- Given 코어 엔진 실행 중, When 대시보드 접속, Then 현재 Stage/Layer/체인 단계 실시간 표시
- Given 대시보드 프로세스 종료, When 코어 엔진 확인, Then 코어는 중단 없이 계속 실행
- Given L1 승인 대기 중, When 대시보드에서 승인 클릭, Then 코어가 해당 단계 실행 진행

### 기능 7: 스캐너 플러그인 관리 — 우선순위 P1

**유저 스토리:** 보안 전문가로서, 새로운 스캐닝 도구를 코어 코드 수정 없이 플러그인으로 추가하고 싶다.

**트리거:** 새 플러그인 파일 생성 + registry.yaml 등록

**동작:**

1. ScannerPlugin 추상 클래스를 상속한 구현체 작성
2. registry.yaml에 플러그인 등록 + enabled 설정
3. 다음 실행 시 자동 반영

**사용자 화면:** registry.yaml 수정으로 관리

**수락 기준:**

- Given 새 플러그인 구현체 + registry.yaml 등록, When 정찰 실행, Then 새 플러그인이 병렬 스캐너에 포함됨
- Given 플러그인 enabled=false, When 정찰 실행, Then 해당 플러그인 건너뛰고 나머지 정상 실행
- Given 플러그인이 에러 발생, When 병렬 실행 중, Then 나머지 플러그인에 영향 없이 해당 플러그인만 실패 기록

---

## 사용자 플로

### 메인 플로: 전체 모의해킹 수행

```
1. 사용자가 CLI에서 새 세션 생성
   → python cli.py new --target https://app.example.com --scope "*.example.com"

2. 워크스페이스 생성됨 (workspaces/{random_id}/)
   → config.yaml 편집하여 크레덴셜, 도구 토글, LLM 모델 설정

3. 정찰 + Knowledge Graph 구축
   → python cli.py scan --workspace {id}
   → 1.1 인증 매핑 + 1.2 병렬 스캐너 (동시 시작)
   → LLM 종합 해석 (1회)
   → 1.3 인증된 크롤링
   → Knowledge Graph 구축 (API 관계, 데이터 플로, 비즈니스 흐름)
   → 결과: recon/knowledge_graph.json + recon/attack_surface.json 저장

4. 공격 경로 계획
   → 자동으로 Stage 2 진입 (또는 수동 실행)
   → Knowledge Graph 탐색으로 공격 경로 발견
   → 기술적 + 비즈니스 로직 + 복합 체인 시나리오 목록 표시
   → 사용자가 시나리오 선택 (또는 전체 실행)

5. 익스플로잇 실행
   → 체인 단계별로:
     → [L1] "POST /api/login에 SQLi 전송. 영향도: Medium. 승인? (y/n/edit):"
     → 사용자 승인
     → [L2] 페이로드 전송 + 응답 수집
     → [L3] 성공/실패 판정
     → 실패 시 [L4] 적응 → L2 재시도
   → 성공 시 다음 체인 단계로 진행

6. 분석 + 리포트
   → CVSS 산출 (SQLi 단독: 7.5 → 체인: 9.8)
   → report.md 생성
   → 사용자가 리포트 확인 후 고객사에 전달

7. (선택) 대시보드로 전환
   → 브라우저에서 실시간 모니터링 + 승인 UI 사용
```

### 에러 플로: WAF 차단

```
1. L2에서 페이로드 전송
2. WAF가 403 + 차단 패턴 응답
3. L3 검증: success=false, evidence=["WAF blocked: UNION SELECT pattern"]
4. L4 전술 재시도: WAF 우회 Skill 로드 → 인코딩 변경 (URL 인코딩 → 더블 인코딩)
5. L2 재전송 → L3 재검증
6. 3회 실패 시 L4 전략 전환: 에러 기반 → 블라인드 SQLi로 벡터 변경
7. Reflexion: "CloudFlare WAF가 UNION/SELECT 키워드를 차단. 주석 삽입 우회 시도 필요" 기록
```

### 에러 플로: 세션 만료

```
1. 크롤링 중 갑자기 401/403 응답
2. 세션 미들웨어가 감지 → 자동 재인증 시도
3. 재인증 성공 → 중단 지점부터 크롤링 재개
4. 재인증 실패 → 사용자에게 알림 ("세션 재인증 실패. 크레덴셜 확인 필요")
```

### 비즈니스 로직 테스트 플로: 결제 금액 변조

```
1. Stage 1에서 Knowledge Graph 구축 시:
   - 결제 관련 노드 식별: cart_add, order_create, payment
   - DataPath 추출: price가 cart_add에서 생성 → order_create 경유 → payment에서 사용
   - 엣지: cart_add --calls--> order_create --calls--> payment
   - 엣지: cart_add --sends_data(price)--> payment

2. Stage 2에서 KG 탐색:
   - DataPath의 price 경로에서 변조 가능 지점 발견
   - 가설 생성: "payment API의 amount를 변조하면 가격 조작 가능"
   - 가설 생성: "order_create를 건너뛰고 payment를 직접 호출하면 단계 우회 가능"

3. Stage 3 실행:
   → [L1] "POST /cart/add → POST /order/create → POST /payment에서 amount=1로 변조. 영향도: High. 승인?"
   → 사용자 승인
   → [L2] 정상 흐름대로 장바구니 → 주문까지 진행 후, 결제 단계에서 amount 변조
   → [L3] 검증: 결제 성공 응답(200) + 변조된 금액으로 주문 완료 여부 확인
   → 성공 시: Finding 기록 (가격 변조 취약점, 증거 = 변조 전/후 요청/응답)
   → 실패 시: "서버 측 금액 검증 존재" 기록
```

---

## 비목표 (만들지 않을 것)

- **인프라 해킹:** 네트워크 레벨 공격 (포트 스캔, 서비스 익스플로잇)은 범위 밖. 웹 애플리케이션만 대상
- **0-day 취약점 발견:** 알려진 취약점 패턴과 로직 결함만 탐지. 바이너리 분석이나 퍼징은 포함하지 않음
- **DDoS/서비스 거부:** 대량 트래픽을 발생시키는 공격은 수행하지 않음
- **자율 실행 모드:** 사용자 승인 없이 공격을 자동 실행하는 모드는 만들지 않음
- **다국어 UI:** 대시보드는 한국어/영어만 지원. 다국어 i18n은 향후 과제
- **모바일 앱 테스트:** 웹 앱의 API 레벨만 대상. 모바일 앱 바이너리 분석은 범위 밖
- **취약점 익스플로잇 이후 포스트 익스플로잇:** 래터럴 무브먼트, 피벗팅, 권한 유지(persistence)는 범위 밖

---

## 경계

- ✅ **항상:** 모든 HTTP 요청/응답을 history.jsonl에 기록, 승인/거부를 audit.jsonl에 기록, 민감 데이터 마스킹, 스코프 바운더리 내에서만 요청 전송
- ⚠️ **먼저 확인:** 새 스캐너 플러그인 추가, Skill 파일 수정, 데이터 모델 스키마 변경, 새 Python 의존성 추가
- 🚫 **절대 금지:** 스코프 밖 도메인/IP에 요청 전송, 민감 데이터를 평문으로 저장/로그, LangSmith 등 외부 SaaS에 모의해킹 데이터 전송, 사용자 승인 없이 High 영향도 공격 실행

---

## 구현 단계

|단계|범위|의존성|산출물|
|---|---|---|---|
|0|기반 인프라: 세션 미들웨어 · Skill 로더 · 플러그인 레지스트리 · 워크스페이스 구조|없음|미들웨어 단위 테스트 통과 · 워크스페이스 CRUD 동작|
|1|Stage 1 정찰: 인증 매핑 · 스캐너 1~2개 · LLM 해석 · 크롤링|단계 0|타겟에 대해 attack_surface.json 생성|
|2|Stage 2 계획: 가설 생성 · Hybrid Planner · 경로 랭킹|단계 1|최소 1개 공격 체인 시나리오 생성|
|3|Stage 3 핵심: L1 승인(CLI) · L2 경로 A · L3 검증 · L4 적응|단계 2|SQLi 체인 1개 end-to-end 성공|
|4|Stage 3 확장: L2 경로 B(도구) · 추가 Skill · 추가 스캐너 플러그인|단계 3|도구 경로 동작 · Skill 5개+|
|5|Stage 4 분석: CVSS 산정 · 비즈니스 영향 · 리포트 생성|단계 3|report.md 생성|
|6|웹 대시보드: WebSocket 연동 · React UI · 승인 게이트 전환|단계 5|대시보드 7개 패널 동작|

---

## 파일 구조

```
EAZY/
│
├── src/
│   ├── frontend/                       # 웹 대시보드 (React · 마지막 개발)
│   ├── backend/                        # API 서버 (FastAPI · WebSocket)
│   └── agents/                         # 에이전트 파이프라인
│       ├── core/                       # 엔진 · 상태 · 공통 모델
│       ├── middleware/                  # 세션 미들웨어
│       ├── recon/                      # Stage 1 — 정찰
│       ├── planning/                   # Stage 2 — 공격 경로 계획
│       ├── exploit/                    # Stage 3 — 익스플로잇 (4레이어)
│       │   └── execution/              # L2. 실행 (이중 경로)
│       ├── analysis/                   # Stage 4 — 분석 + 리포트
│       ├── skills/                     # Skill 시스템
│       │   └── static/                 # 정적 Skill
│       │       ├── attacks/
│       │       ├── tools/
│       │       ├── waf/
│       │       ├── verify/
│       │       ├── chains/
│       │       ├── crypto/
│       │       └── business_logic/     # 비즈니스 로직 취약점 패턴
│       ├── tools/                      # 스캐너 플러그인 레지스트리
│       └── rag/                        # RAG (축소)
│
├── workspaces/                         # 세션 데이터 (.gitignore)
│   └── {random_id}/
│       ├── config.yaml
│       ├── recon/                      # Stage 1 결과
│       │   ├── knowledge_graph.json    # Knowledge Graph (핵심 출력)
│       │   ├── attack_surface.json     # 공격 표면 요약 (KG에서 파생)
│       │   ├── crypto_context.yaml
│       │   └── scanner_results/
│       ├── planning/
│       ├── exploit/
│       ├── analysis/
│       ├── http_history/
│       └── logs/
│
├── tests/
├── cli.py                              # CLI 진입점
├── config.yaml                         # 전역 설정
├── requirements.txt
├── .gitignore
└── README.md
```
