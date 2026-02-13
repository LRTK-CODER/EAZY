# Implementation Plan: REQ-009 CLI 인터페이스

**Status**: 🔄 In Progress
**Started**: 2026-02-13
**Last Updated**: 2026-02-13
**Estimated Completion**: 2026-02-14

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
CLI 인터페이스(REQ-009)로 터미널에서 크롤링 및 스캔을 실행할 수 있게 한다.
Typer + Rich 기반으로 기존 async CrawlerEngine을 래핑하며, `eazy crawl <url>`, `eazy scan <url>`,
출력 포맷팅(JSON/text/table), 프로그레스 표시, 파일 내보내기를 지원한다.

### Success Criteria
- [ ] `eazy crawl <url>` 이 크롤링을 실행하고 결과를 출력한다
- [ ] `eazy scan <url>` 커맨드 구조가 존재한다 (크롤러 + 스캐너 placeholder)
- [ ] `--depth`, `--include-subdomains`, `--output`, `--format` 옵션이 정상 동작한다
- [ ] 크롤링 실행 중 프로그레스가 표시된다
- [ ] JSON/text/table 출력 포맷이 올바르게 렌더링된다
- [ ] `eazy resume <scan-id>` 커맨드가 안내 메시지와 함께 존재한다
- [ ] `--help`가 모든 커맨드와 옵션의 문서를 표시한다
- [ ] CLI 모듈 테스트 커버리지 >= 80%

### User Impact
보안 전문가가 터미널에서 직관적인 커맨드로 EAZY를 실행할 수 있어, 스크립트, CI/CD 파이프라인, 수동 워크플로우에 통합 가능하다.

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| Typer CLI 프레임워크 | 타입 힌트 기반, 자동 --help 생성, Rich 통합 내장, Click 위에 구축 | Click 단독 대비 약간 덜 성숙 |
| Rich 디스플레이 | 프로그레스 바, 테이블, 패널 - REQ-009 표시 요구사항 전부 충족 | 추가 의존성 |
| asyncio.run() 래퍼 | Typer는 sync 전용; async 호출 래핑은 표준 패턴 | 테스트에서 약간의 복잡성 |
| Formatter 프로토콜 클래스 | 출력 포맷의 깔끔한 분리, 새 포맷 추가 용이 | 작은 추상화 오버헤드 |

---

## 📦 Dependencies

### Required Before Starting
- [x] CrawlerEngine 모듈 존재 및 테스트 완료 (REQ-001)
- [x] Pydantic 모델 정의 완료 (CrawlConfig, CrawlResult, PageResult)

### External Dependencies
- typer >= 0.9.0 (CLI 프레임워크, Click 포함)
- rich >= 13.0 (터미널 포맷팅, 프로그레스 바, 테이블)

---

## 🧪 Test Strategy

### Testing Approach
**TDD Principle**: Write tests FIRST, then implement to make them pass

CLI 테스트는 `typer.testing.CliRunner`로 커맨드를 호출하고 exit code, stdout 출력, 부수효과를 검증한다.
Async 크롤러 호출은 `unittest.mock.AsyncMock`으로 모킹한다.

### Test Pyramid for This Feature
| Test Type | Coverage Target | Purpose |
|-----------|-----------------|---------|
| **Unit Tests** | ≥80% | CLI 커맨드, 포맷터, 디스플레이 헬퍼 |
| **Integration Tests** | Critical paths | CLI -> CrawlerEngine -> mocked HTTP |

### Test File Organization
```
tests/
├── conftest.py                              # 공유 fixture (mock_crawl_result, cli_runner)
├── unit/
│   └── cli/
│       ├── __init__.py
│       ├── test_app.py                      # 앱 구조, --help, --version
│       ├── test_crawl_command.py            # crawl 커맨드 옵션 및 실행
│       ├── test_scan_command.py             # scan 커맨드 구조
│       ├── test_formatters.py              # 출력 포맷터 테스트
│       └── test_display.py                 # 디스플레이 헬퍼 테스트
└── integration/
    └── cli/
        ├── __init__.py
        └── test_cli_crawl_integration.py   # 전체 크롤 플로우 (mocked HTTP)
```

