# 아키텍처 검토 보고서 (Architecture Review Report)

**일시:** 2025-12-23  
**검토자:** Architect Reviewer Agent

## 1. 개요 (Executive Summary)
본 프로젝트는 **FastAPI, React, Zustand, SQLAlchemy**와 같은 최신 기술 스택을 활용하고 있으며, 프론트엔드와 백엔드 간의 큰 역할 분리는 잘 이루어져 있습니다.  
그러나 **Repository Layer(저장소 계층)** 등 엄격한 아키텍처 패턴이 일부 누락되어 있으며, `db_schema.md`나 `coding_convention.md`와 같은 **핵심 문서가 비어 있어**, 향후 유지보수 및 확장성에 큰 위험(Risk)이 존재합니다.

## 2. 강점 (Strengths)
*   **최신 기술 스택**: 고성능의 인기 있는 프레임워크(FastAPI, Vite+React)를 적절히 선정했습니다.
*   **프론트엔드 상태 관리**: `Zustand`를 효과적으로 사용하여(예: Proxy 패킷 관리) 비즈니스 로직과 UI 컴포넌트를 깔끔하게 분리했습니다.
*   **API 설계**: `APIRouter`와 Pydantic 모델을 사용하여 요청/응답 검증 및 코드 분리가 잘 되어 있습니다.

## 3. 핵심 발견 및 취약점 (Critical Findings & Weaknesses)

### 3.1. 문서 부채 (Documentation Debt) - [High Risk]
*   **`docs/specs/db_schema.md` 비어 있음**: 데이터베이스 구조에 대한 '단일 진실 공급원(Source of Truth)'이 없습니다.
*   **`docs/specs/coding_convention.md` 비어 있음**: 통일된 코드 규칙이 정의되지 않아 코드 일관성이 깨질 우려가 있습니다.

### 3.2. 아키텍처 위반 (Architecture Violations)
*   **Repository Layer 누락 (Backend)**:
    *   **관찰**: `TargetService` (`backend/app/services/target_service.py`) 등에서 `db.query()`를 통해 DB에 직접 접근하고 있습니다.
    *   **위반**: 프로젝트 규칙상 "Controller -> Service -> Repository 계층 구조 엄수"가 요구됩니다.
    *   **영향**: 비즈니스 로직과 데이터 접근 로직이 강하게 결합되어(Coupling), 테스트가 어렵고 리팩토링이 힘들어집니다.

## 4. 권고 사항 (Recommendations)

### 1단계: 컨텍스트 확보 (Context Anchoring) - [즉시 실행]
*   **조치**: `coding_convention.md`와 `db_schema.md`를 즉시 작성합니다.
*   **이유**: 이 문서들은 개발의 **"헌법"**과 같습니다. 이 기준 없이 진행되는 개발은 설계 의도와 어긋날 확률이 매우 높습니다.

### 2단계: 구조적 리팩토링 (Structural Refactoring) - [단기 목표]
*   **조치**: `backend/app/repositories/` 계층을 도입합니다.
*   **세부 내용**: Service에 있는 `db.query` 로직을 Repository(예: `TargetRepository`)로 이동시킵니다. Service는 순수 비즈니스 로직만 담당해야 합니다.

### 3단계: 보안 및 안정성 (Security & Stability) - [지속적 수행]
*   **조치**: `ProxyService`의 에러 처리를 강화합니다 (현재는 단순 로깅 위주).
*   **조치**: 핵심 컴포넌트에 대한 유닛 테스트를 추가합니다.

## 5. 결론
프로젝트의 기반은 튼튼하나, 문서화 및 아키텍처 엄격성 부재라는 "기술 부채(Technical Debt)"를 조기에 해결하지 않으면 병목이 될 수 있습니다. **1단계(문서화 복구)를 최우선으로 즉시 진행할 것을 강력히 권고합니다.**
