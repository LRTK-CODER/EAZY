# Implementation Plan: REQ-009 Auth CLI

**Status**: 🔄 In Progress
**Started**: 2026-02-15
**Last Updated**: 2026-02-15
**Estimated Completion**: 2026-02-16

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

REQ-002B에서 구축된 OAuth 인프라(OAuthFlowEngine, TokenStorage, ProviderType)를 활용하여 `eazy auth` CLI 서브커맨드 그룹을 구현한다. 사용자가 터미널에서 LLM Provider 인증을 수행, 확인, 삭제할 수 있다.

### Success Criteria
- [ ] `eazy auth login --provider <type>` 명령으로 LLM Provider 인증을 수행할 수 있다 (브라우저 기반 OAuth consent flow)
- [ ] `eazy auth status` 명령으로 현재 인증 상태와 저장된 계정 목록을 확인할 수 있다
- [ ] `eazy auth logout --provider <type>` 명령으로 저장된 인증 토큰을 삭제할 수 있다

### User Impact

보안 담당자가 CLI에서 직접 LLM 인증을 관리할 수 있어, AI 기반 스마트 크롤링/스캐닝 전에 필요한 인증 설정을 쉽게 수행할 수 있다.

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| Typer sub-app `auth_app = typer.Typer()` + `app.add_typer()` | `eazy auth login/status/logout` 계층 구조. Typer 공식 패턴 | 진입점이 하나 더 생기지만 명확한 커맨드 그룹 |
| 별도 `src/eazy/cli/auth.py` 모듈 | app.py를 lean하게 유지. 기존 패턴(display.py, formatters.py)과 일관 | 파일 하나 추가되지만 관심사 분리 |
| OAuth provider → `OAuthFlowEngine.run_interactive_flow()` 위임 | 이미 구현+테스트 완료된 인프라(Phase 6). 새 코드 최소화 | OAuth 플로우 커스터마이징 제한 (현재 불필요) |
| API key provider → `typer.prompt()` 입력 | 표준 CLI 대화형 입력. CliRunner의 `input=` 파라미터로 테스트 가능 | 파이프 입력 시 TTY 문제 가능 (Phase 2+ 에서 `--key` 옵션 추가 고려) |
| Rich Table for status output | 기존 crawl의 TableFormatter와 일관된 UX | Rich 의존성 (Typer에 이미 포함) |
| logout 시 확인 프롬프트 없음 | CLI 자동화 친화적. `--provider`가 이미 범위 한정 | 실수 삭제 위험 (저영향: 재인증으로 복구 가능) |

---

## 📦 Dependencies

### Required Before Starting
- [x] REQ-002B LLM Provider Abstraction 완료 (380 tests, 95% eazy.ai coverage)
- [x] OAuth 인프라: OAuthFlowEngine, TokenStorage, ProviderType 구현 완료
- [x] 기존 CLI 구조: app.py, CliRunner 테스트 패턴 확립

### External Dependencies
- `typer` (기존 — CLI 프레임워크)
- `rich` (기존 — Typer 내장, Table 출력)

### Reusable Existing Infrastructure (REQ-002B)

| Module | File | Reuse Point |
|--------|------|-------------|
| `OAuthFlowEngine` | `src/eazy/ai/oauth_flow.py` | `run_interactive_flow()` — 브라우저 OAuth 전체 플로우 |
| `TokenStorage` | `src/eazy/ai/token_storage.py` | `save/load/delete/list_accounts` — 토큰 CRUD |
| `ProviderType` | `src/eazy/ai/models.py` | enum: `GEMINI_OAUTH`, `ANTIGRAVITY`, `GEMINI_API` |
| `OAuthTokens` | `src/eazy/ai/models.py` | frozen model: access_token, refresh_token, expires_at |
| `ProviderFactory` | `src/eazy/ai/provider_factory.py` | `create(config)` → concrete provider |
| Typer CLI patterns | `src/eazy/cli/app.py` | CliRunner, @app.command(), asyncio.run() |
| CLI test patterns | `tests/unit/cli/test_crawl_command.py` | CliRunner + @patch + AsyncMock |

---

## 🧪 Test Strategy