### Coverage Requirements by Phase
- **Phase 1 (Foundation)**: CLI 앱 구조 단위 테스트 (≥80%)
- **Phase 2 (Crawl Command)**: crawl 커맨드 옵션 + 실행 테스트 (≥80%)
- **Phase 3 (Formatters)**: 포맷터 + 디스플레이 테스트 (≥80%)
- **Phase 4 (Scan/Integration)**: scan 커맨드 + 통합 테스트 (≥80%)

### Test Naming Convention
```python
# 파일명: test_{모듈명}.py
# 클래스명: Test{컴포넌트명}
# 함수명: test_{행위}_{조건}_{기대결과}
# 패턴: Arrange -> Act -> Assert
```

---

## 🚀 Implementation Phases

### Phase 1: CLI 앱 기본 구조
**Goal**: Typer 앱에 --help, --version, crawl/scan 서브커맨드 등록 및 엔트리 포인트 설정
**Estimated Time**: 2 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**
- [ ] **Test 1.1**: 기존 CLI 앱 구조 테스트 확인 및 실패 검증
  - File(s): `tests/unit/cli/test_app.py` (이미 존재 - 9개 테스트, 3개 클래스)
  - Expected: Tests FAIL (red) - `eazy.cli.app` 모듈이 아직 없어 ImportError
  - Details: 기존 테스트가 다음을 커버하는지 확인하고, 부족한 케이스 보강:
    - `eazy --help` exit code 0, "Usage" 텍스트 포함
    - `eazy --version` exit code 0, "0.1.0" 표시
    - `eazy` 인수 없이 실행 시 help 텍스트 표시
    - `crawl` 서브커맨드가 --help 출력에 등록됨
    - `scan` 서브커맨드가 --help 출력에 등록됨
- [ ] **Test 1.5**: 공유 테스트 fixture 생성
  - File(s): `tests/conftest.py`
  - Expected: fixture 정의만 존재 (테스트 실행의 전제 조건)
  - Details:
    - `cli_runner` fixture (CliRunner 인스턴스)
    - `mock_page_result` fixture (현실적 데이터의 PageResult)
    - `mock_crawl_result` fixture (pages, statistics 포함 CrawlResult)

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 1.2**: pyproject.toml에 의존성 추가
  - File(s): `pyproject.toml`
  - Goal: Make Test 1.1 pass with minimal code
  - Details:
    - `typer>=0.9.0`, `rich>=13.0`을 `[project.dependencies]`에 추가
    - `[project.scripts] eazy = "eazy.cli:main"` 엔트리 포인트 추가
    - `uv sync` 실행하여 설치
- [ ] **Task 1.3**: CLI 패키지 및 메인 엔트리 포인트 생성
  - File(s): `src/eazy/cli/__init__.py`
  - Goal: `main()` 함수가 `app()`를 호출
  - Details: 패키지 초기화, `main()` 함수 정의
- [ ] **Task 1.4**: Typer 앱 생성 및 서브커맨드 등록
  - File(s): `src/eazy/cli/app.py`
  - Goal: Make Test 1.1 pass
  - Details:
    - Typer 앱 인스턴스 생성 (help 텍스트 포함)
    - `--version` 콜백 추가
    - `crawl`, `scan` 빈 스텁 커맨드 등록
**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 1.6**: 코드 품질 리팩토링
  - Files: 이 Phase의 모든 새 코드 검토
  - Goal: 테스트를 깨뜨리지 않고 설계 개선
  - Checklist:
    - [ ] Google 스타일 docstring 추가
    - [ ] 모든 함수 시그니처에 타입 힌트
    - [ ] Ruff lint/format 통과 확인

#### Quality Gate ✋

