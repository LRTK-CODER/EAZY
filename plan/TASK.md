# Implementation Plan: REQ-002B LLM Provider 추상화 및 플러그인 기반 인증

**Status**: ⏳ Pending
**Started**: 2026-02-17
**Last Updated**: 2026-02-17

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
다양한 LLM Provider를 통합하는 추상화 레이어를 구축한다. 플러그인 기반 인증 아키텍처를 채택하여 각 프로바이더의 인증 로직(OAuth, API 키)을 독립 모듈로 분리한다. REQ-002C, REQ-002D 및 향후 모든 LLM 관련 기능의 기반 인프라이다.

### Success Criteria
- [ ] LLMProvider 추상 인터페이스가 정의되어 있다
- [ ] 플러그인 기반 인증 아키텍처가 구현되어 있다
- [ ] ~/.eazy/auth.json 기반 인증 저장소가 동작한다
- [ ] Gemini OAuth, Antigravity OAuth, Gemini API 3개 프로바이더가 구현되어 있다
- [ ] OAuth 브라우저 consent flow → 콜백 서버 → 토큰 저장/갱신이 동작한다
- [ ] Rate limit 시 멀티 계정 자동 전환이 동작한다
- [ ] 테스트 커버리지 80% 이상

### User Impact
보안 담당자가 별도 API 과금 없이 기존 Gemini 구독으로 AI 기능을 사용하고, 향후 다른 LLM으로 쉽게 전환할 수 있다.

---

## 🏗️ Architecture Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| 명시적 플러그인 등록 (auto-discovery 아님) | 단순성 우선, 프로바이더 수가 적음(3개) | 새 프로바이더 추가 시 레지스트리에 수동 등록 필요 |
| asyncio 기반 OAuth 콜백 서버 | 추가 의존성(aiohttp) 불필요, httpx만 사용 | 기능이 제한적 (단순 GET 수신만) |
| TokenStorage는 단순 JSON CRUD | auth.json은 사용자당 1개, 동시 접근 불필요 | 파일 잠금(locking) 미지원 |
| LLMResponse는 Pydantic 모델 | 직렬화/검증 필요, 프로젝트 컨벤션 일치 | dataclass 대비 약간의 오버헤드 |
| AccountManager를 별도 클래스로 분리 | 멀티 계정 로직 재사용 (Gemini OAuth + Antigravity) | 파일 1개 추가 |

---

## 📦 Dependencies

### Required Before Starting
- [x] REQ-001 정규식 크롤링 엔진 완료 (109 tests, 98% coverage)
- [x] PRD REQ-002B 플러그인 기반 아키텍처 업데이트 완료

### External Dependencies
- httpx: 기존 설치됨 (HTTP 클라이언트)
- pydantic: 기존 설치됨 (데이터 모델)
- 추가 패키지: 없음

---

## 🧪 Test Strategy

### Testing Approach
**TDD Principle**: Write tests FIRST, then implement to make them pass

### Test Pyramid for This Feature
| Test Type | Coverage Target | Purpose |
|-----------|-----------------|---------|
| **Unit Tests** | ≥80% | ABC 계약, 모델 검증, 저장소 CRUD, 프로바이더 로직 |
| **Integration Tests** | Critical paths | Registry ↔ Provider ↔ TokenStorage 연동 |

### Test File Organization
```
tests/
├── unit/
│   └── ai/
│       ├── test_models.py
│       ├── test_provider.py
│       ├── test_credentials.py
│       ├── test_oauth_flow.py
│       ├── test_account_manager.py
│       └── plugins/
│           ├── test_gemini_api.py
│           ├── test_gemini_oauth.py
│           └── test_antigravity_oauth.py
└── integration/
    └── ai/
        └── test_provider_integration.py
```

### Coverage Requirements by Phase
- **Phase 1 (추상화 계층)**: ≥90% (순수 모델/ABC/CRUD)
- **Phase 2 (프로바이더 구현)**: ≥80% (OAuth mock 포함)
- **Phase 3 (확장 + 통합)**: ≥80% (통합 테스트 포함)

### Test Naming Convention
```python
# 파일명: test_{모듈명}.py
# 클래스명: Test{컴포넌트명}
# 함수명: test_{행위}_{조건}_{기대결과}
# 예시: test_register_provider_with_duplicate_name_raises_error
# 패턴: Arrange -> Act -> Assert
```