### Testing Approach
**TDD Principle**: Write tests FIRST, then implement to make them pass

**Auth CLI Test Guidelines**:
- OAuth 플로우는 전부 Mock (`OAuthFlowEngine.run_interactive_flow` → AsyncMock)
- `TokenStorage`는 Mock (save/load/delete/list_accounts 호출 검증)
- `typer.prompt()`는 CliRunner의 `input=` 파라미터로 시뮬레이션
- CliRunner 패턴: `runner.invoke(app, ["auth", "login", "--provider", "gemini_oauth"])`
- `@patch("eazy.cli.auth.XXX")` — auth.py 모듈 레벨에서 Mock

### Test Pyramid for This Feature
| Test Type | Coverage Target | Purpose |
|-----------|-----------------|---------|
| **Unit Tests** | ≥80% | CLI command 로직, 옵션 파싱, 출력 포맷 |
| **Integration Tests** | Critical paths | login → status → logout 전체 플로우 |

### Test File Organization
```
tests/
└── unit/
    └── cli/
        └── test_auth_command.py   # 22 tests (all 3 phases)
```

### Coverage Requirements by Phase
- **Phase 1 (Login)**: auth.py login 관련 코드 (≥80%)
- **Phase 2 (Status)**: auth.py status 관련 코드 (≥80%)
- **Phase 3 (Logout + Integration)**: auth.py 전체 (≥80%)

### Test Naming Convention
```python
# File: test_auth_command.py
# Class: Test{CommandGroup}{Feature}
# Function: test_auth_{command}_{behavior}_{expected_result}
# Example: test_auth_login_gemini_oauth_triggers_interactive_flow
# Pattern: Arrange -> Act -> Assert
```

---

## 🚀 Implementation Phases

### Phase 1: Auth Command Group & Login
**Goal**: `eazy auth login --provider <type>` 명령 구현. OAuth/API key 인증 플로우 지원
**Estimated Time**: 2 hours
**Status**: ✅ Complete

#### Tasks

**🔴 RED: Write Failing Tests First**

- [x] **Test 1.1**: Auth command group 구조 테스트 (4 tests)
  - File(s): `tests/unit/cli/test_auth_command.py` (신규 파일)
  - Expected: Tests FAIL (red) because auth sub-app doesn't exist
  - Details:
    - `test_auth_help_shows_usage` — `eazy auth --help` 시 usage 텍스트 출력, exit_code 0
    - `test_auth_login_help_shows_provider_option` — `eazy auth login --help` 시 `--provider` 옵션 표시
    - `test_auth_login_requires_provider_option` — `eazy auth login` (provider 없이) 시 에러
    - `test_auth_login_rejects_unknown_provider` — `--provider unknown` 시 에러 메시지

- [x] **Test 1.2**: Login OAuth 테스트 (3 tests)
  - File(s): `tests/unit/cli/test_auth_command.py` (동일 파일에 추가)
  - Expected: Tests FAIL (red) because login command doesn't exist
  - Details:
    - `test_auth_login_gemini_oauth_triggers_interactive_flow` — `--provider gemini_oauth` 시 `OAuthFlowEngine.run_interactive_flow()` 호출
    - `test_auth_login_gemini_oauth_saves_token` — 성공 시 `TokenStorage.save()` 호출
    - `test_auth_login_gemini_oauth_shows_success_message` — 성공 시 "Successfully authenticated" 메시지

- [x] **Test 1.3**: Login API key 테스트 (3 tests)
  - File(s): `tests/unit/cli/test_auth_command.py` (동일 파일에 추가)
  - Expected: Tests FAIL (red)
  - Details:
    - `test_auth_login_gemini_api_prompts_for_key` — `--provider gemini_api` 시 `typer.prompt()` 호출 (CliRunner `input=` 사용)
    - `test_auth_login_gemini_api_saves_key` — 입력된 키를 `TokenStorage.save()` 로 저장
    - `test_auth_login_gemini_api_shows_success_message` — 성공 시 "API key saved" 메시지

**🟢 GREEN: Implement to Make Tests Pass**