**⚠️ STOP: Do NOT proceed to Phase 2 until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Test coverage meets requirements
  ```bash
  uv run pytest --cov=src/eazy/cli --cov-report=term-missing tests/unit/cli/test_app.py
  ```

**Build & Tests**:
- [ ] **All Tests Pass**: `uv run pytest tests/unit/cli/test_app.py -v`
- [ ] **No Regressions**: `uv run pytest tests/ -v`
- [ ] **No Flaky Tests**: 3회 반복 실행 시 일관된 결과

**Code Quality**:
- [ ] **Linting**: `uv run ruff check src/eazy/cli/ tests/unit/cli/`
- [ ] **Formatting**: `uv run ruff format --check src/eazy/cli/ tests/unit/cli/`

**Security & Performance**:
- [ ] **Dependencies**: 새 의존성(typer, rich)에 알려진 보안 취약점 없음
- [ ] **Error Handling**: 적절한 에러 처리 구현

**Documentation**:
- [ ] **Code Comments**: 복잡한 로직에 주석
- [ ] **API Docs**: 공개 인터페이스 문서화 (docstring)

**Manual Testing**:
- [ ] **Functionality**: `uv run eazy --help` 가 crawl, scan 커맨드 포함 Usage 표시
- [ ] **Edge Cases**: `uv run eazy --version` 이 "0.1.0" 표시
- [ ] **Error States**: `uv run eazy crawl --help` 가 crawl 서브커맨드 help 표시

**Validation Commands**:
```bash
# Test Commands
uv run pytest tests/unit/cli/test_app.py -v

# Coverage Check
uv run pytest --cov=src/eazy/cli --cov-report=term-missing tests/unit/cli/test_app.py

# Code Quality
uv run ruff check src/eazy/cli/ tests/unit/cli/
uv run ruff format --check src/eazy/cli/ tests/unit/cli/

# No Regressions
uv run pytest tests/ -v
```

**Manual Test Checklist**:
- [ ] `uv run eazy --help` 이 Usage와 crawl/scan 커맨드를 표시
- [ ] `uv run eazy --version` 이 "0.1.0"을 표시
- [ ] `uv run eazy crawl --help` 가 crawl 서브커맨드 help를 표시

---

### Phase 2: Crawl 커맨드 핵심 기능
**Goal**: `eazy crawl <url>`이 모든 CrawlConfig 옵션으로 async 크롤링을 실행하고 결과를 출력
**Estimated Time**: 3 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**
- [ ] **Test 2.1**: crawl 커맨드 옵션 및 실행 단위 테스트
  - File(s): `tests/unit/cli/test_crawl_command.py`
  - Expected: Tests FAIL (red) - crawl 커맨드 미구현
  - Details: Test cases covering:
    - `eazy crawl http://example.com` 이 CrawlerEngine을 올바른 config로 호출
    - `--depth 5` 가 CrawlConfig.max_depth=5 설정
    - `--max-pages 100` 가 CrawlConfig.max_pages=100 설정
    - `--timeout 60` 가 CrawlConfig.timeout=60 설정
    - `--delay 0.5` 가 CrawlConfig.request_delay=0.5 설정
    - `--exclude "*.pdf"` 가 CrawlConfig.exclude_patterns에 추가
    - `--exclude` 반복 사용 시 여러 패턴 추가
    - `--user-agent "MyBot/1.0"` 가 CrawlConfig.user_agent 설정
    - `--no-respect-robots` 가 CrawlConfig.respect_robots=False 설정
    - `--include-subdomains` 가 CrawlConfig.include_subdomains=True 설정
    - `--output result.json` 이 결과를 파일에 저장
    - 빈 URL 입력 시 에러 메시지 표시
    - 크롤 결과가 stdout에 JSON으로 출력
  - Mocking: `@patch("eazy.cli.app.CrawlerEngine")` with AsyncMock

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 2.2**: crawl 커맨드 구현
  - File(s): `src/eazy/cli/app.py`
  - Goal: Make Test 2.1 pass with minimal code
  - Details:
    - positional `url` 인수 추가
    - CLI 옵션 -> CrawlConfig 필드 매핑:
      - `--depth` -> max_depth (default 3)
      - `--max-pages` -> max_pages
      - `--timeout` -> timeout (default 30)
      - `--delay` -> request_delay (default 0.0)
      - `--exclude` -> exclude_patterns (list, 반복 가능)
      - `--user-agent` -> user_agent
      - `--respect-robots/--no-respect-robots` -> respect_robots (default True)
      - `--include-subdomains` -> include_subdomains (default False)
      - `--retries` -> max_retries (default 3)
      - `--output` -> 출력 파일 경로
      - ~~`--format`~~: Phase 2에서는 미등록. 항상 JSON 출력. `--format` 옵션은 Phase 3에서 추가
    - `asyncio.run()`으로 `CrawlerEngine(config).crawl()` 호출
    - stdout에 JSON 결과 출력 (Phase 2에서는 JSON 전용, 포맷터는 Phase 3)
    - `--output` 시 CrawlResultExporter로 파일 저장

