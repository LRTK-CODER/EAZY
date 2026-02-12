# Implementation Plan: REQ-001 정규식 기반 크롤링 엔진

**Status**: 🔄 In Progress
**Started**: 2025-02-12
**Last Updated**: 2026-02-13
**Estimated Completion**: -
**Phase 2 Completed**: 2026-02-12
**Phase 3 Completed**: 2026-02-12
**Phase 4 Completed**: 2026-02-12
**Phase 5 Completed**: 2026-02-12
**Phase 6 Completed**: 2026-02-13

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
LLM API 없이 정규식 패턴 매칭으로 웹 페이지 구조를 파싱하는 경량 크롤링 엔진 구현. EAZY 프로젝트의 첫 번째 구현 단계(REQ-001)로, HTML에서 링크, 폼, 버튼, 스크립트 내 API 호출 패턴을 정규식으로 추출하고, 크롤링 결과를 구조화된 사이트맵 및 JSON으로 출력한다. 오프라인 환경에서도 동작하며 외부 LLM 의존성이 없다.

**브랜치**: `feature/req-001-regex-crawler`
**기술 스택**: Python 3.12+, httpx, pydantic, pytest, pytest-asyncio, pytest-cov, respx, ruff
**총 16 TDD 사이클, 80+ 테스트 케이스, 목표 커버리지 80%+**

### Success Criteria
- [ ] 정규식으로 HTML에서 링크, 폼, 버튼, 스크립트 내 API 호출 패턴 추출
- [ ] 크롤링 결과를 구조화된 사이트맵으로 저장
- [ ] 크롤링 깊이 및 범위를 사용자가 설정 가능
- [ ] robots.txt 준수 옵션 제공
- [ ] LLM API 없이 오프라인 환경에서도 동작
- [ ] URL, 파라미터, 엔드포인트 목록을 JSON 형태로 출력

### User Impact
보안 테스터가 LLM API 키 없이도 대상 웹 애플리케이션의 구조를 빠르게 파악할 수 있다. 정규식 기반이므로 오프라인/에어갭 환경에서도 동작하며, 후속 Phase(REQ-002 Smart Crawling, REQ-004 Vulnerability Scanning)의 기반 데이터를 제공한다.

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| 정규식 기반 파싱 (BeautifulSoup/lxml 미사용) | LLM 없는 경량 오프라인 동작, 외부 의존성 최소화 | 복잡한 HTML 구조 파싱 정확도 다소 낮음 |
| httpx AsyncClient 사용 | 비동기 요청으로 크롤링 성능 확보, HTTP/2 지원 | requests 대비 학습 곡선 |
| Pydantic v2 데이터 모델 | 타입 안전성, JSON 직렬화, 유효성 검증 내장 | 런타임 오버헤드 미미 |
| respx로 HTTP 모킹 | httpx 네이티브 모킹, 실제 네트워크 요청 없이 테스트 | respx 전용 (requests 호환 안됨) |
| uv 패키지 매니저 | 빠른 의존성 해결, pyproject.toml 네이티브 | pip 대비 생태계 작음 |

---

## 📦 Dependencies

### Required Before Starting
- [x] PRD 문서 검토 완료 (`plan/PRD.md`)
- [x] Python 3.12+ 설치 확인
- [x] uv 패키지 매니저 설치 확인

### External Dependencies
- httpx: 비동기 HTTP 클라이언트
- pydantic: 데이터 모델 및 유효성 검증
- pytest: 테스트 프레임워크
- pytest-asyncio: 비동기 테스트 지원
- pytest-cov: 테스트 커버리지 측정
- respx: httpx 전용 HTTP 모킹
- ruff: 린팅 및 포맷팅

---

## 🧪 Test Strategy

### Testing Approach
**TDD Principle**: 테스트를 먼저 작성(RED)하고, 최소 구현으로 테스트를 통과(GREEN)시킨 뒤, 리팩토링(BLUE)한다.

### Test Pyramid for This Feature
| Test Type | Coverage Target | Purpose |
|-----------|-----------------|---------|
| **Unit Tests** | ≥80% | 정규식 파싱, URL 처리, robots.txt 파싱, HTTP 클라이언트, 사이트맵, 내보내기 |
| **Integration Tests** | 핵심 경로 | 크롤링 엔진 전체 워크플로우 (URL 입력 → 크롤링 → JSON 출력) |

### Test File Organization
```
tests/
├── conftest.py
├── unit/
│   ├── models/
│   │   └── test_crawl_types.py
│   └── crawler/
│       ├── test_regex_parser.py
│       ├── test_url_resolver.py
│       ├── test_robots_parser.py
│       ├── test_http_client.py
│       ├── test_sitemap.py
│       └── test_exporter.py
└── integration/
    └── crawler/
        └── test_crawler_engine.py
```

### Coverage Requirements by Phase
- **Phase 1 (프로젝트 초기화 + 데이터 모델)**: Pydantic 모델 단위 테스트 (≥80%)
- **Phase 2 (HTML Regex Parser)**: 정규식 파싱 함수 단위 테스트 (≥80%)
- **Phase 3 (URL Resolver)**: URL 변환/정규화/필터링 단위 테스트 (≥80%)
- **Phase 4 (Robots.txt Parser)**: robots.txt 파싱 및 허용 판단 단위 테스트 (≥80%)
- **Phase 5 (HTTP Client)**: 비동기 HTTP 클라이언트 단위 테스트 (≥80%)
- **Phase 6 (Sitemap & Exporter)**: 사이트맵/내보내기 단위 테스트 (≥80%)
- **Phase 7 (Crawler Engine 통합)**: 통합 테스트 + 전체 커버리지 80%+

### Test Naming Convention
```python
# pytest 기반 테스트 구조:
# 파일명: test_{module_name}.py
# 클래스: Test{ComponentName}
# 함수: test_{행위}_{조건}_{기대결과}
# 예: test_extract_links_from_empty_html_returns_empty_list
# Arrange → Act → Assert 패턴 사용
```

---

## 🚀 Implementation Phases

### Phase 1: 프로젝트 초기화 + 데이터 모델
**Goal**: 프로젝트 기반 구조 구축 및 핵심 데이터 모델 정의
**Status**: ✅ Complete

#### Tasks

**사전 작업 (non-TDD):**
- [x] **Task 0.0**: 프로젝트 초기화
  - `feature/req-001-regex-crawler` 브랜치 생성
  - `uv init` → pyproject.toml 생성
  - .gitignore, 디렉토리 구조, pytest/ruff 설정
  - 의존성 설치 (httpx, pydantic, pytest, pytest-asyncio, pytest-cov, respx, ruff)

**🔴 RED: Write Failing Tests First (TDD-0.1: 데이터 모델)**
- [x] **Test 0.1**: 크롤링 데이터 모델 단위 테스트 작성
  - File(s): `tests/unit/models/test_crawl_types.py`
  - Expected: 테스트 FAIL (모델 미구현 상태) → ✅ ModuleNotFoundError 확인
  - Details: 테스트 케이스:
    - CrawlConfig 기본값 검증 (max_depth=3, respect_robots=True 등)
    - PageResult 생성 및 필드 검증
    - FormData 필드 검증 (action, method, inputs)
    - EndpointInfo 필드 검증 (url, method, source)
    - ButtonInfo 필드 검증
    - CrawlResult JSON 직렬화/역직렬화