- [x] **Task 1.4**: auth.py 모듈 생성 및 login 구현
  - File(s): `src/eazy/cli/auth.py` (신규)
  - Goal: Test 1.1 + 1.2 + 1.3 통과
  - Details:
    - `auth_app = typer.Typer(name="auth", help="Manage LLM provider authentication.")`
    - `VALID_PROVIDERS = ["gemini_oauth", "antigravity", "gemini_api"]`
    - `@auth_app.command("login")` — provider 옵션 필수
    - OAuth provider (`gemini_oauth`, `antigravity`): `OAuthFlowEngine.run_interactive_flow()` 호출 → `TokenStorage.save()`
    - API key provider (`gemini_api`): `typer.prompt("Enter API key", hide_input=True)` → `TokenStorage.save()`
    - 에러 처리: OAuthError → `typer.echo("Authentication failed: ...")` + `raise typer.Exit(1)`

- [x] **Task 1.5**: app.py에 auth sub-app 등록
  - File(s): `src/eazy/cli/app.py` (기존 파일 수정)
  - Goal: `eazy auth` 커맨드 그룹 활성화
  - Details:
    - `from eazy.cli.auth import auth_app`
    - `app.add_typer(auth_app, name="auth")`

**🔵 REFACTOR: Clean Up Code**

- [x] **Task 1.6**: 코드 품질 개선
  - Files: `src/eazy/cli/auth.py`, `src/eazy/cli/app.py`
  - Goal: 테스트 깨지지 않으면서 설계 개선
  - Checklist:
    - [x] Google 스타일 docstring 추가
    - [x] 에러 처리 일관성 확인
    - [x] 기존 380개 테스트 전부 통과 재확인

#### Quality Gate ✋

**⚠️ STOP: Do NOT proceed to Phase 2 until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [x] **Red Phase**: Tests were written FIRST and initially failed
- [x] **Green Phase**: Production code written to make tests pass
- [x] **Refactor Phase**: Code improved while tests still pass
- [x] **Coverage Check**: auth.py login 관련 커버리지 92% (≥80%)

**Build & Tests**:
- [x] **All Tests Pass**: 380 existing + 10 new = 390 tests, all passing
- [x] **No Flaky Tests**: 일관된 결과

**Code Quality**:
- [x] **Linting**: `uv run ruff check src/ tests/` — 에러 없음
- [x] **Formatting**: `uv run ruff format --check src/ tests/` — 변경 없음
- [x] **Type Safety**: 모든 함수에 타입 힌트 적용