**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 2.3**: 코드 품질 리팩토링
  - Files: 이 Phase의 모든 새 코드 검토
  - Goal: 테스트를 깨뜨리지 않고 설계 개선
  - Checklist:
    - [ ] URL 유효성 검증 헬퍼 추출
    - [ ] 일관된 에러 메시지 포맷팅
    - [ ] 모든 함수에 docstring
    - [ ] 타입 힌트 완성

#### Quality Gate ✋

**⚠️ STOP: Do NOT proceed to Phase 3 until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Test coverage meets requirements
  ```bash
  uv run pytest --cov=src/eazy/cli --cov-report=term-missing tests/unit/cli/
  ```

**Build & Tests**:
- [ ] **All Tests Pass**: `uv run pytest tests/unit/cli/ -v`
- [ ] **No Regressions**: `uv run pytest tests/ -v`
- [ ] **No Flaky Tests**: 3회 반복 실행 시 일관된 결과

**Code Quality**:
- [ ] **Linting**: `uv run ruff check src/eazy/cli/ tests/unit/cli/`
- [ ] **Formatting**: `uv run ruff format --check src/eazy/cli/ tests/unit/cli/`

**Security & Performance**:
- [ ] **Error Handling**: 잘못된 URL, 네트워크 에러 등 적절히 처리
- [ ] **Performance**: async 크롤링이 sync 래퍼에서 정상 동작

**Documentation**:
- [ ] **Code Comments**: 복잡한 로직에 주석
- [ ] **API Docs**: 모든 CLI 옵션에 help 텍스트

**Manual Testing**:
- [ ] **Functionality**: `uv run eazy crawl http://example.com --depth 1` 실행 및 결과 출력
- [ ] **Edge Cases**: 잘못된 URL 입력 시 에러 메시지
- [ ] **Error States**: 네트워크 에러 시 적절한 메시지

**Validation Commands**:
```bash
# Test Commands
uv run pytest tests/unit/cli/ -v

# Coverage Check
uv run pytest --cov=src/eazy/cli --cov-report=term-missing tests/unit/cli/

# Code Quality
uv run ruff check src/eazy/cli/ tests/unit/cli/
uv run ruff format --check src/eazy/cli/ tests/unit/cli/

# No Regressions
uv run pytest tests/ -v
```

**Manual Test Checklist**:
- [ ] `uv run eazy crawl --help` 가 모든 옵션과 설명 표시
- [ ] `uv run eazy crawl http://example.com --depth 1` 이 결과 출력
- [ ] `uv run eazy crawl http://example.com --output test.json` 이 파일 생성

---

