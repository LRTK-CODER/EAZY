# Claude 에이전트 시스템

[← 메인 문서로 돌아가기](../README.md)

---

## 목차

1. [개요](#개요)
2. [에이전트 구성](#에이전트-구성)
3. [에이전트 협업 패턴](#에이전트-협업-패턴)
4. [설정 파일](#설정-파일)
5. [사용 가이드](#사용-가이드)

---

## 개요

EAZY 프로젝트는 **Claude 에이전트 시스템**을 활용하여 개발됩니다. `.claude/agents/` 디렉토리에 17개의 전문 에이전트가 구성되어 있으며, 각 에이전트는 특정 영역의 전문가 역할을 수행합니다.

### 에이전트 시스템의 장점

1. **전문성**: 각 에이전트가 특정 기술 스택에 집중
2. **일관성**: 코딩 스타일 및 아키텍처 패턴 유지
3. **효율성**: 작업을 병렬로 분산 처리
4. **품질 보증**: 코드 리뷰 및 아키텍처 검토 자동화

---

## 에이전트 구성

### 전체 에이전트 목록 (17개)

| 에이전트 | 역할 | 주요 책임 |
|---------|------|----------|
| **api-designer** | API 아키텍처 설계 | REST API 설계, OpenAPI 3.1 명세 작성 |
| **architect-reviewer** | 시스템 아키텍처 검토 | 아키텍처 패턴 검증, 설계 리뷰 |
| **backend-developer** | Python/FastAPI 백엔드 개발 | API 구현, 서비스 레이어 작성 |
| **code-reviewer** | 코드 리뷰 자동화 | 보안, 성능, 스타일 검토 |
| **feature-planner** | 기능 계획 수립 | Phase 기반 작업 분해, 우선순위 결정 |
| **frontend-developer** | React 프론트엔드 개발 | UI 컴포넌트 구현, 상태 관리 |
| **git-workflow-manager** | Git 워크플로우 관리 | 브랜치 전략, 커밋 메시지 검증 |
| **python-pro** | Python 전문가 | 타입 힌트, 비동기 프로그래밍 |
| **react-specialist** | React 전문가 | Hooks, 성능 최적화, Atomic Design |
| **sql-pro** | SQL 및 데이터베이스 전문가 | 스키마 설계, 쿼리 최적화 |
| **task-distributor** | 작업 분배 조정자 | 작업 할당, 우선순위 관리 |
| **technical-writer** | 기술 문서 작성 | API 문서, README, 가이드 작성 |
| **typescript-pro** | TypeScript 전문가 | 타입 시스템, 제네릭, 유틸리티 타입 |
| **ui-designer** | UI 디자인 검토 | 디자인 시스템, 접근성, UX |
| **ux-researcher** | UX 분석 | 사용성 검증, 사용자 흐름 개선 |
| **websocket-engineer** | WebSocket 통신 전문가 | 실시간 통신, 이벤트 기반 아키텍처 |
| **react-flow-specialist** | React Flow 시각화 전문가 | 노드 기반 그래프, 비즈니스 로직 맵 |

---

### 주요 에이전트 상세

#### api-designer (API 아키텍처 설계)

**전문 분야**:
- RESTful API 설계 원칙
- OpenAPI 3.1 명세 작성
- HTTP 메서드 및 상태 코드 선택
- API 버저닝 전략

**작업 예시**:
- API 엔드포인트 설계 (`POST /projects/`, `GET /projects/{id}`)
- 요청/응답 스키마 정의
- 에러 핸들링 규칙 수립

---

#### backend-developer (Python/FastAPI 백엔드 개발)

**전문 분야**:
- FastAPI 프레임워크
- SQLModel ORM
- 비동기 프로그래밍 (AsyncIO)
- Pydantic 데이터 유효성 검증

**작업 예시**:
- API 엔드포인트 구현
- 서비스 레이어 작성
- 데이터베이스 마이그레이션 생성

**관련 문서**: [TECH_STACK.md](TECH_STACK.md#backend)

---

#### frontend-developer (React 프론트엔드 개발)

**전문 분야**:
- React 19 (Hooks, Suspense)
- TypeScript Strict Mode
- TanStack Query (서버 상태 관리)
- shadcn/ui 컴포넌트

**작업 예시**:
- UI 컴포넌트 구현
- 폼 유효성 검증 (Zod + React Hook Form)
- TanStack Query 커스텀 훅 작성

**관련 문서**: [TECH_STACK.md](TECH_STACK.md#frontend)

---

#### react-specialist (React 전문가)

**전문 분야**:
- React Hooks 최적화 (useMemo, useCallback)
- Atomic Design 아키텍처
- 성능 최적화 (Code Splitting, Lazy Loading)
- 접근성 (a11y)

**작업 예시**:
- 컴포넌트 리팩토링
- 성능 병목 해결
- Atomic Design 패턴 적용

---

#### code-reviewer (코드 리뷰 자동화)

**전문 분야**:
- 보안 취약점 검출
- 성능 이슈 식별
- 코딩 컨벤션 검증
- 테스트 커버리지 확인

**리뷰 체크리스트**:
- ✅ Type Hint 존재 여부
- ✅ SQL Injection 방지
- ✅ XSS 방지
- ✅ 에러 핸들링 적절성
- ✅ 테스트 코드 존재

**관련 문서**: [coding_convention.md](coding_convention.md)

---

#### ui-designer (UI 디자인 검토)

**전문 분야**:
- 디자인 시스템 구축
- 색상/타이포그래피 일관성
- 반응형 디자인
- 접근성 (WCAG 2.1)

**평가 기준** (10점 만점):
- 시각적 일관성: 8.5/10
- 사용성: 8.5/10
- 접근성: 9.0/10
- 반응형: 8.0/10

---

#### ux-researcher (UX 분석)

**전문 분야**:
- 사용자 흐름 분석
- 인지 부하 최소화
- 에러 메시지 개선
- 피드백 메커니즘

**평가 기준** (10점 만점):
- 학습 곡선: 8.5/10
- 효율성: 8.5/10
- 에러 회복: 9.0/10
- 만족도: 8.0/10

---

#### task-distributor (작업 분배 조정자)

**전문 분야**:
- 작업 분해 (Task Breakdown)
- 우선순위 결정
- 의존성 관리
- 진행 상황 추적

**작업 예시**:
- Phase별 작업 목록 생성
- 에이전트 간 작업 할당
- 블로킹 이슈 해결

---

#### technical-writer (기술 문서 작성)

**전문 분야**:
- API 참조 문서
- 사용자 가이드
- 아키텍처 문서
- Markdown 작성

**작업 예시**:
- README.md 작성
- API 명세 작성 (api_spec.md)
- 데이터베이스 스키마 문서화 (db_schema.md)

**관련 문서**: [README.md](../README.md), [QUICK_START.md](../QUICK_START.md)

---

## 에이전트 협업 패턴

### Phase 기반 개발 프로세스

EAZY 프로젝트는 Phase 기반으로 개발되며, 각 Phase마다 여러 에이전트가 협업합니다.

#### Phase 4 예시: ProjectDetailPage 구현

**작업**: ProjectDetailPage에 Target 관리 기능 통합

**협업 프로세스**:

```
1. feature-planner
   - 작업 분해: UI 컴포넌트, API 통합, 테스트
   - 우선순위: TDD 순서 결정

2. typescript-pro
   - ProjectDetailPage 컴포넌트 구현
   - TargetList 통합
   - useTargets Hook 사용

3. frontend-developer
   - CreateTargetForm 다이얼로그 추가
   - EditTargetForm 다이얼로그 추가
   - DeleteTargetDialog 추가

4. react-specialist
   - 컴포넌트 최적화 (useMemo, useCallback)
   - Presentation & Container 패턴 적용

5. ui-designer
   - UI 검토: 8.5/10
   - 피드백: "Target 테이블의 가독성이 우수함"

6. ux-researcher
   - UX 검토: 8.5/10
   - 피드백: "스캔 버튼 위치가 직관적임"

7. code-reviewer
   - 코드 리뷰: 9.0/10
   - 피드백: "타입 안전성 확보, 테스트 커버리지 100%"

8. technical-writer
   - 문서화: PLAN_MVP_Frontend.md 업데이트
   - Task 4.22 완료 표시
```

**결과**:
- 28개 테스트 모두 통과
- UI/UX 점수 8.5/10 이상
- Phase 4 완료 (85%)

**관련 커밋**:
```
64c2fd6 feat(frontend): implement ProjectDetailPage Target integration (TDD GREEN)
```

---

### 코드 리뷰 협업

**프로세스**:
```
1. 개발자 에이전트 (backend-developer, frontend-developer)
   - 코드 구현

2. 전문가 에이전트 (python-pro, react-specialist, typescript-pro)
   - 베스트 프랙티스 검증
   - 성능 최적화 제안

3. code-reviewer
   - 보안 취약점 검토
   - 코딩 컨벤션 검증

4. architect-reviewer
   - 아키텍처 패턴 일관성 확인
   - 레이어 분리 검증

5. technical-writer
   - 문서화 필요 사항 체크
   - 주석 품질 검토
```

---

### 문서화 협업

**프로세스**:
```
1. feature-planner
   - 문서화 범위 결정

2. technical-writer
   - 초안 작성

3. 전문가 에이전트 (해당 도메인)
   - 기술적 정확성 검토

4. ux-researcher
   - 문서 가독성 검토

5. git-workflow-manager
   - 문서 버전 관리
   - 커밋 메시지 검증
```

---

## 설정 파일

### .claude/settings.local.json

```json
{
  "outputStyle": "default",
  "spinnerTipsEnabled": false,
  "statusLine": {
    "type": "command",
    "command": "~/.claude/scripts/context-bar.sh"
  }
}
```

**설정 항목**:
- `outputStyle`: 출력 스타일 (default, compact, verbose)
- `spinnerTipsEnabled`: 스피너 팁 표시 여부
- `statusLine`: 상태 표시줄 설정

---

### 에이전트 파일 위치

```
/Users/lrtk/Documents/Project/EAZY/.claude/agents/
├── api-designer.md
├── architect-reviewer.md
├── backend-developer.md
├── code-reviewer.md
├── feature-planner.md
├── frontend-developer.md
├── git-workflow-manager.md
├── python-pro.md
├── react-specialist.md
├── sql-pro.md
├── task-distributor.md
├── technical-writer.md
├── typescript-pro.md
├── ui-designer.md
├── ux-researcher.md
├── websocket-engineer.md
└── react-flow-specialist.md
```

**파일 구조**:
- 각 에이전트는 독립된 Markdown 파일
- 에이전트별 역할, 전문 분야, 작업 예시 포함
- 프롬프트 템플릿 및 체크리스트 포함

---

## 사용 가이드

### 에이전트 호출 방법

#### 1. 작업 요청 시 에이전트 지정

```markdown
@api-designer
프로젝트 아카이브 API 엔드포인트를 설계해주세요.
요구사항:
- PATCH /projects/{id}/restore
- 아카이브된 프로젝트를 복원
- is_archived = false, archived_at = null
```

#### 2. 여러 에이전트 순차 호출

```markdown
@feature-planner
Phase 5: Asset 시각화 기능 작업을 분해해주세요.

@frontend-developer
Asset 테이블 컴포넌트를 구현해주세요.

@ui-designer
Asset 테이블 UI를 검토해주세요.
```

#### 3. 에이전트 협업 요청

```markdown
@task-distributor
ProjectDetailPage에 Target 관리 기능을 통합하는 작업을
Phase별로 분해하고, 적절한 에이전트에게 할당해주세요.
```

---

### 에이전트 선택 가이드

| 작업 유형 | 추천 에이전트 |
|----------|-------------|
| API 설계 | api-designer |
| Backend 구현 | backend-developer, python-pro |
| Frontend 구현 | frontend-developer, react-specialist, typescript-pro |
| DB 스키마 설계 | sql-pro |
| 코드 리뷰 | code-reviewer, architect-reviewer |
| UI 디자인 검토 | ui-designer |
| UX 분석 | ux-researcher |
| 문서 작성 | technical-writer |
| 작업 계획 | feature-planner, task-distributor |
| Git 관리 | git-workflow-manager |

---

### 베스트 프랙티스

#### 1. 명확한 컨텍스트 제공

```markdown
❌ Bad:
@frontend-developer
프로젝트 페이지 만들어주세요.

✅ Good:
@frontend-developer
ProjectDetailPage에 Target 목록 테이블을 추가해주세요.
- TargetList 컴포넌트 사용
- 스캔 트리거 버튼 포함
- useTargets Hook으로 데이터 페칭
```

---

#### 2. TDD 순서 준수

```markdown
@frontend-developer
Target 삭제 다이얼로그를 TDD로 구현해주세요.

1. RED: 테스트 작성 (DeleteTargetDialog.test.tsx)
2. GREEN: 최소 구현 (DeleteTargetDialog.tsx)
3. REFACTOR: 코드 개선
```

---

#### 3. 리뷰 프로세스 활용

```markdown
# 구현 후 리뷰 요청
@code-reviewer
ProjectDetailPage 구현을 리뷰해주세요.

@ui-designer
Target 테이블 UI를 평가해주세요.

@ux-researcher
사용자 흐름을 분석해주세요.
```

---

### 에이전트 커스터마이징

#### 새 에이전트 추가

1. `.claude/agents/` 디렉토리에 Markdown 파일 생성
2. 에이전트 역할 및 전문 분야 정의
3. 작업 예시 및 체크리스트 포함

**예시** (security-analyst.md):
```markdown
# Security Analyst

## 역할
보안 취약점 분석 및 보안 정책 수립

## 전문 분야
- OWASP Top 10 검증
- 인증/인가 검토
- 데이터 암호화
- 보안 설정 검토

## 작업 예시
- SQL Injection 방지 확인
- XSS 방지 확인
- CSRF 토큰 검증
- 비밀번호 해싱 검토
```

---

## 참고 자료

- Claude 공식 문서: https://docs.anthropic.com/
- 에이전트 시스템 소개: https://www.anthropic.com/agents
- 프롬프트 엔지니어링 가이드: https://docs.anthropic.com/prompt-engineering

---

**다음 문서**: [GLOSSARY.md](GLOSSARY.md)

[← 메인 문서로 돌아가기](../README.md)