**Validation Commands**:
```bash
uv run pytest tests/ -v
uv run pytest tests/unit/cli/test_auth_command.py --cov=eazy.cli.auth --cov-report=term-missing
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [x] `eazy auth --help` 시 login 서브커맨드 표시
- [x] `eazy auth login --provider gemini_api` 시 API 키 입력 프롬프트 표시
- [x] 기존 380개 테스트 regression 없음

---

### Phase 2: Auth Status Command
**Goal**: `eazy auth status` 명령 구현. 저장된 계정 목록과 인증 상태를 Rich Table로 출력
**Estimated Time**: 1.5 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**

- [ ] **Test 2.1**: Status 명령 테스트 (6 tests)
  - File(s): `tests/unit/cli/test_auth_command.py` (기존 파일에 추가)
  - Expected: Tests FAIL (red) because status command doesn't exist
  - Details:
    - `test_auth_status_help_shows_usage` — `eazy auth status --help` 시 도움말 표시, exit_code 0
    - `test_auth_status_no_accounts_shows_empty_message` — 계정 없을 때 "No authenticated providers" 메시지
    - `test_auth_status_shows_gemini_oauth_account` — 단일 OAuth 계정 표시 (provider, account_id, status)
    - `test_auth_status_shows_multiple_providers` — 복수 provider 계정 표시
    - `test_auth_status_shows_expired_token` — 만료된 토큰의 상태 "expired" 표시
    - `test_auth_status_exit_code_zero` — 항상 exit_code 0 (정보 표시 명령)

**🟢 GREEN: Implement to Make Tests Pass**

- [ ] **Task 2.2**: status 명령 구현
  - File(s): `src/eazy/cli/auth.py` (기존 파일에 추가)
  - Goal: Test 2.1 통과
  - Details:
    - `@auth_app.command("status")` — 인자 없음
    - `TokenStorage` 인스턴스 생성 → 각 `ProviderType`에 대해 `list_accounts()` 호출
    - 계정별 `load()` → 토큰 데이터에서 `expires_at` 확인 → 만료 여부 판정
    - Rich Table 출력: Provider | Account | Status (active/expired) | Expires At
    - 계정 없으면 "No authenticated providers found." 메시지

**🔵 REFACTOR: Clean Up Code**

- [ ] **Task 2.3**: 코드 품질 개선
  - Files: `src/eazy/cli/auth.py`
  - Goal: 테스트 깨지지 않으면서 설계 개선
  - Checklist:
    - [ ] status 출력 헬퍼 함수 추출 (필요 시)
    - [ ] docstring 추가
    - [ ] 전체 테스트 통과 재확인

#### Quality Gate ✋

**⚠️ STOP: Do NOT proceed to Phase 3 until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: auth.py status 관련 커버리지 ≥80%

**Build & Tests**:
- [ ] **All Tests Pass**: 390 existing + 6 new = 396 tests, all passing
- [ ] **No Flaky Tests**: 일관된 결과

**Code Quality**:
- [ ] **Linting**: `uv run ruff check src/ tests/` — 에러 없음
- [ ] **Formatting**: `uv run ruff format --check src/ tests/` — 변경 없음

**Validation Commands**:
```bash
uv run pytest tests/ -v
uv run pytest tests/unit/cli/test_auth_command.py --cov=eazy.cli.auth --cov-report=term-missing
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Manual Test Checklist**:
- [ ] `eazy auth status` 시 테이블 형식으로 출력
- [ ] 계정 없을 때 빈 상태 메시지 출력
- [ ] 만료된 토큰이 "expired" 상태로 표시

---

### Phase 3: Auth Logout & Integration
**Goal**: `eazy auth logout --provider <type>` 구현 + login → status → logout 전체 통합 테스트
**Estimated Time**: 1.5 hours
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**

- [ ] **Test 3.1**: Logout 명령 테스트 (4 tests)
  - File(s): `tests/unit/cli/test_auth_command.py` (기존 파일에 추가)
  - Expected: Tests FAIL (red) because logout command doesn't exist
  - Details:
    - `test_auth_logout_help_shows_provider_option` — `eazy auth logout --help` 시 `--provider` 옵션 표시
    - `test_auth_logout_requires_provider_option` — `eazy auth logout` (provider 없이) 시 에러
    - `test_auth_logout_deletes_stored_tokens` — `--provider gemini_oauth` 시 `TokenStorage.delete()` 호출
    - `test_auth_logout_shows_success_message` — 성공 시 "Successfully logged out" 메시지

- [ ] **Test 3.2**: 통합 테스트 (2 tests)
  - File(s): `tests/unit/cli/test_auth_command.py` (기존 파일에 추가)
  - Expected: Tests FAIL (red)
  - Details:
    - `test_auth_login_then_status_shows_account` — login 후 status에서 해당 계정 표시 (Mock 체이닝)
    - `test_auth_login_then_logout_removes_account` — login 후 logout 시 토큰 삭제 확인 (Mock 체이닝)

**🟢 GREEN: Implement to Make Tests Pass**

- [ ] **Task 3.3**: logout 명령 구현
  - File(s): `src/eazy/cli/auth.py` (기존 파일에 추가)
  - Goal: Test 3.1 + 3.2 통과
  - Details:
    - `@auth_app.command("logout")` — `--provider` 옵션 필수
    - `TokenStorage` → 해당 provider의 모든 계정에 대해 `delete()` 호출
    - 성공 시 "Successfully logged out from {provider}" 메시지
    - 저장된 토큰 없어도 에러 없이 성공 처리 (idempotent)

**🔵 REFACTOR: Clean Up Code**