---

## 🚀 Implementation Phases

### Phase 1: 추상화 계층 — 모델, 인터페이스, 레지스트리, 저장소
**Goal**: LLM Provider 시스템의 기반 추상화 완성. 프로바이더 없이도 레지스트리와 저장소가 독립 동작.
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**

- [ ] **Test 1.1**: AI 데이터 모델 단위 테스트
  - File: `tests/unit/ai/test_models.py`
  - Expected: Tests FAIL — 모델 클래스 미존재
  - Details:
    - `LLMResponse` 생성 및 필드 검증
    - `AuthEntry` OAuth 타입 / API 키 타입 구분
    - `OAuthTokens` 만료 시간 검증
    - `ApiKeyEntry` 키 마스킹

- [ ] **Test 1.2**: LLMProvider ABC + ProviderRegistry 단위 테스트
  - File: `tests/unit/ai/test_provider.py`
  - Expected: Tests FAIL — ABC/Registry 미존재
  - Details:
    - LLMProvider ABC 직접 인스턴스화 불가
    - LLMProvider 필수 메서드 계약 (send, is_available, name)
    - ProviderRegistry 등록/조회/목록
    - 중복 이름 등록 시 에러
    - 미등록 프로바이더 조회 시 None 또는 KeyError

- [ ] **Test 1.3**: AuthPlugin ABC 단위 테스트
  - File: `tests/unit/ai/plugins/test_base.py` (또는 test_provider.py에 통합)
  - Expected: Tests FAIL — AuthPlugin 미존재
  - Details:
    - AuthPlugin ABC 직접 인스턴스화 불가
    - 필수 메서드 계약 (authenticate, refresh, is_expired)

- [ ] **Test 1.4**: TokenStorage 단위 테스트
  - File: `tests/unit/ai/test_credentials.py`
  - Expected: Tests FAIL — TokenStorage 미존재
  - Details:
    - auth.json 저장/로드 (save, load, get, remove)
    - 파일 없을 때 빈 dict 반환
    - 디렉토리 자동 생성
    - OAuth 타입과 API 키 타입 모두 저장/로드
    - 존재하지 않는 키 get → None

**🟢 GREEN: Implement to Make Tests Pass**

- [ ] **Task 1.5**: AI 데이터 모델 구현
  - File: `src/eazy/ai/models.py`
  - Goal: Test 1.1 통과
  - Details:
    - `LLMResponse(BaseModel)`: content, model, usage (tokens), finish_reason
    - `OAuthTokens(BaseModel)`: access_token, refresh_token, expires_at (int, epoch ms)
    - `ApiKeyEntry(BaseModel)`: key
    - `AuthEntry(BaseModel)`: type (Literal["oauth", "api"]), oauth: OAuthTokens | None, api: ApiKeyEntry | None

- [ ] **Task 1.6**: LLMProvider ABC + ProviderRegistry 구현
  - File: `src/eazy/ai/provider.py`
  - Goal: Test 1.2 통과
  - Details:
    - `LLMProvider(ABC)`: abstractmethod send(), is_available(), property name
    - `ProviderRegistry`: dict 기반 등록/조회, register(), get(), list_providers()

- [ ] **Task 1.7**: AuthPlugin ABC 구현
  - File: `src/eazy/ai/plugins/base.py`
  - Goal: Test 1.3 통과
  - Details:
    - `AuthPlugin(ABC)`: abstractmethod authenticate(), refresh(), is_expired()

- [ ] **Task 1.8**: TokenStorage 구현
  - File: `src/eazy/ai/credentials.py`
  - Goal: Test 1.4 통과
  - Details:
    - `TokenStorage`: path 기본값 ~/.eazy/auth.json
    - load() → dict[str, AuthEntry], save(), get(), remove()
    - JSON 직렬화: Pydantic model_dump(mode="json") + json.dumps
    - 역직렬화: json.loads + AuthEntry.model_validate

- [ ] **Task 1.9**: __init__.py 및 plugins/__init__.py 설정
  - Files: `src/eazy/ai/__init__.py`, `src/eazy/ai/plugins/__init__.py`
  - Goal: public exports 정리
  - Details: LLMProvider, ProviderRegistry, AuthPlugin, TokenStorage 등 export

**🔵 REFACTOR: Clean Up Code**