### Phase 3: 출력 포맷팅 & 프로그레스 표시
**Goal**: JSON/text/table 출력 포맷과 Rich 프로그레스 스피너
**Estimated Time**: 3 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**
- [ ] **Test 3.1**: 출력 포맷터 단위 테스트
  - File(s): `tests/unit/cli/test_formatters.py`
  - Expected: Tests FAIL (red) - formatters 모듈 미존재
  - Details: Test cases covering:
    - JsonFormatter: CrawlResult에서 유효한 JSON 문자열 출력
    - JsonFormatter: pages, statistics, config 포함 확인
    - TextFormatter: 통계 포함 사람이 읽기 쉬운 요약 출력
    - TextFormatter: URL, status code 포함 페이지 목록
    - TextFormatter: 페이지별 form 수, endpoint 수 표시
    - TableFormatter: Rich 렌더링 가능한 테이블 구조
    - TableFormatter: URL, Status, Depth, Links, Forms, Endpoints 컬럼
    - TableFormatter: 합계 요약 행
    - `format_result(result, format_type)` 가 올바른 포맷터로 디스패치

- [ ] **Test 3.2**: display 모듈 단위 테스트
  - File(s): `tests/unit/cli/test_display.py`
  - Expected: Tests FAIL (red) - display 모듈 미존재
  - Details: Test cases covering:
    - `create_progress_spinner()`가 유효한 Rich 객체 반환
    - `print_banner()`가 예외 없이 실행
    - `print_summary(result)`가 통계 포함 출력 생성

- [ ] **Test 3.3**: crawl 커맨드 포맷 옵션 통합 테스트
  - File(s): `tests/unit/cli/test_app.py` (추가)
  - Expected: Tests FAIL (red) - 포맷 옵션 미연결
  - Details: Test cases:
    - `eazy crawl` with `--format json` 이 유효한 JSON 출력
    - `eazy crawl` with `--format text` 가 텍스트 요약 출력
    - `eazy crawl` with `--format table` 이 테이블 출력
    - `--format` 미지정 시 기본 table 포맷 출력

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 3.3**: formatters 모듈 구현
  - File(s): `src/eazy/cli/formatters.py`
  - Goal: Make Test 3.1 pass with minimal code
  - Details:
    - `JsonFormatter.format(result: CrawlResult) -> str` - CrawlResultExporter 재사용
    - `TextFormatter.format(result: CrawlResult) -> str` - 플레인 텍스트 요약
    - `TableFormatter.format(result: CrawlResult) -> str` - Rich 테이블 (문자열 캡처)
    - `format_result(result, format_type: str) -> str` - 디스패처 함수
- [ ] **Task 3.4**: display 모듈 구현
  - File(s): `src/eazy/cli/display.py`
  - Goal: Make Test 3.2 pass
  - Details:
    - `create_progress_spinner()` - 크롤 진행 Rich 스피너
    - `print_banner()` - EAZY 배너/헤더
    - `print_summary(result: CrawlResult)` - 간략 통계 요약
- [ ] **Task 3.5**: 포맷터와 디스플레이를 crawl 커맨드에 연결
  - File(s): `src/eazy/cli/app.py`
  - Goal: `--format` 옵션으로 포맷터 선택, 스피너 표시
  - Details: crawl 커맨드에서 포맷터 호출, 스피너 표시/숨김

**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 3.6**: 코드 품질 리팩토링
  - Files: 이 Phase의 모든 새 코드 검토
  - Goal: 테스트를 깨뜨리지 않고 설계 개선
  - Checklist:
    - [ ] 포맷터 코드 DRY (공유 유틸리티 메서드)
    - [ ] 일관된 Rich 스타일링 (색상, 패널)
    - [ ] 모든 포맷터 클래스/메서드에 docstring

#### Quality Gate ✋

**⚠️ STOP: Do NOT proceed to Phase 4 until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Test coverage meets requirements
  ```bash
  uv run pytest --cov=src/eazy/cli --cov-report=term-missing
  ```

**Build & Tests**:
- [ ] **All Tests Pass**: `uv run pytest tests/unit/cli/ -v`
- [ ] **No Regressions**: `uv run pytest tests/ -v`
- [ ] **Coverage >= 80%**: CLI 모듈 커버리지 확인
- [ ] **No Flaky Tests**: 3회 반복 실행 시 일관된 결과