**🟢 GREEN: Implement to Make Tests Pass**
- [x] **Task 0.2**: Pydantic 데이터 모델 구현
  - File(s): `src/eazy/models/crawl_types.py`
  - Goal: Test 0.1 전체 통과 → ✅ 17/17 passed
  - Details: Pydantic BaseModel 상속 모델 구현 (CrawlConfig, PageResult, FormData, EndpointInfo, ButtonInfo, CrawlResult)

**🔵 REFACTOR: Clean Up Code**
- [x] **Task 0.3**: 데이터 모델 리팩토링
  - Files: `src/eazy/models/crawl_types.py`
  - Goal: 테스트 통과 유지하면서 코드 품질 개선 → ✅ 17/17 passed
  - Checklist:
    - [x] model_config 설정 최적화 (CrawlConfig frozen=True)
    - [x] 필드 기본값 및 validators 정리 (Field(default_factory=...) 적용)
    - [x] 인라인 문서화 추가 (Google 스타일 Attributes docstring)
    - [x] 불필요한 코드 제거

#### Commits
```
chore: initialize project with uv, pytest, ruff
test(models): add failing tests for crawl data models
feat(models): implement crawl data models with pydantic
refactor(models): optimize data model configuration
```

#### Quality Gate ✋

**⚠️ STOP: Phase 2 진행 전 모든 체크 항목을 통과해야 함**

**TDD Compliance** (CRITICAL):
- [x] **Red Phase**: 테스트를 먼저 작성하고 실패 확인 (ModuleNotFoundError)
- [x] **Green Phase**: 최소 코드로 테스트 통과 (17/17 passed)
- [x] **Refactor Phase**: 테스트 통과 유지하면서 코드 개선 (frozen, Field, docstrings)
- [x] **Coverage Check**: 커버리지 요구사항 충족 (100%, 목표 80%+)
  ```bash
  # 커버리지 확인
  uv run pytest --cov=src/eazy --cov-report=term-missing
  ```

**Build & Tests**:
- [x] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [x] **All Tests Pass**: 100% 테스트 통과 (17/17, 스킵 없음)
- [x] **Test Performance**: 테스트 스위트 0.05초 완료
- [x] **No Flaky Tests**: 테스트 일관 통과 확인

**Code Quality**:
- [x] **Linting**: 린팅 에러/경고 없음 (ruff check passed)
- [x] **Formatting**: 프로젝트 표준에 맞는 포맷팅 (ruff format passed)
- [x] **Type Safety**: 모든 필드 타입 힌트 적용
- [x] **Static Analysis**: 정적 분석 도구 심각 이슈 없음

**Security & Performance**:
- [x] **Dependencies**: 알려진 보안 취약점 없음
- [x] **Performance**: 성능 저하 없음
- [x] **Memory**: 메모리 누수/자원 이슈 없음
- [x] **Error Handling**: Pydantic ValidationError로 잘못된 입력 처리

**Documentation**:
- [x] **Code Comments**: Google 스타일 Attributes docstring 추가
- [x] **API Docs**: 공개 인터페이스 문서화 (모든 모델 docstring)
- [x] **README**: N/A (Phase 1)

**Manual Testing**:
- [x] **Functionality**: 기능 정상 동작 확인
- [x] **Edge Cases**: 경계 조건 테스트 완료
- [x] **Error States**: 에러 처리 검증 완료

**Validation Commands**:
```bash
# 테스트 실행
uv run pytest

# 커버리지 확인
uv run pytest --cov=src/eazy --cov-report=term-missing

# 린팅
uv run ruff check src/ tests/

# 포맷팅
uv run ruff format --check src/ tests/

# 전체 검증 (한 줄)
uv run pytest --cov=src/eazy --cov-report=term-missing && uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [x] CrawlConfig() 기본값 올바른지 확인
- [x] CrawlResult.model_dump_json() 출력 스키마 확인
- [x] 잘못된 타입 입력 시 ValidationError 발생 확인

---

### Phase 2: HTML Regex Parser
**Goal**: HTML에서 링크, 폼, 버튼, API 호출 패턴을 정규식으로 추출
**Status**: ✅ Complete

#### Tasks

**🔴 RED: Write Failing Tests First (TDD-1.1: 링크 추출)**
- [x] **Test 1.1**: 링크 추출 단위 테스트 작성
  - File(s): `tests/unit/crawler/test_regex_parser.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ ImportError 확인
  - Details: 테스트 케이스:
    - 기본 `<a href="...">` 링크 추출
    - 다중 링크 추출
    - 빈 HTML에서 빈 리스트 반환
    - href 없는 `<a>` 태그 무시
    - 작은따옴표/큰따옴표 모두 처리
    - javascript:, mailto:, tel: 프로토콜 무시

**🟢 GREEN: Implement to Make Tests Pass (TDD-1.1)**
- [x] **Task 1.1**: 링크 추출 함수 구현
  - File(s): `src/eazy/crawler/regex_parser.py`
  - Goal: Test 1.1 통과 → ✅ 6/6 passed
  - Details: `extract_links(html: str) -> list[str]` 구현

**🔵 REFACTOR (TDD-1.1)**
- [x] **Task 1.1R**: 링크 추출 리팩토링
  - Files: `src/eazy/crawler/regex_parser.py`
  - Goal: 정규식 컴파일 최적화 (모듈 레벨 상수) → ✅ 6/6 passed

**🔴 RED: Write Failing Tests First (TDD-1.2: 폼 추출)**
- [x] **Test 1.2**: 폼 추출 단위 테스트 작성
  - File(s): `tests/unit/crawler/test_regex_parser.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ AttributeError 확인
  - Details: 테스트 케이스:
    - 기본 `<form>` 추출 (action, method)
    - `<input>` 필드 추출 (name, type, value)
    - 다중 폼 추출
    - action 없는 폼 처리
    - 기본 method=GET
    - `<select>`, `<textarea>` 추출
    - hidden input 추출

**🟢 GREEN: Implement to Make Tests Pass (TDD-1.2)**
- [x] **Task 1.2**: 폼 추출 함수 구현
  - File(s): `src/eazy/crawler/regex_parser.py`
  - Goal: Test 1.2 통과 → ✅ 13/13 passed
  - Details: `extract_forms(html: str, base_url: str) -> list[FormData]` 구현

**🔵 REFACTOR (TDD-1.2)**
- [x] **Task 1.2R**: 폼 추출 리팩토링
  - Files: `src/eazy/crawler/regex_parser.py`
  - Goal: 코드 품질 개선 → ✅ 13/13 passed

**🔴 RED: Write Failing Tests First (TDD-1.3: 버튼 추출)**
- [x] **Test 1.3**: 버튼 추출 단위 테스트 작성
  - File(s): `tests/unit/crawler/test_regex_parser.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ AttributeError 확인
  - Details: 테스트 케이스:
    - 기본 `<button>` 추출
    - onclick 이벤트 핸들러 추출
    - submit 타입 버튼

**🟢 GREEN: Implement to Make Tests Pass (TDD-1.3)**
- [x] **Task 1.3**: 버튼 추출 함수 구현
  - File(s): `src/eazy/crawler/regex_parser.py`
  - Goal: Test 1.3 통과 → ✅ 18/18 passed
  - Details: `extract_buttons(html: str) -> list[ButtonInfo]` 구현