- [ ] **Task 1.10**: Phase 1 리팩터링
  - Files: Phase 1에서 생성한 모든 파일
  - Checklist:
    - [ ] 중복 제거
    - [ ] 네이밍 일관성 확인
    - [ ] 타입 힌트 완전성
    - [ ] ruff 포맷팅/린팅 통과

#### Quality Gate ✋

**⚠️ STOP: Do NOT proceed to Phase 2 until ALL checks pass**

**TDD Compliance**:
- [ ] Tests were written FIRST and initially failed
- [ ] Production code written to make tests pass
- [ ] Code improved while tests still pass
- [ ] Coverage ≥ 90%

**Build & Tests**:
- [ ] All tests pass
- [ ] No flaky tests

**Code Quality**:
- [ ] Linting pass
- [ ] Formatting pass

**Validation Commands**:
```bash
uv run pytest tests/unit/ai/test_models.py tests/unit/ai/test_provider.py tests/unit/ai/test_credentials.py -v
uv run pytest tests/unit/ai/ --cov=eazy.ai --cov-report=term-missing
uv run ruff check src/eazy/ai/ tests/unit/ai/
uv run ruff format --check src/eazy/ai/ tests/unit/ai/
```

---

### Phase 2: 프로바이더 구현 — Gemini API + OAuth 플로우 + Gemini OAuth
**Goal**: 실제 LLM과 통신 가능한 프로바이더 2개 완성. API 키와 OAuth 양 방식 지원.
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**

- [ ] **Test 2.1**: Gemini API Provider 단위 테스트
  - File: `tests/unit/ai/plugins/test_gemini_api.py`
  - Expected: Tests FAIL
  - Details:
    - GeminiApiPlugin.authenticate: API 키 검증 (빈 키 에러)
    - GeminiApiPlugin.is_expired: 항상 False
    - GeminiApiProvider.send: 성공 응답 (respx mock)
    - GeminiApiProvider.send: API 에러 (4xx, 5xx)
    - GeminiApiProvider.send: rate limit 429 처리
    - GeminiApiProvider.is_available: 키 존재 여부

- [ ] **Test 2.2**: OAuth 플로우 단위 테스트
  - File: `tests/unit/ai/test_oauth_flow.py`
  - Expected: Tests FAIL
  - Details:
    - OAuthFlow.build_auth_url: 올바른 URL 생성 (client_id, scopes, redirect_uri 포함)
    - OAuthFlow.exchange_code: code → token 교환 성공 (respx mock)
    - OAuthFlow.exchange_code: 잘못된 code 에러
    - OAuthFlow.refresh_token: refresh → new access token (respx mock)
    - OAuthFlow.refresh_token: 만료된 refresh token 에러
    - OAuthCallbackServer: 코드 수신 성공 (asyncio mock)
    - OAuthCallbackServer: timeout 처리

- [ ] **Test 2.3**: Gemini OAuth Provider 단위 테스트
  - File: `tests/unit/ai/plugins/test_gemini_oauth.py`
  - Expected: Tests FAIL
  - Details:
    - GeminiOAuthPlugin: 올바른 OAuth 설정 (client_id, scopes, endpoints)
    - GeminiOAuthPlugin.is_expired: 만료 시간 비교
    - GeminiOAuthPlugin.refresh: 토큰 갱신 (OAuthFlow mock)
    - GeminiOAuthProvider.send: 유효한 토큰으로 요청 (respx mock)
    - GeminiOAuthProvider.send: 만료된 토큰 → 자동 갱신 → 재시도

**🟢 GREEN: Implement to Make Tests Pass**

- [ ] **Task 2.4**: Gemini API Provider 구현
  - File: `src/eazy/ai/plugins/gemini_api.py`
  - Goal: Test 2.1 통과
  - Details:
    - `GeminiApiPlugin(AuthPlugin)`: authenticate (키 검증), is_expired (False), refresh (no-op)
    - `GeminiApiProvider(LLMProvider)`: httpx로 generativelanguage.googleapis.com 호출
    - 엔드포인트: `POST /v1beta/models/{model}:generateContent`
    - 인증: `?key={api_key}` 쿼리 파라미터