**Code Quality**:
- [ ] **Linting**: `uv run ruff check src/eazy/cli/ tests/unit/cli/`
- [ ] **Formatting**: `uv run ruff format --check src/eazy/cli/ tests/unit/cli/`

**Security & Performance**:
- [ ] **Performance**: 포맷팅이 대용량 결과에서도 합리적 시간 내 완료
- [ ] **Error Handling**: 잘못된 포맷 타입 입력 시 적절한 에러

**Documentation**:
- [ ] **Code Comments**: 복잡한 포맷팅 로직 주석
- [ ] **API Docs**: 포맷터 클래스 인터페이스 문서화

**Manual Testing**:
- [ ] **Functionality**: 3가지 포맷 모두 정상 출력
- [ ] **Edge Cases**: 빈 결과(0 페이지)에서도 포맷 정상 동작
- [ ] **Error States**: 잘못된 --format 값 입력 시 에러 메시지

**Validation Commands**:
```bash
# Test Commands
uv run pytest tests/unit/cli/ -v

# Coverage Check
uv run pytest --cov=src/eazy/cli --cov-report=term-missing

# Code Quality
uv run ruff check src/eazy/cli/ tests/unit/cli/
uv run ruff format --check src/eazy/cli/ tests/unit/cli/

# No Regressions
uv run pytest tests/ -v
```

**Manual Test Checklist**:
- [ ] `uv run eazy crawl http://example.com --format json` 이 유효한 JSON 출력
- [ ] `uv run eazy crawl http://example.com --format text` 가 읽기 쉬운 텍스트 출력
- [ ] `uv run eazy crawl http://example.com --format table` 이 포맷된 테이블 출력
- [ ] `uv run eazy crawl http://example.com` (기본) 이 table 포맷 출력

---

### Phase 4: Scan 커맨드, Resume 스텁 & 통합 테스트
**Goal**: `eazy scan <url>` 커맨드 (크롤러 + 스캐너 placeholder), `eazy resume` 스텁, E2E 통합 테스트
**Estimated Time**: 3 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**
- [ ] **Test 4.1**: scan 커맨드 단위 테스트
  - File(s): `tests/unit/cli/test_scan_command.py`
  - Expected: Tests FAIL (red) - scan 커맨드 미완성
  - Details: Test cases covering:
    - `eazy scan http://example.com` 이 성공적으로 실행 (exit code 0)
    - `eazy scan` URL 없이 실행 시 에러
    - `--depth`, `--format`, `--output` 옵션이 scan에서 동작
    - scan 커맨드가 CrawlerEngine 호출 (크롤 단계)
    - scan 출력에 크롤 결과 포함

- [ ] **Test 4.2**: resume 커맨드 단위 테스트
  - File(s): `tests/unit/cli/test_app.py` (추가)
  - Expected: Tests FAIL (red) - resume 커맨드 미존재
  - Details: Test cases:
    - `eazy resume --help` 가 help 텍스트 표시
    - `eazy resume some-scan-id` 가 기능 상태 안내 메시지 표시

- [ ] **Test 4.3**: CLI 크롤 플로우 통합 테스트
  - File(s): `tests/integration/cli/test_cli_crawl_integration.py`
  - Expected: Tests FAIL (red) - 통합 테스트 인프라 미구축
  - Details: Test cases:
    - respx 모킹된 HTTP 응답으로 전체 `eazy crawl` 실행
    - 출력에 모킹에서 발견된 페이지 포함 확인
    - `--output`이 올바른 JSON 파일 생성 확인
    - `--format text`가 읽기 쉬운 출력 생성 확인
    - 출력의 통계가 기대값과 일치 확인
  - Note: `respx.mock` 컨텍스트가 `CliRunner.invoke()` 전체를 감싸야 함 (async 이벤트 루프가 respx 라우트를 인식하도록)