**🔵 REFACTOR (TDD-1.3)**
- [x] **Task 1.3R**: 버튼 추출 리팩토링
  - Files: `src/eazy/crawler/regex_parser.py`
  - Goal: 코드 품질 개선 → ✅ 18/18 passed

**🔴 RED: Write Failing Tests First (TDD-1.4: API 호출 패턴 추출)**
- [x] **Test 1.4**: API 호출 패턴 추출 단위 테스트 작성
  - File(s): `tests/unit/crawler/test_regex_parser.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ ImportError 확인
  - Details: 테스트 케이스:
    - `fetch('/api/...')` 패턴
    - `axios.get/post(...)` 패턴
    - `XMLHttpRequest` open 패턴
    - jQuery `$.ajax(...)` 패턴
    - 전체 URL (`https://api.example.com/...`)
    - 빈 HTML 처리
    - 중복 제거

**🟢 GREEN: Implement to Make Tests Pass (TDD-1.4)**
- [x] **Task 1.4**: API 호출 패턴 추출 함수 구현
  - File(s): `src/eazy/crawler/regex_parser.py`
  - Goal: Test 1.4 통과 → ✅ 25/25 passed
  - Details: `extract_api_endpoints(html: str) -> list[EndpointInfo]` 구현

**🔵 REFACTOR (TDD-1.4)**
- [x] **Task 1.4R**: API 호출 패턴 추출 리팩토링
  - Files: `src/eazy/crawler/regex_parser.py`
  - Goal: 정규식 패턴 최적화 → ✅ 25/25 passed

#### Commits
```
test(crawler): add failing tests for link extraction
feat(crawler): implement link extraction with regex
refactor(crawler): optimize link extraction regex patterns
test(crawler): add failing tests for form extraction
feat(crawler): implement form extraction
refactor(crawler): improve form extraction code quality
test(crawler): add failing tests for button extraction
feat(crawler): implement button extraction
refactor(crawler): improve button extraction code quality
test(crawler): add failing tests for API endpoint extraction
feat(crawler): implement API endpoint extraction
refactor(crawler): optimize API endpoint extraction patterns
```

#### Quality Gate ✋

**⚠️ STOP: Phase 3 진행 전 모든 체크 항목을 통과해야 함**

**TDD Compliance** (CRITICAL):
- [x] **Red Phase**: 테스트를 먼저 작성하고 실패 확인 (ImportError/AttributeError)
- [x] **Green Phase**: 최소 코드로 테스트 통과 (25/25 passed)
- [x] **Refactor Phase**: 테스트 통과 유지하면서 코드 개선
- [x] **Coverage Check**: 커버리지 요구사항 충족 (100%, 목표 80%+)
  ```bash
  # 커버리지 확인
  uv run pytest tests/unit/crawler/ --cov=src/eazy/crawler --cov-report=term-missing
  # Result: 93/93 statements, 100% coverage
  ```

**Build & Tests**:
- [x] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [x] **All Tests Pass**: 100% 테스트 통과 (25/25, 스킵 없음)
- [x] **Test Performance**: 테스트 스위트 0.05초 완료
- [x] **No Flaky Tests**: 테스트 일관 통과 확인

**Code Quality**:
- [x] **Linting**: 린팅 에러/경고 없음 (ruff check passed)
- [x] **Formatting**: 프로젝트 표준에 맞는 포맷팅 (ruff format applied)
- [x] **Type Safety**: 모든 함수 시그니처 타입 힌트 적용
- [x] **Static Analysis**: 정적 분석 도구 심각 이슈 없음

**Security & Performance**:
- [x] **Dependencies**: 알려진 보안 취약점 없음
- [x] **Performance**: 성능 저하 없음 (모듈 레벨 정규식 컴파일)
- [x] **Memory**: 메모리 누수/자원 이슈 없음
- [x] **Error Handling**: 빈 HTML, 잘못된 형식 등 엣지 케이스 처리

**Documentation**:
- [x] **Code Comments**: Google 스타일 docstring 추가
- [x] **API Docs**: 공개 인터페이스 문서화 (모든 함수 docstring)
- [x] **README**: N/A (Phase 2)

**Manual Testing**:
- [x] **Functionality**: 기능 정상 동작 확인
- [x] **Edge Cases**: 경계 조건 테스트 완료
- [x] **Error States**: 에러 처리 검증 완료

**Validation Commands**:
```bash
# 테스트 실행
uv run pytest tests/unit/crawler/

# 커버리지 확인
uv run pytest tests/unit/crawler/ --cov=src/eazy/crawler --cov-report=term-missing

# 린팅
uv run ruff check src/eazy/crawler/ tests/unit/crawler/

# 포맷팅 확인
uv run ruff format --check src/eazy/crawler/ tests/unit/crawler/

# 전체 검증 (한 줄)
uv run pytest tests/unit/crawler/ --cov=src/eazy/crawler --cov-report=term-missing && uv run ruff check src/eazy/crawler/ tests/unit/crawler/
```

**Manual Test Checklist**:
- [x] 실제 HTML 샘플에서 링크 추출 결과 확인
- [x] 복잡한 폼(다중 input, select, textarea)에서 정확한 추출 확인
- [x] JavaScript 코드 내 API 호출 패턴 감지 확인

---

### Phase 3: URL Resolver
**Goal**: 상대/절대 URL 변환, 정규화, 스코프 필터링
**Status**: ✅ Complete

#### Tasks