- [ ] **Task 2.5**: OAuth 플로우 인프라 구현
  - File: `src/eazy/ai/oauth_flow.py`
  - Goal: Test 2.2 통과
  - Details:
    - `OAuthCallbackServer`: asyncio.start_server 기반, GET /?code=xxx 수신
    - `OAuthFlow`: build_auth_url(), exchange_code(), refresh_token()
    - 브라우저 오픈: webbrowser.open()
    - 토큰 교환: httpx.AsyncClient POST to token_url

- [ ] **Task 2.6**: Gemini OAuth Provider 구현
  - File: `src/eazy/ai/plugins/gemini_oauth.py`
  - Goal: Test 2.3 통과
  - Details:
    - `GeminiOAuthPlugin(AuthPlugin)`: Gemini CLI OAuth 미러링
    - client_id/secret: cloudaicompanion 앱 설정
    - endpoint: cloudaicompanion.googleapis.com
    - `GeminiOAuthProvider(LLMProvider)`: Bearer token으로 API 호출

**🔵 REFACTOR: Clean Up Code**

- [ ] **Task 2.7**: Phase 2 리팩터링
  - Files: Phase 2에서 생성한 모든 파일
  - Checklist:
    - [ ] OAuthFlow와 Provider 간 중복 제거
    - [ ] 에러 처리 일관성
    - [ ] respx mock 패턴 정리
    - [ ] ruff 포맷팅/린팅 통과

#### Quality Gate ✋

**⚠️ STOP: Do NOT proceed to Phase 3 until ALL checks pass**

**TDD Compliance**:
- [ ] Tests were written FIRST and initially failed
- [ ] Production code written to make tests pass
- [ ] Code improved while tests still pass
- [ ] Coverage ≥ 80%

**Build & Tests**:
- [ ] All tests pass (Phase 1 + Phase 2)
- [ ] No flaky tests

**Code Quality**:
- [ ] Linting pass
- [ ] Formatting pass

**Validation Commands**:
```bash
uv run pytest tests/unit/ai/ -v
uv run pytest tests/unit/ai/ --cov=eazy.ai --cov-report=term-missing
uv run ruff check src/eazy/ai/ tests/unit/ai/
uv run ruff format --check src/eazy/ai/ tests/unit/ai/
```

---

### Phase 3: 확장 + 통합 — Antigravity Provider, 멀티 계정, 통합 테스트
**Goal**: Antigravity 프로바이더 추가, 멀티 계정 로테이션 구현, 전체 시스템 통합 검증.
**Status**: ⏳ Pending

#### Tasks

**🔴 RED: Write Failing Tests First**

- [ ] **Test 3.1**: AccountManager 단위 테스트
  - File: `tests/unit/ai/test_account_manager.py`
  - Expected: Tests FAIL
  - Details:
    - get_active_account: 유효한 계정 반환
    - get_active_account: 만료 계정 스킵
    - rotate: 다음 계정으로 전환
    - mark_rate_limited: cooldown 설정
    - 모든 계정 rate limited → None 반환

- [ ] **Test 3.2**: Antigravity OAuth Provider 단위 테스트
  - File: `tests/unit/ai/plugins/test_antigravity_oauth.py`
  - Expected: Tests FAIL
  - Details:
    - AntigravityOAuthPlugin: 올바른 OAuth 설정
    - AntigravityOAuthPlugin: 엔드포인트 폴백 순서 (daily → autopush → prod)
    - AntigravityProvider.send: 성공 (respx mock)
    - AntigravityProvider.send: 429 → 계정 자동 전환
    - AntigravityProvider.send: 엔드포인트 폴백

- [ ] **Test 3.3**: 통합 테스트
  - File: `tests/integration/ai/test_provider_integration.py`
  - Expected: Tests FAIL
  - Details:
    - ProviderRegistry에 3개 프로바이더 등록 + 조회
    - TokenStorage ↔ Provider 연동 (저장 → 로드 → 인증)
    - Provider send → 토큰 만료 → auto refresh → 재시도 (mock)
    - AccountManager ↔ Provider 연동 (rate limit → rotate)

**🟢 GREEN: Implement to Make Tests Pass**

- [ ] **Task 3.4**: AccountManager 구현
  - File: `src/eazy/ai/account_manager.py`
  - Goal: Test 3.1 통과
  - Details:
    - `AccountManager`: provider_name 기반 멀티 계정 관리
    - get_active_account(), rotate(), mark_rate_limited()
    - cooldown: time.monotonic() 기반 (기본 60초)
    - accounts 리스트를 순회하며 유효한 계정 선택