**🟢 GREEN: Implement to Make Tests Pass**
- [ ] **Task 4.4**: scan 커맨드 구현
  - File(s): `src/eazy/cli/app.py`
  - Goal: Make Test 4.1 pass
  - Details:
    - 크롤러 먼저 실행, 스캐너 단계는 placeholder
    - crawl 커맨드와 공통 옵션 공유
    - 포맷된 결과 출력 (포맷터 재사용)
- [ ] **Task 4.5**: resume 커맨드 스텁 구현
  - File(s): `src/eazy/cli/app.py`
  - Goal: Make Test 4.2 pass
  - Details:
    - `scan_id` 인수 수용
    - 안내 메시지 출력: "Resume 기능은 향후 버전에서 제공될 예정입니다"
- [ ] **Task 4.6**: 통합 테스트 인프라 구축
  - File(s): `tests/integration/cli/__init__.py`, `tests/integration/cli/test_cli_crawl_integration.py`
  - Goal: Make Test 4.3 pass
  - Details: respx로 HTTP 모킹, CliRunner로 CLI 호출, 출력 검증

**🔵 REFACTOR: Clean Up Code**
- [ ] **Task 4.7**: 최종 리팩토링
  - Files: 전체 CLI 모듈 코드 검토
  - Goal: 테스트를 깨뜨리지 않고 설계 개선
  - Checklist:
    - [ ] crawl/scan 간 공통 옵션 추출 (DRY)
    - [ ] 모든 커맨드에 일관된 에러 처리
    - [ ] 모든 모듈에 `__all__` export
    - [ ] 모든 docstring 완성

#### Quality Gate ✋

**⚠️ STOP: Final quality gate - ALL checks must pass**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: Test coverage meets requirements
  ```bash
  uv run pytest --cov=src/eazy/cli --cov-report=term-missing
  ```

**Build & Tests**:
- [ ] **All Tests Pass**: `uv run pytest tests/ -v`
- [ ] **No Regressions**: 기존 crawler 테스트 전부 통과
- [ ] **CLI Coverage >= 80%**: `uv run pytest --cov=src/eazy/cli --cov-report=term-missing`
- [ ] **Overall Coverage**: `uv run pytest --cov=src/eazy --cov-report=term-missing`
- [ ] **No Flaky Tests**: 3회 반복 실행 시 일관된 결과

**Code Quality**:
- [ ] **Linting**: `uv run ruff check src/ tests/`
- [ ] **Formatting**: `uv run ruff format --check src/ tests/`

**Security & Performance**:
- [ ] **Dependencies**: 모든 의존성에 알려진 보안 취약점 없음
- [ ] **Performance**: 성능 저하 없음
- [ ] **Error Handling**: 모든 커맨드에서 적절한 에러 처리

**Documentation**:
- [ ] **Code Comments**: 복잡한 로직 문서화
- [ ] **API Docs**: 모든 공개 인터페이스 문서화

**Manual Testing**:
- [ ] **Functionality**: 모든 커맨드 정상 동작
- [ ] **Edge Cases**: 경계 조건 테스트 완료
- [ ] **Error States**: 에러 처리 검증 완료

**Validation Commands**:
```bash
# Test Commands
uv run pytest tests/ -v

# Coverage Check
uv run pytest --cov=src/eazy/cli --cov-report=term-missing
uv run pytest --cov=src/eazy --cov-report=term-missing

# Code Quality
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [ ] `uv run eazy --help` 가 모든 커맨드 표시
- [ ] `uv run eazy crawl http://example.com --depth 2 --format table`
- [ ] `uv run eazy scan http://example.com --format json`
- [ ] `uv run eazy resume test-id` 가 안내 메시지 표시

---