- [ ] **Task 3.4**: 최종 코드 품질 개선
  - Files: `src/eazy/cli/auth.py`, `tests/unit/cli/test_auth_command.py`
  - Goal: 테스트 깨지지 않으면서 최종 정리
  - Checklist:
    - [ ] 공통 헬퍼 함수 추출 (`_get_token_storage()` 등)
    - [ ] docstring 최종 확인
    - [ ] import 정렬 (ruff check --fix)
    - [ ] 전체 코드 린팅/포맷팅 최종 확인

#### Quality Gate ✋

**⚠️ STOP: Do NOT mark complete until ALL checks pass**

**TDD Compliance** (CRITICAL):
- [ ] **Red Phase**: Tests were written FIRST and initially failed
- [ ] **Green Phase**: Production code written to make tests pass
- [ ] **Refactor Phase**: Code improved while tests still pass
- [ ] **Coverage Check**: auth.py 전체 커버리지 ≥80%

**Build & Tests**:
- [ ] **Build**: 프로젝트 에러 없이 빌드
- [ ] **All Tests Pass**: 396 existing + 6 new = 402 tests, all passing
- [ ] **No Flaky Tests**: 일관된 결과

**Code Quality**:
- [ ] **Linting**: `uv run ruff check src/ tests/` — 에러 없음
- [ ] **Formatting**: `uv run ruff format --check src/ tests/` — 변경 없음
- [ ] **Type Safety**: 모든 새 함수에 타입 힌트 적용

**Security & Performance**:
- [ ] **No Secrets in Code**: API 키, 토큰 등 하드코딩 없음
- [ ] **Token Security**: logout 시 토큰 파일 완전 삭제 확인
- [ ] **Error Handling**: OAuth 실패, 파일 I/O 에러 등 적절한 처리

**Documentation**:
- [ ] **Code Comments**: 복잡한 로직에 주석
- [ ] **Docstring**: 모든 public 함수에 Google 스타일 docstring

**Validation Commands**:
```bash
# 전체 테스트
uv run pytest tests/ -v

# Auth CLI 커버리지
uv run pytest tests/unit/cli/test_auth_command.py --cov=eazy.cli.auth --cov-report=term-missing

# 린팅/포맷팅
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# 기존 테스트 regression
uv run pytest tests/ --tb=short
```

**Manual Test Checklist**:
- [ ] `eazy auth logout --provider gemini_oauth` 시 토큰 삭제 확인
- [ ] 존재하지 않는 토큰 logout 시 에러 없음
- [ ] 전체 플로우: login → status → logout 동작

---

## 🧪 Mocking Strategy

### Login OAuth Test Pattern
```python
@patch("eazy.cli.auth.TokenStorage")
@patch("eazy.cli.auth.OAuthFlowEngine")
def test_auth_login_gemini_oauth_triggers_interactive_flow(
    self, mock_flow_cls, mock_storage_cls
):
    mock_flow = AsyncMock()
    mock_flow.run_interactive_flow.return_value = OAuthTokens(...)
    mock_flow_cls.return_value = mock_flow
    result = runner.invoke(app, ["auth", "login", "--provider", "gemini_oauth"])
    assert result.exit_code == 0
    mock_flow.run_interactive_flow.assert_called_once()
```

### Login API Key Test Pattern
```python
@patch("eazy.cli.auth.TokenStorage")
def test_auth_login_gemini_api_prompts_for_key(self, mock_storage_cls):
    result = runner.invoke(
        app,
        ["auth", "login", "--provider", "gemini_api"],
        input="my-api-key\n",
    )
    assert result.exit_code == 0
    mock_storage_cls.return_value.save.assert_called_once()
```

### Status Test Pattern
```python
@patch("eazy.cli.auth.TokenStorage")
def test_auth_status_shows_gemini_oauth_account(self, mock_storage_cls):
    mock_storage = Mock()
    mock_storage.list_accounts.return_value = ["default"]
    mock_storage.load.return_value = {"access_token": "...", "expires_at": "..."}
    mock_storage_cls.return_value = mock_storage
    result = runner.invoke(app, ["auth", "status"])
    assert "gemini_oauth" in result.output
```

---