- [ ] **Task 3.5**: Antigravity OAuth Provider 구현
  - File: `src/eazy/ai/plugins/antigravity_oauth.py`
  - Goal: Test 3.2 통과
  - Details:
    - `AntigravityOAuthPlugin(AuthPlugin)`: Antigravity IDE OAuth
    - `AntigravityProvider(LLMProvider)`: 엔드포인트 폴백 + 멀티 계정
    - ENDPOINTS 리스트: daily → autopush → prod 순서
    - send()에서 429/503 → 다음 엔드포인트 → 다음 계정

- [ ] **Task 3.6**: 통합 테스트 구현 + 레지스트리 등록
  - Files: `tests/integration/ai/test_provider_integration.py`, `src/eazy/ai/plugins/__init__.py`
  - Goal: Test 3.3 통과 + 3개 프로바이더 레지스트리 등록
  - Details:
    - plugins/__init__.py에서 기본 프로바이더 3개 등록
    - 통합 테스트: 전체 플로우 검증 (mock 기반)

**🔵 REFACTOR: Clean Up Code**

- [ ] **Task 3.7**: Phase 3 + 전체 리팩터링
  - Files: src/eazy/ai/ 전체
  - Checklist:
    - [ ] Provider 간 공통 로직 추출 (에러 처리, 재시도 등)
    - [ ] __init__.py exports 정리
    - [ ] 전체 타입 힌트 검증
    - [ ] ruff 포맷팅/린팅 통과

#### Quality Gate ✋

**⚠️ STOP: Do NOT proceed until ALL checks pass**

**TDD Compliance**:
- [ ] Tests were written FIRST and initially failed
- [ ] Production code written to make tests pass
- [ ] Code improved while tests still pass
- [ ] Coverage ≥ 80%

**Build & Tests**:
- [ ] All tests pass (Phase 1 + 2 + 3)
- [ ] No flaky tests

**Code Quality**:
- [ ] Linting pass
- [ ] Formatting pass

**Validation Commands**:
```bash
uv run pytest tests/unit/ai/ tests/integration/ai/ -v
uv run pytest tests/unit/ai/ tests/integration/ai/ --cov=eazy.ai --cov-report=term-missing
uv run ruff check src/eazy/ai/ tests/
uv run ruff format --check src/eazy/ai/ tests/
```

---

## ⚠️ Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| OAuth 엔드포인트 변경 | Medium | High | 엔드포인트를 설정으로 분리, 플러그인 구조로 빠른 대응 |
| Gemini CLI OAuth client_id 차단 | Low | High | API 키 Provider를 폴백으로 사용 |
| asyncio 콜백 서버 포트 충돌 | Low | Low | 포트 설정 가능, 에러 메시지로 안내 |

---

## 🔄 Rollback Strategy

### If Phase 1 Fails
- 모든 src/eazy/ai/ 파일 삭제 (기존 코드 영향 없음)
- tests/unit/ai/ 삭제

### If Phase 2 Fails
- Phase 1 상태로 복원 (plugins/gemini_*.py, oauth_flow.py 삭제)

### If Phase 3 Fails
- Phase 2 상태로 복원 (plugins/antigravity_oauth.py, account_manager.py 삭제)

---

## 📊 Progress Tracking

### Completion Status
- **Phase 1**: ⏳ 0%
- **Phase 2**: ⏳ 0%
- **Phase 3**: ⏳ 0%

**Overall Progress**: 0% complete

---

## 📝 Notes & Learnings

### Implementation Notes
- (Phase 진행 중 기록)

### Blockers Encountered
- (발생 시 기록)

---

## 📚 References

### Documentation
- PRD REQ-002B: `plan/PRD.md` lines 132-224
- Gemini API: https://ai.google.dev/api
- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2

### Related Issues
- Reverted commit: 031ee69 (이전 구현 참조용)
- PRD update: 018dec9 (플러그인 아키텍처 반영)

---

## ✅ Final Checklist

**Before marking plan as COMPLETE**:
- [ ] All phases completed with quality gates passed
- [ ] Full integration testing performed
- [ ] 테스트 커버리지 80% 이상
- [ ] 3개 프로바이더 모두 동작 확인
- [ ] auth.json 저장/로드 확인
- [ ] ruff lint/format 통과
