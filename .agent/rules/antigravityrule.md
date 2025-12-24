---
trigger: always_on
---

# **무조건 지켜야하는 것**
1. 너는 한국인으로써 생각도 한국어로 해야하고, 답변/Implementation Plan도 **무조건 한국어**로 해줘야 해.
2. 너가 뭔가하려고 할 때, 반드시 나한테 계획을 말하고 나한테 승인 받은 뒤 해야 돼.
3. Shell은 zsh으로 사용해야 돼.


---

# **PROJECT INTELLIGENCE: AI-Based DAST Tool**

이 문서는 Google Antigravity (Gemini 3 Pro) 에이전트를 위한 최상위 컨텍스트(Root Context) 정의서입니다.  
본 프로젝트의 개발, 리팩토링, 테스트를 수행할 때 아래의 지침을 \*\*헌법(Constitution)\*\*처럼 준수하십시오.

## **1\. 프로젝트 정체성 (Identity)**

우리는 Python 3.12 (FastAPI) 와 React (Vite \+ shadcn/ui) 를 기반으로 하는 지능형 DAST(Dynamic Application Security Testing) 도구를 개발합니다.  
단순한 스캐너가 아니라, LLM을 활용해 비즈니스 로직을 분석하고 연쇄 공격 시나리오를 시각화(React Flow) 하는 것이 핵심 목표입니다.

## **2\. 문서 참조 체계 (Documentation Map)**

모든 코드를 작성하기 전에, 반드시 아래 문서들을 먼저 참조하여 'Context Anchoring'을 수행하십시오. **임의로 판단하지 말고 문서에 정의된 스펙을 따르십시오.**

| 문서 파일 (docs/) | 설명 | 참조 시점 |
| :---- | :---- | :---- |
| **dast\_functional\_spec.md** | **\[기획서\]** 기능 요구사항, REQ-ID 정의 | **항상 (Always)** |
| **coding\_convention.md** | **\[규칙\]** 언어별 스타일, 폴더 구조, 기술 스택 | **코드 작성 전** |
| **db\_schema.md** | **\[DB\]** 테이블 구조, 필드명, 관계 정의 | **모델링/쿼리 작성 시** |
| **api\_spec.md** | **\[API\]** 엔드포인트 URL, Request/Response 포맷 | **프론트/백엔드 연동 시** |
| **agent\_prompts.md** | **\[페르소나\]** 에이전트별 역할 및 전문성 정의 | **세션 시작 시** |

## **3\. 핵심 원칙 (Core Directives)**

### **3.1. 보안 최우선 (Security First)**

* 우리는 보안 도구를 만듭니다. 따라서 **도구 자체의 보안**이 가장 중요합니다.  
* 모든 입력값 검증(Pydantic), SQL Injection 방지(ORM 사용), XSS 방지(React escaping)를 기본으로 적용하십시오.  
* **security-auditor** 규칙을 준수하여 취약점 없는 코드를 작성하십시오.

### **3.2. 아키텍처 준수 (Architectural Integrity)**

* **Backend:** Controller \-\> Service \-\> Repository 계층 구조를 엄격히 유지하십시오. 비즈니스 로직이 API 라우터에 노출되면 안 됩니다.  
* **Frontend:** 컴포넌트는 presentation과 container 로직을 분리하고, 전역 상태는 Zustand로 관리하십시오.  
* **architect-reviewer** 규칙에 따라 스파게티 코드를 방지하십시오.

### **3.3. 테스트 주도 (Test-Driven Approach)**

* 기능을 구현하기 전에 **"어떻게 검증할 것인가?"** 를 먼저 고민하십시오.  
* 가능하다면 pytest (Backend) 또는 Vitest (Frontend) 테스트 코드를 먼저 제안하고 구현을 시작하십시오.

## **4\. 작업 프로세스 (Workflow Protocol)**

사용자(User)로부터 명령을 받으면 다음 단계를 따르십시오.

1. **Analyze (분석):** 사용자의 요청이 dast\_functional\_spec.md의 어떤 REQ-ID와 관련이 있는지 파악합니다.  
2. **Plan (설계):** 코드를 작성하기 전에, 수정할 파일 목록과 구현 논리를 먼저 브리핑합니다. (Activation Mode가 Agent-assisted일 경우 승인 대기)  
3. **Implement (구현):** coding\_convention.md를 준수하여 코드를 작성합니다.  
4. **Verify (검증):** 작성된 코드가 문법적으로 올바른지, 기존 기능을 깨뜨리지 않는지 확인합니다.  
5. **Document (문서화):** API나 스키마가 변경되었다면 technical-writer 규칙에 따라 관련 문서를 업데이트합니다.