## ⚠️ Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| Typer sub-app 라우팅 문제 | Low | Medium | Typer 공식 문서 sub-app 패턴 사용. CliRunner 테스트로 즉시 검증 |
| OAuth flow mock 복잡성 | Low | Low | AsyncMock + `run_interactive_flow` 단일 진입점. REQ-002B 테스트 패턴 재활용 |
| CliRunner input= 제한 | Low | Low | `typer.prompt()` 표준 패턴. 기존 Typer 프로젝트 검증 완료 |
| 기존 380 테스트 깨짐 | Very Low | High | auth.py는 독립 모듈. app.py 수정은 `add_typer()` 한 줄뿐 |

---

## 🔄 Rollback Strategy

### If Phase 1 Fails
**Steps to revert**:
- `src/eazy/cli/auth.py` 삭제
- `src/eazy/cli/app.py`에서 `add_typer()` 및 import 제거
- `tests/unit/cli/test_auth_command.py` 삭제

### If Phase 2 Fails
**Steps to revert**:
- Phase 1 완료 상태로 복원
- auth.py에서 status 명령 관련 코드 제거
- test_auth_command.py에서 TestAuthStatus 클래스 제거

### If Phase 3 Fails
**Steps to revert**:
- Phase 2 완료 상태로 복원
- auth.py에서 logout 명령 관련 코드 제거
- test_auth_command.py에서 TestAuthLogout, TestAuthIntegration 클래스 제거

---

## 📊 Progress Tracking

### Completion Status
- **Phase 1**: ✅ 100%
- **Phase 2**: ⏳ 0%
- **Phase 3**: ⏳ 0%

**Overall Progress**: 33% complete

### Time Tracking
| Phase | Estimated | Actual | Variance |
|-------|-----------|--------|----------|
| Phase 1 | 2 hours | - | - |
| Phase 2 | 1.5 hours | - | - |
| Phase 3 | 1.5 hours | - | - |
| **Total** | **5 hours** | - | - |

---

## 📝 Notes & Learnings

### Implementation Notes
- [Add insights discovered during implementation]

### Blockers Encountered
- None yet

### Improvements for Future Plans
- [What would you do differently next time?]

---

## 📚 References

### Documentation
- PRD REQ-009 스펙: `plan/PRD.md` (lines 391-411)
- OAuth 인프라: `src/eazy/ai/oauth_flow.py` (OAuthFlowEngine.run_interactive_flow)
- 토큰 저장: `src/eazy/ai/token_storage.py` (TokenStorage.save/load/delete/list_accounts)
- 기존 CLI 구조: `src/eazy/cli/app.py`
- 기존 CLI 테스트: `tests/unit/cli/test_crawl_command.py`
- Typer sub-app 문서: https://typer.tiangolo.com/tutorial/subcommands/

### Related Issues
- Branch: `feature/req-009-auth-cli`
- 선행 작업: REQ-002B 전체 완료 (feature/req-002b-llm-provider, merged to main)
- 후속 작업: REQ-009 resume 명령 (REQ-004 스캔 기능 구현 시 함께)

---

## ✅ Final Checklist

**Before marking plan as COMPLETE**:
- [ ] All phases completed with quality gates passed
- [ ] Full integration testing performed (login → status → logout)
- [ ] 402 tests total (380 existing + 22 new auth CLI) 전부 통과
- [ ] eazy.cli.auth 커버리지 ≥80%
- [ ] PRD REQ-009 auth 관련 3개 AC 모두 체크 완료
- [ ] TASK.md 최종 업데이트
- [ ] Plan document archived for future reference

---

## 🔍 Verification

After implementing all phases, verify end-to-end:

```bash
# 1. 전체 테스트 실행
uv run pytest tests/ -v

# 2. Auth CLI 커버리지 확인
uv run pytest tests/unit/cli/test_auth_command.py --cov=eazy.cli.auth --cov-report=term-missing

# 3. 린팅/포맷팅
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# 4. 기존 테스트 regression 확인
uv run pytest tests/unit/models/ tests/unit/crawler/ tests/integration/crawler/ tests/unit/ai/ tests/integration/ai/ -v
```

---

**Plan Status**: 🔄 In Progress
**Next Action**: Phase 2 — RED: Write failing tests for auth status command
**Blocked By**: None