## ⚠️ Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| Typer async 호환성 | Low | Medium | asyncio.run() 래퍼 사용 - 확립된 패턴 |
| Scanner 모듈 부재 (REQ-010) | High | Low | scan 커맨드가 크롤러 호출; 스캐너 단계는 placeholder |
| 콜백 없는 프로그레스 바 | Medium | Low | Rich 스피너(불확정 진행률) 사용; Phase 2에서 콜백 추가 |
| Resume에 상태 영속성 필요 | Medium | Medium | Phase 1에서 스텁 커맨드; 전체 구현은 추후 |
| PRD `--scope`/`--auth` 옵션 미구현 | N/A | Low | Phase 2+(AI/스캐너 통합) 연기. `--include-subdomains`가 `--scope` 부분 대체 |

---

## 🔄 Rollback Strategy

### If Phase 1 Fails
**Steps to revert**:
- `src/eazy/cli/` 디렉토리 삭제
- `pyproject.toml` 의존성 변경 되돌리기
- `tests/unit/cli/` 디렉토리 삭제

### If Phase 2 Fails
**Steps to revert**:
- Phase 1 완료 상태로 복원
- `src/eazy/cli/app.py`의 crawl 커맨드 변경사항만 되돌리기
- `tests/unit/cli/test_crawl_command.py` 삭제

### If Phase 3 Fails
**Steps to revert**:
- Phase 2 완료 상태로 복원
- `src/eazy/cli/formatters.py`, `src/eazy/cli/display.py` 삭제
- `tests/unit/cli/test_formatters.py` 삭제

### If Phase 4 Fails
**Steps to revert**:
- Phase 3 완료 상태로 복원
- scan/resume 관련 변경사항만 되돌리기
- `tests/integration/cli/` 디렉토리 삭제

---

## 📊 Progress Tracking

### Completion Status
- **Phase 1**: ⏳ 0%
- **Phase 2**: ⏳ 0%
- **Phase 3**: ⏳ 0%
- **Phase 4**: ⏳ 0%

**Overall Progress**: 0% complete

### Time Tracking
| Phase | Estimated | Actual | Variance |
|-------|-----------|--------|----------|
| Phase 1 | 2 hours | - | - |
| Phase 2 | 3 hours | - | - |
| Phase 3 | 3 hours | - | - |
| Phase 4 | 3 hours | - | - |
| **Total** | 11 hours | - | - |

---

## 📝 Notes & Learnings

### Implementation Notes
- CrawlerEngine은 완전 async - CLI는 sync Typer에서 async 엔진으로 브릿지 필요
- CrawlConfig는 frozen (immutable) - 모든 CLI 옵션으로 한번에 생성
- CrawlResultExporter.to_json()이 이미 pretty-printed JSON 제공
- conftest.py가 현재 비어있음 - 공유 CLI 테스트 fixture 배치에 적합

### Blockers Encountered
- (구현 시 기록)

### Improvements for Future Plans
- (구현 완료 후 기록)

---

## 📚 References

### Documentation
- Typer 공식 문서: https://typer.tiangolo.com/
- Rich 공식 문서: https://rich.readthedocs.io/
- Click Testing: https://click.palletsprojects.com/en/8.1.x/testing/

### Key Source Files
- `src/eazy/crawler/engine.py` - CrawlerEngine.crawl() async 메서드
- `src/eazy/crawler/exporter.py` - CrawlResultExporter (JSON 출력)
- `src/eazy/models/crawl_types.py` - CrawlConfig, CrawlResult, PageResult
- `src/eazy/models/__init__.py` - 공개 모델 export

### PRD Reference
- REQ-009: CLI 인터페이스 (plan/PRD.md)

---

## ✅ Final Checklist

**Before marking plan as COMPLETE**:
- [ ] All 4 phases completed with quality gates passed
- [ ] Full integration testing performed
- [ ] CLI module coverage >= 80%
- [ ] All existing tests still pass (no regressions)
- [ ] `eazy` command works from terminal via entry point
- [ ] Plan document updated with completion status

---

**Plan Status**: 🔄 In Progress
**Next Action**: Phase 1 RED - CLI 앱 구조 테스트 작성
**Blocked By**: None