**🔴 RED: Write Failing Tests First (TDD-2.1: URL 변환)**
- [x] **Test 2.1**: URL 변환 단위 테스트 작성
  - File(s): `tests/unit/crawler/test_url_resolver.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ ModuleNotFoundError 확인
  - Details: 테스트 케이스:
    - 상대 경로 → 절대 URL 변환
    - protocol-relative URL (//) 처리
    - 부모 경로 (../) 해석
    - fragment-only (#section) → None 반환
    - 빈 href → None 반환
    - 이미 절대 URL → 그대로 반환

**🟢 GREEN: Implement to Make Tests Pass (TDD-2.1)**
- [x] **Task 2.1**: URL 변환 함수 구현
  - File(s): `src/eazy/crawler/url_resolver.py`
  - Goal: Test 2.1 통과 → ✅ 6/6 passed
  - Details: `resolve_url(base_url: str, href: str) -> str | None` 구현

**🔵 REFACTOR (TDD-2.1)**
- [x] **Task 2.1R**: URL 변환 리팩토링
  - Files: `src/eazy/crawler/url_resolver.py`
  - Goal: 코드 품질 개선 → ✅ 6/6 passed (이미 최적 상태)

**🔴 RED: Write Failing Tests First (TDD-2.2: URL 정규화)**
- [x] **Test 2.2**: URL 정규화 단위 테스트 작성
  - File(s): `tests/unit/crawler/test_url_resolver.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ ImportError 확인
  - Details: 테스트 케이스:
    - fragment 제거 (url#section → url)
    - trailing slash 정규화
    - scheme/host 소문자 변환
    - 기본 포트 제거 (:80, :443)
    - 쿼리 파라미터 키 기준 정렬
    - 비표준 포트 유지 (:8080)

**🟢 GREEN: Implement to Make Tests Pass (TDD-2.2)**
- [x] **Task 2.2**: URL 정규화 함수 구현
  - File(s): `src/eazy/crawler/url_resolver.py`
  - Goal: Test 2.2 통과 → ✅ 13/13 passed
  - Details: `normalize_url(url: str) -> str` 구현

**🔵 REFACTOR (TDD-2.2)**
- [x] **Task 2.2R**: URL 정규화 리팩토링
  - Files: `src/eazy/crawler/url_resolver.py`
  - Goal: URL 정규화 로직 최적화 → ✅ 13/13 passed (이미 최적 상태)

**🔴 RED: Write Failing Tests First (TDD-2.3: 스코프 필터링)**
- [x] **Test 2.3**: 스코프 필터링 단위 테스트 작성
  - File(s): `tests/unit/crawler/test_url_resolver.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ ImportError 확인
  - Details: 테스트 케이스:
    - 같은 도메인 → True
    - 다른 도메인 → False
    - 서브도메인 포함 옵션
    - 경로 접두사 필터
    - 제외 패턴 (*.pdf, /admin/*)

**🟢 GREEN: Implement to Make Tests Pass (TDD-2.3)**
- [x] **Task 2.3**: 스코프 필터링 함수 구현
  - File(s): `src/eazy/crawler/url_resolver.py`
  - Goal: Test 2.3 통과 → ✅ 20/20 passed
  - Details: `is_in_scope(url: str, config: CrawlConfig) -> bool` 구현

**🔵 REFACTOR (TDD-2.3)**
- [x] **Task 2.3R**: 스코프 필터링 리팩토링
  - Files: `src/eazy/crawler/url_resolver.py`
  - Goal: 코드 품질 개선 → ✅ 20/20 passed (이미 최적 상태)

#### Commits
```
test(crawler): add failing tests for URL resolution
feat(crawler): implement URL resolution
refactor(crawler): improve URL resolution code quality
test(crawler): add failing tests for URL normalization
feat(crawler): implement URL normalization
refactor(crawler): optimize URL normalization
test(crawler): add failing tests for scope filtering
feat(crawler): implement scope filtering
refactor(crawler): improve scope filtering code quality
```

#### Quality Gate ✋

**⚠️ STOP: Phase 4 진행 전 모든 체크 항목을 통과해야 함**

**TDD Compliance** (CRITICAL):
- [x] **Red Phase**: 테스트를 먼저 작성하고 실패 확인 (ModuleNotFoundError/ImportError)
- [x] **Green Phase**: 최소 코드로 테스트 통과 (20/20 passed)
- [x] **Refactor Phase**: 테스트 통과 유지하면서 코드 개선
- [x] **Coverage Check**: 커버리지 요구사항 충족 (96%, 목표 80%+)
  ```bash
  # 커버리지 확인
  uv run pytest tests/unit/crawler/test_url_resolver.py --cov=eazy.crawler.url_resolver --cov-report=term-missing
  # Result: 52 statements, 2 missed, 96% coverage
  ```

**Build & Tests**:
- [x] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [x] **All Tests Pass**: 100% 테스트 통과 (62/62 전체, 20/20 url_resolver, 스킵 없음)
- [x] **Test Performance**: 테스트 스위트 0.07초 완료
- [x] **No Flaky Tests**: 테스트 일관 통과 확인

**Code Quality**:
- [x] **Linting**: 린팅 에러/경고 없음 (ruff check passed)
- [x] **Formatting**: 프로젝트 표준에 맞는 포맷팅 (ruff format passed)
- [x] **Type Safety**: 모든 함수 시그니처 타입 힌트 적용
- [x] **Static Analysis**: 정적 분석 도구 심각 이슈 없음

**Security & Performance**:
- [x] **Dependencies**: 알려진 보안 취약점 없음 (stdlib만 사용)
- [x] **Performance**: 성능 저하 없음
- [x] **Memory**: 메모리 누수/자원 이슈 없음
- [x] **Error Handling**: 빈 href, fragment-only 등 엣지 케이스 처리

**Documentation**:
- [x] **Code Comments**: Google 스타일 docstring 추가
- [x] **API Docs**: 공개 인터페이스 문서화 (모든 함수 docstring)
- [x] **README**: N/A (Phase 3)

**Manual Testing**:
- [x] **Functionality**: 기능 정상 동작 확인
- [x] **Edge Cases**: 경계 조건 테스트 완료
- [x] **Error States**: 에러 처리 검증 완료

**Validation Commands**:
```bash
# 테스트 실행
uv run pytest tests/unit/crawler/test_url_resolver.py -v

# 커버리지 확인
uv run pytest tests/unit/crawler/test_url_resolver.py --cov=eazy.crawler.url_resolver --cov-report=term-missing

# 린팅
uv run ruff check src/eazy/crawler/url_resolver.py tests/unit/crawler/test_url_resolver.py

# 포맷팅 확인
uv run ruff format --check src/eazy/crawler/url_resolver.py tests/unit/crawler/test_url_resolver.py

# 전체 회귀 테스트
uv run pytest --cov=src/eazy --cov-report=term-missing
```

**Manual Test Checklist**:
- [x] 다양한 상대 URL 변환 결과 확인
- [x] 정규화 후 동일 URL 중복 제거 확인
- [x] 도메인 외부 URL 정확히 필터링되는지 확인

---

### Phase 4: Robots.txt Parser
**Goal**: robots.txt 파싱 및 URL 허용/차단 판단
**Status**: ✅ Complete

#### Tasks

**🔴 RED: Write Failing Tests First (TDD-3.1: robots.txt 파싱)**
- [x] **Test 3.1**: robots.txt 파싱 단위 테스트 작성
  - File(s): `tests/unit/crawler/test_robots_parser.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ ModuleNotFoundError 확인
  - Details: 테스트 케이스:
    - 기본 User-agent/Disallow 파싱
    - 빈 robots.txt 처리
    - 주석(#) 무시
    - 다중 User-agent 블록
    - Allow/Disallow 우선순위
    - Crawl-delay 파싱

**🟢 GREEN: Implement to Make Tests Pass (TDD-3.1)**
- [x] **Task 3.1**: RobotsParser 클래스 구현
  - File(s): `src/eazy/crawler/robots_parser.py`
  - Goal: Test 3.1 통과 → ✅ 7/7 passed
  - Details: `RobotsParser` 클래스 (robots.txt 파싱 기능)

**🔵 REFACTOR (TDD-3.1)**
- [x] **Task 3.1R**: robots.txt 파싱 리팩토링
  - Files: `src/eazy/crawler/robots_parser.py`
  - Goal: 코드 품질 개선 → ✅ 7/7 passed (ruff format 적용)

**🔴 RED: Write Failing Tests First (TDD-3.2: URL 허용 판단)**
- [x] **Test 3.2**: URL 허용/차단 판단 단위 테스트 작성
  - File(s): `tests/unit/crawler/test_robots_parser.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ AttributeError 확인
  - Details: 테스트 케이스:
    - 규칙 없음 → 허용
    - Disallow 경로 → 차단
    - Allow 경로 → 허용
    - 와일드카드(*) 패턴
    - 특정 User-agent 규칙

**🟢 GREEN: Implement to Make Tests Pass (TDD-3.2)**
- [x] **Task 3.2**: URL 허용 판단 메서드 구현
  - File(s): `src/eazy/crawler/robots_parser.py`
  - Goal: Test 3.2 통과 → ✅ 12/12 passed
  - Details: `is_allowed(url: str, user_agent: str) -> bool` 구현

**🔵 REFACTOR (TDD-3.2)**
- [x] **Task 3.2R**: URL 허용 판단 리팩토링
  - Files: `src/eazy/crawler/robots_parser.py`
  - Goal: URL 허용 판단 로직 최적화 → ✅ 12/12 passed (_match_pattern 간소화)

#### Commits
```
test(crawler): add failing tests for robots.txt parsing
feat(crawler): implement robots.txt parser
refactor(crawler): improve robots parser code quality
test(crawler): add failing tests for URL allow/disallow check
feat(crawler): implement URL permission checking
refactor(crawler): optimize URL permission logic
```

#### Quality Gate ✋

**⚠️ STOP: Phase 5 진행 전 모든 체크 항목을 통과해야 함**

**TDD Compliance** (CRITICAL):
- [x] **Red Phase**: 테스트를 먼저 작성하고 실패 확인 (ModuleNotFoundError/AttributeError)
- [x] **Green Phase**: 최소 코드로 테스트 통과 (12/12 passed)
- [x] **Refactor Phase**: 테스트 통과 유지하면서 코드 개선
- [x] **Coverage Check**: 커버리지 요구사항 충족 (93%, 목표 80%+)
  ```bash
  # 커버리지 확인
  uv run pytest tests/unit/crawler/test_robots_parser.py --cov=eazy.crawler.robots_parser --cov-report=term-missing
  # Result: 74 statements, 5 missed, 93% coverage
  ```

**Build & Tests**:
- [x] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [x] **All Tests Pass**: 100% 테스트 통과 (74/74 전체, 12/12 robots_parser, 스킵 없음)
- [x] **Test Performance**: 테스트 스위트 0.09초 완료
- [x] **No Flaky Tests**: 테스트 일관 통과 확인

**Code Quality**:
- [x] **Linting**: 린팅 에러/경고 없음 (ruff check passed)
- [x] **Formatting**: 프로젝트 표준에 맞는 포맷팅 (ruff format passed)
- [x] **Type Safety**: 모든 함수 시그니처 타입 힌트 적용
- [x] **Static Analysis**: 정적 분석 도구 심각 이슈 없음

**Security & Performance**:
- [x] **Dependencies**: 알려진 보안 취약점 없음 (stdlib만 사용: re, urllib.parse)
- [x] **Performance**: 성능 저하 없음
- [x] **Memory**: 메모리 누수/자원 이슈 없음
- [x] **Error Handling**: 빈 robots.txt, 잘못된 Crawl-delay 등 엣지 케이스 처리

**Documentation**:
- [x] **Code Comments**: Google 스타일 docstring 추가
- [x] **API Docs**: 공개 인터페이스 문서화 (모든 메서드 docstring)
- [x] **README**: N/A (Phase 4)

**Manual Testing**:
- [x] **Functionality**: 기능 정상 동작 확인
- [x] **Edge Cases**: 경계 조건 테스트 완료
- [x] **Error States**: 에러 처리 검증 완료

**Validation Commands**:
```bash
# 테스트 실행
uv run pytest tests/unit/crawler/test_robots_parser.py -v

# 커버리지 확인
uv run pytest tests/unit/crawler/test_robots_parser.py --cov=eazy.crawler.robots_parser --cov-report=term-missing

# 린팅
uv run ruff check src/eazy/crawler/robots_parser.py tests/unit/crawler/test_robots_parser.py

# 포맷팅 확인
uv run ruff format --check src/eazy/crawler/robots_parser.py tests/unit/crawler/test_robots_parser.py

# 전체 회귀 테스트
uv run pytest --cov=src/eazy --cov-report=term-missing
```

**Manual Test Checklist**:
- [x] 실제 robots.txt 예시 파싱 결과 확인
- [x] Googlebot vs * User-agent 규칙 분리 확인
- [x] 와일드카드 패턴 매칭 정확성 확인

---

### Phase 5: HTTP Client
**Goal**: 비동기 HTTP 요청, 재시도, 딜레이, 에러 처리
**Status**: ✅ Complete

#### Tasks

**🔴 RED: Write Failing Tests First (TDD-4.1: 페이지 요청)**
- [x] **Test 4.1**: HTTP 클라이언트 단위 테스트 작성 (respx 모킹)
  - File(s): `tests/unit/crawler/test_http_client.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ ModuleNotFoundError 확인
  - Details: 테스트 케이스:
    - 200 성공 응답 처리
    - 404 에러 처리
    - 타임아웃 처리
    - 리다이렉트 추적
    - 연결 에러 처리
    - 재시도 로직 (최대 3회)
    - 요청 간 딜레이
    - 커스텀 User-Agent 헤더

**🟢 GREEN: Implement to Make Tests Pass (TDD-4.1)**
- [x] **Task 4.1**: HttpClient 클래스 구현
  - File(s): `src/eazy/crawler/http_client.py`
  - Goal: Test 4.1 통과 → ✅ 8/8 passed
  - Details: `HttpClient` 클래스 (httpx.AsyncClient 기반, 재시도/딜레이/에러 처리 포함)

**🔵 REFACTOR (TDD-4.1)**
- [x] **Task 4.1R**: HTTP 클라이언트 리팩토링
  - Files: `src/eazy/crawler/http_client.py`
  - Goal: 에러 처리 로직 개선, 코드 품질 향상 → ✅ 8/8 passed (import 정렬, ruff format 적용)

#### Commits
```
test(crawler): add failing tests for HTTP client
feat(crawler): implement async HTTP client with retry
refactor(crawler): fix HTTP client test import ordering
```

#### Quality Gate ✋

**⚠️ STOP: Phase 6 진행 전 모든 체크 항목을 통과해야 함**

**TDD Compliance** (CRITICAL):
- [x] **Red Phase**: 테스트를 먼저 작성하고 실패 확인 (ModuleNotFoundError)
- [x] **Green Phase**: 최소 코드로 테스트 통과 (8/8 passed)
- [x] **Refactor Phase**: 테스트 통과 유지하면서 코드 개선 (import 정렬)
- [x] **Coverage Check**: 커버리지 요구사항 충족 (96%, 목표 80%+)
  ```bash
  # 커버리지 확인
  uv run pytest tests/unit/crawler/test_http_client.py --cov=eazy.crawler.http_client --cov-report=term-missing
  # Result: 53 statements, 2 missed, 96% coverage
  ```

**Build & Tests**:
- [x] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [x] **All Tests Pass**: 100% 테스트 통과 (82/82 전체, 8/8 http_client, 스킵 없음)
- [x] **Test Performance**: 테스트 스위트 0.13초 완료
- [x] **No Flaky Tests**: 테스트 일관 통과 확인

**Code Quality**:
- [x] **Linting**: 린팅 에러/경고 없음 (ruff check passed)
- [x] **Formatting**: 프로젝트 표준에 맞는 포맷팅 (ruff format passed)
- [x] **Type Safety**: 모든 함수 시그니처 타입 힌트 적용
- [x] **Static Analysis**: 정적 분석 도구 심각 이슈 없음

**Security & Performance**:
- [x] **Dependencies**: 알려진 보안 취약점 없음 (httpx 사용)
- [x] **Performance**: 성능 저하 없음 (monotonic clock 기반 딜레이)
- [x] **Memory**: 메모리 누수/자원 이슈 없음 (async context manager로 클라이언트 생명주기 관리)
- [x] **Error Handling**: 5xx/timeout/connect 에러 재시도, 4xx 즉시 반환, error 필드로 에러 전달

**Documentation**:
- [x] **Code Comments**: Google 스타일 docstring 추가
- [x] **API Docs**: 공개 인터페이스 문서화 (HttpResponse, HttpClient, fetch 메서드)
- [x] **README**: N/A (Phase 5)

**Manual Testing**:
- [x] **Functionality**: 기능 정상 동작 확인
- [x] **Edge Cases**: 경계 조건 테스트 완료
- [x] **Error States**: 에러 처리 검증 완료

**Validation Commands**:
```bash
# 테스트 실행
uv run pytest tests/unit/crawler/test_http_client.py -v

# 커버리지 확인
uv run pytest tests/unit/crawler/test_http_client.py --cov=eazy.crawler.http_client --cov-report=term-missing

# 린팅
uv run ruff check src/eazy/crawler/http_client.py tests/unit/crawler/test_http_client.py

# 포맷팅 확인
uv run ruff format --check src/eazy/crawler/http_client.py tests/unit/crawler/test_http_client.py

# 전체 회귀 테스트
uv run pytest --cov=src/eazy --cov-report=term-missing
```

**Manual Test Checklist**:
- [x] respx 모킹으로 다양한 HTTP 상태 코드 응답 확인
- [x] 재시도 로직이 정확히 3회까지 동작하는지 확인
- [x] 타임아웃 설정이 올바르게 적용되는지 확인

---

### Phase 6: Sitemap & Exporter
**Goal**: 크롤링 결과 사이트맵 구조화 및 JSON 출력
**Status**: ✅ Complete

#### Tasks

**🔴 RED: Write Failing Tests First (TDD-5.1: 사이트맵 구조)**
- [x] **Test 5.1**: 사이트맵 단위 테스트 작성
  - File(s): `tests/unit/crawler/test_sitemap.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ ModuleNotFoundError 확인
  - Details: 테스트 케이스:
    - 페이지 추가 및 조회
    - 트리 구조 (부모-자식 관계)
    - 깊이(depth) 추적
    - dict 변환
    - 통계 (총 페이지 수, 총 링크 수, 총 폼 수 등)

**🟢 GREEN: Implement to Make Tests Pass (TDD-5.1)**
- [x] **Task 5.1**: Sitemap 클래스 구현
  - File(s): `src/eazy/crawler/sitemap.py`
  - Goal: Test 5.1 통과 → ✅ 7/7 passed
  - Details: `Sitemap` 클래스 (페이지 추가, 트리 구조, 통계 기능)

**🔵 REFACTOR (TDD-5.1)**
- [x] **Task 5.1R**: 사이트맵 리팩토링
  - Files: `src/eazy/crawler/sitemap.py`
  - Goal: 코드 품질 개선 → ✅ 7/7 passed (ruff format 적용)

**🔴 RED: Write Failing Tests First (TDD-5.2: 결과 출력)**
- [x] **Test 5.2**: 결과 출력(Exporter) 단위 테스트 작성
  - File(s): `tests/unit/crawler/test_exporter.py`
  - Expected: 테스트 FAIL (구현 미존재) → ✅ ModuleNotFoundError 확인
  - Details: 테스트 케이스:
    - JSON 문자열 출력
    - 파일 저장 (tmp_path 활용)
    - URL 목록 포함 확인
    - 파라미터 목록 포함 확인
    - 엔드포인트 목록 포함 확인
    - 폼 데이터 포함 확인
    - 메타데이터(타임스탬프, 설정 등) 포함 확인

**🟢 GREEN: Implement to Make Tests Pass (TDD-5.2)**
- [x] **Task 5.2**: CrawlResultExporter 클래스 구현
  - File(s): `src/eazy/crawler/exporter.py`
  - Goal: Test 5.2 통과 → ✅ 7/7 passed
  - Details: `CrawlResultExporter` 클래스 (JSON 출력, 파일 저장 기능)

**🔵 REFACTOR (TDD-5.2)**
- [x] **Task 5.2R**: 결과 출력 리팩토링
  - Files: `src/eazy/crawler/exporter.py`
  - Goal: 출력 포맷 최적화 → ✅ 7/7 passed (이미 최적 상태)

#### Commits
```
test(crawler): add failing tests for sitemap structure
feat(crawler): implement sitemap class
refactor(crawler): improve sitemap code quality
test(crawler): add failing tests for result exporter
feat(crawler): implement crawl result exporter
refactor(crawler): optimize exporter output format
```

#### Quality Gate ✋

**⚠️ STOP: Phase 7 진행 전 모든 체크 항목을 통과해야 함**

**TDD Compliance** (CRITICAL):
- [x] **Red Phase**: 테스트를 먼저 작성하고 실패 확인 (ModuleNotFoundError)
- [x] **Green Phase**: 최소 코드로 테스트 통과 (14/14 passed)
- [x] **Refactor Phase**: 테스트 통과 유지하면서 코드 개선 (ruff format 적용)
- [x] **Coverage Check**: 커버리지 요구사항 충족 (sitemap 100%, exporter 100%, 목표 80%+)
  ```bash
  # 커버리지 확인
  uv run pytest tests/unit/crawler/test_sitemap.py --cov=eazy.crawler.sitemap --cov-report=term-missing
  # Result: 21 statements, 0 missed, 100% coverage
  uv run pytest tests/unit/crawler/test_exporter.py --cov=eazy.crawler.exporter --cov-report=term-missing
  # Result: 10 statements, 0 missed, 100% coverage
  ```

**Build & Tests**:
- [x] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [x] **All Tests Pass**: 100% 테스트 통과 (96/96 전체, 14/14 sitemap+exporter, 스킵 없음)
- [x] **Test Performance**: 테스트 스위트 0.12초 완료
- [x] **No Flaky Tests**: 테스트 일관 통과 확인

**Code Quality**:
- [x] **Linting**: 린팅 에러/경고 없음 (ruff check passed)
- [x] **Formatting**: 프로젝트 표준에 맞는 포맷팅 (ruff format passed)
- [x] **Type Safety**: 모든 함수 시그니처 타입 힌트 적용
- [x] **Static Analysis**: 정적 분석 도구 심각 이슈 없음

**Security & Performance**:
- [x] **Dependencies**: 알려진 보안 취약점 없음 (stdlib + pydantic만 사용)
- [x] **Performance**: 성능 저하 없음 (dict 기반 O(1) 조회)
- [x] **Memory**: 메모리 누수/자원 이슈 없음
- [x] **Error Handling**: get_page None 반환, get_children 빈 리스트 반환

**Documentation**:
- [x] **Code Comments**: Google 스타일 docstring 추가
- [x] **API Docs**: 공개 인터페이스 문서화 (Sitemap, CrawlResultExporter 모든 메서드)
- [x] **README**: N/A (Phase 6)

**Manual Testing**:
- [x] **Functionality**: 기능 정상 동작 확인
- [x] **Edge Cases**: 경계 조건 테스트 완료
- [x] **Error States**: 에러 처리 검증 완료

**Validation Commands**:
```bash
# 테스트 실행
uv run pytest tests/unit/crawler/test_sitemap.py tests/unit/crawler/test_exporter.py -v

# 커버리지 확인
uv run pytest tests/unit/crawler/test_sitemap.py --cov=eazy.crawler.sitemap --cov-report=term-missing
uv run pytest tests/unit/crawler/test_exporter.py --cov=eazy.crawler.exporter --cov-report=term-missing

# 린팅
uv run ruff check src/eazy/crawler/sitemap.py src/eazy/crawler/exporter.py tests/unit/crawler/test_sitemap.py tests/unit/crawler/test_exporter.py

# 포맷팅 확인
uv run ruff format --check src/eazy/crawler/sitemap.py src/eazy/crawler/exporter.py tests/unit/crawler/test_sitemap.py tests/unit/crawler/test_exporter.py

# 전체 회귀 테스트
uv run pytest --cov=src/eazy --cov-report=term-missing
```

**Manual Test Checklist**:
- [x] Sitemap 트리 구조가 올바른 부모-자식 관계인지 확인
- [x] JSON 출력 스키마가 PRD 요구사항 충족하는지 확인
- [x] 파일 저장 후 재로드 시 데이터 일관성 확인

---

### Phase 7: Crawler Engine 통합
**Goal**: 모든 컴포넌트를 통합한 크롤링 엔진 완성
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First (TDD-6.1: 기본 크롤링)**
- [ ] **Test 6.1**: 기본 크롤링 통합 테스트 작성
  - File(s): `tests/integration/crawler/test_crawler_engine.py`
  - Expected: 테스트 FAIL (엔진 미구현)
  - Details: 테스트 케이스:
    - 단일 페이지 크롤링
    - 링크 추적 (발견된 링크 → 후속 크롤링)
    - 중복 URL 방지
    - 방문 기록 유지

**🟢 GREEN: Implement to Make Tests Pass (TDD-6.1)**
- [ ] **Task 6.1**: CrawlerEngine 기본 구현
  - File(s): `src/eazy/crawler/engine.py`
  - Goal: Test 6.1 통과
  - Details: `CrawlerEngine.crawl()` 메서드 기본 구현 (단일 페이지 크롤링 + 링크 추적)

**🔵 REFACTOR (TDD-6.1)**
- [ ] **Task 6.1R**: 크롤링 엔진 구조 리팩토링
  - Files: `src/eazy/crawler/engine.py`
  - Goal: 엔진 구조 개선

**🔴 RED: Write Failing Tests First (TDD-6.2: 크롤링 설정)**
- [ ] **Test 6.2**: 크롤링 설정 적용 통합 테스트 작성
  - File(s): `tests/integration/crawler/test_crawler_engine.py`
  - Expected: 테스트 FAIL (설정 적용 미구현)
  - Details: 테스트 케이스:
    - 최대 깊이 제한
    - 도메인 스코프 적용
    - robots.txt 준수
    - 최대 페이지 수 제한
    - 제외 패턴 적용

**🟢 GREEN: Implement to Make Tests Pass (TDD-6.2)**
- [ ] **Task 6.2**: 크롤링 설정 적용 로직 구현
  - File(s): `src/eazy/crawler/engine.py`
  - Goal: Test 6.2 통과
  - Details: CrawlConfig 기반 설정 적용 (깊이 제한, 스코프, robots.txt, 페이지 수 제한, 제외 패턴)

**🔵 REFACTOR (TDD-6.2)**
- [ ] **Task 6.2R**: 설정 로직 리팩토링
  - Files: `src/eazy/crawler/engine.py`
  - Goal: 설정 적용 로직 최적화

**🔴 RED: Write Failing Tests First (TDD-6.3: 전체 통합 테스트)**
- [ ] **Test 6.3**: 전체 워크플로우 통합 테스트 작성
  - File(s): `tests/integration/crawler/test_crawler_engine.py`
  - Expected: 테스트 FAIL (전체 통합 미완성)
  - Details: 테스트 케이스:
    - 전체 워크플로우 (URL 입력 → 크롤링 → JSON 출력)
    - robots.txt 포함 시나리오
    - 출력 JSON 스키마 검증
    - 에러 핸들링 (존재하지 않는 URL, 네트워크 에러)

**🟢 GREEN: Implement to Make Tests Pass (TDD-6.3)**
- [ ] **Task 6.3**: 전체 통합 완성
  - File(s): `src/eazy/crawler/engine.py`
  - Goal: Test 6.3 통과
  - Details: 전체 워크플로우 통합 (URL 입력 → 크롤링 → Sitemap 구축 → JSON 출력)

**🔵 REFACTOR (TDD-6.3)**
- [ ] **Task 6.3R**: 최종 리팩토링
  - Files: `src/eazy/crawler/engine.py` 및 관련 모듈 전체
  - Goal: 최종 코드 품질 개선
  - Checklist:
    - [ ] 중복 코드 제거 (DRY 원칙)
    - [ ] 네이밍 명확성 개선
    - [ ] 재사용 가능한 컴포넌트 추출
    - [ ] 인라인 문서화 추가
    - [ ] 성능 최적화 (필요 시)

#### Commits
```
test(crawler): add failing tests for basic crawling
feat(crawler): implement basic crawler engine
refactor(crawler): improve crawler engine structure
test(crawler): add failing tests for crawl configuration
feat(crawler): implement crawl configuration handling
refactor(crawler): optimize configuration logic
test(crawler): add failing integration tests for full workflow
feat(crawler): complete full crawling workflow integration
refactor(crawler): final code quality improvements
```

#### Quality Gate ✋

**⚠️ STOP: 최종 완료 선언 전 모든 체크 항목을 통과해야 함**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: 테스트를 먼저 작성하고 실패 확인
- [ ] **Green Phase**: 최소 코드로 테스트 통과
- [ ] **Refactor Phase**: 테스트 통과 유지하면서 코드 개선
- [ ] **Coverage Check**: 전체 커버리지 80%+ 달성

**Build & Tests**:
- [ ] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [ ] **All Tests Pass**: 100% 테스트 통과 (스킵 없음)
- [ ] **Test Performance**: 테스트 스위트 허용 시간 내 완료
- [ ] **No Flaky Tests**: 테스트 3회 이상 일관 통과

**Code Quality**:
- [ ] **Linting**: 린팅 에러/경고 없음
- [ ] **Formatting**: 프로젝트 표준에 맞는 포맷팅
- [ ] **Type Safety**: 타입 체크 통과 (해당 시)
- [ ] **Static Analysis**: 정적 분석 도구 심각 이슈 없음

**Security & Performance**:
- [ ] **Dependencies**: 알려진 보안 취약점 없음
- [ ] **Performance**: 성능 저하 없음
- [ ] **Memory**: 메모리 누수/자원 이슈 없음
- [ ] **Error Handling**: 적절한 에러 처리 구현

**Documentation**:
- [ ] **Code Comments**: 복잡한 로직 문서화
- [ ] **API Docs**: 공개 인터페이스 문서화
- [ ] **README**: 필요 시 사용 방법 업데이트

**Manual Testing**:
- [ ] **Functionality**: 기능 정상 동작 확인
- [ ] **Edge Cases**: 경계 조건 테스트 완료
- [ ] **Error States**: 에러 처리 검증 완료

**Validation Commands**: Phase 1 검증 커맨드 참조

**Manual Test Checklist**:
- [ ] respx로 멀티페이지 사이트 모킹 후 전체 크롤링 확인
- [ ] 깊이 제한이 정확히 적용되는지 확인
- [ ] JSON 출력에 모든 필수 필드(URLs, params, endpoints, forms, metadata) 포함 확인
- [ ] robots.txt 차단 경로가 크롤링에서 제외되는지 확인

---

## ⚠️ Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| 정규식으로 복잡한 HTML 파싱 실패 | Medium | Medium | 주요 패턴 위주로 범위 한정, Phase 2에서 edge case 충분히 테스트 |
| httpx/respx 버전 호환성 이슈 | Low | High | pyproject.toml에 버전 고정, CI에서 검증 |
| 비동기 테스트 불안정 (flaky) | Medium | Low | pytest-asyncio strict mode, 타임아웃 여유 설정 |
| 크롤링 엔진 통합 시 컴포넌트 간 인터페이스 불일치 | Low | High | Pydantic 모델로 인터페이스 계약 보장, Phase 1에서 모델 확정 |

---

## 🔄 Rollback Strategy

### If Phase 1 Fails
**복원 단계**:
- `git checkout main` 으로 복원
- 브랜치 삭제: `git branch -D feature/req-001-regex-crawler`

### If Phase 2~6 Fails
**복원 단계**:
- 해당 Phase 직전 커밋으로 복원: `git reset --soft HEAD~N`
- 실패 원인 분석 후 재시도

### If Phase 7 Fails
**복원 단계**:
- Phase 6 완료 상태로 복원
- 통합 로직만 재작성

---

## 📊 Progress Tracking

### Completion Status
- **Phase 1**: ✅ 100% (2026-02-12 완료)
- **Phase 2**: ✅ 100% (2026-02-12 완료)
- **Phase 3**: ✅ 100% (2026-02-12 완료)
- **Phase 4**: ✅ 100% (2026-02-12 완료)
- **Phase 5**: ✅ 100% (2026-02-12 완료)
- **Phase 6**: ✅ 100% (2026-02-13 완료)
- **Phase 7**: ⏳ 0%

**Overall Progress**: ~86% complete (6/7 phases)

### Time Tracking
| Phase | Estimated | Actual | Variance |
|-------|-----------|--------|----------|
| Phase 1 | - | 2026-02-12 | - |
| Phase 2 | - | 2026-02-12 | - |
| Phase 3 | - | 2026-02-12 | - |
| Phase 4 | - | 2026-02-12 | - |
| Phase 5 | - | 2026-02-12 | - |
| Phase 6 | - | 2026-02-13 | - |
| Phase 7 | - | - | - |
| **Total** | - | - | - |

---

## 📝 Notes & Learnings

### Implementation Notes
- Pydantic v2의 `ConfigDict(frozen=True)`를 CrawlConfig에 적용하여 설정 불변성 보장
- `Field(default_factory=list)` 패턴으로 mutable default 문제 방지
- Python 3.14 환경에서 테스트 수행 (3.12+ 호환 확인)
- Google 스타일 docstring으로 Attributes 섹션 추가 (CLAUDE.md 컨벤션)
- `max_depth="not_a_number"` 입력 시 Pydantic v2가 정상적으로 ValidationError 발생 확인
- (Phase 2) 모든 정규식을 모듈 레벨 `re.compile()` 상수로 정의하여 반복 호출 시 성능 최적화
- (Phase 2) 4개 순수 함수로 구현: extract_links, extract_forms, extract_buttons, extract_api_endpoints
- (Phase 2) Phase 1 Pydantic 모델(FormData, ButtonInfo, EndpointInfo) 재사용으로 타입 안전성 확보
- (Phase 2) 25개 테스트, regex_parser.py 100% 커버리지 달성
- (Phase 2) `str.startswith(tuple)` 패턴으로 다중 프로토콜 필터링 간결하게 구현
- (Phase 3) 3개 순수 함수로 구현: resolve_url, normalize_url, is_in_scope
- (Phase 3) Python stdlib만 사용 (urllib.parse, fnmatch) — 외부 의존성 없음
- (Phase 3) CrawlConfig 모델 재사용으로 is_in_scope에서 타입 안전성 확보
- (Phase 3) 20개 테스트, url_resolver.py 96% 커버리지 달성
- (Phase 3) `--cov` 경로는 패키지 이름 (`eazy.crawler.url_resolver`) 사용해야 함 (`src/` 접두사 X)
- (Phase 4) 클래스 기반 구현 (RobotsParser) — 파싱 결과 상태 유지 필요
- (Phase 4) stdlib만 사용 (re, urllib.parse) — 외부 의존성 없음
- (Phase 4) robots.txt 패턴을 정규식으로 변환: `*` → `.*`, `$` → `$`, 나머지 re.escape
- (Phase 4) 우선순위: 더 긴(구체적) 패턴 우선, 같은 길이면 Allow 우선 (Google 표준)
- (Phase 4) 12개 테스트, robots_parser.py 93% 커버리지 달성
- (Phase 5) 클래스 기반 구현 (HttpClient) — async context manager로 httpx.AsyncClient 생명주기 관리
- (Phase 5) HttpResponse는 frozen dataclass (Pydantic 불필요 — 직렬화 안 함)
- (Phase 5) 에러 시 예외 대신 error 필드 반환 — 호출자가 예외 처리 없이 판단 가능
- (Phase 5) 5xx/timeout/connect만 재시도, 4xx는 즉시 반환
- (Phase 5) request_delay는 time.monotonic() 기반 _last_request_time 추적
- (Phase 5) 8개 테스트, http_client.py 96% 커버리지 달성
- (Phase 6) Sitemap: dict[str, PageResult] 기반 O(1) URL 조회, parent_url로 트리 관계 추적
- (Phase 6) Exporter: CrawlResult.model_dump(mode="json") + json.dumps(indent=2) 조합
- (Phase 6) 동기 코드 (async 불필요) — 순수 데이터 구조/직렬화 처리
- (Phase 6) stdlib + pydantic만 사용 — 외부 의존성 없음
- (Phase 6) 14개 테스트, sitemap.py 100% + exporter.py 100% 커버리지 달성

### Blockers Encountered
- (없음)

### Improvements for Future Plans
- Phase 3 (URL Resolver) 구현 시 CrawlConfig.target_url에 URL 유효성 검증 추가 고려
- datetime 라운드트립 정밀도 테스트 추가 고려 (현재 Pydantic이 ISO 8601로 처리)
- template literal URL 패턴 (`${baseUrl}/api/...`) 지원은 Phase 2+ Smart Crawling에서 고려

---

## 📚 References

### Documentation
- PRD 문서: `plan/PRD.md`
- Python httpx 공식 문서: https://www.python-httpx.org/
- Pydantic v2 공식 문서: https://docs.pydantic.dev/latest/
- respx 공식 문서: https://lundberg.github.io/respx/
- ruff 공식 문서: https://docs.astral.sh/ruff/

### Related Issues
- (아직 없음)

---

## ✅ Final Checklist

**Before marking plan as COMPLETE**:
- [ ] 모든 Phase 완료 및 Quality Gate 통과
- [ ] 전체 통합 테스트 수행
- [ ] 문서 업데이트
- [ ] 전체 커버리지 80%+ 달성
- [ ] 보안 리뷰 완료
- [ ] 모든 이해관계자 알림
- [ ] 계획 문서 아카이브

---

**Plan Status**: 🔄 In Progress
**Next Action**: Phase 2 - HTML Regex Parser
**Blocked By**: None
