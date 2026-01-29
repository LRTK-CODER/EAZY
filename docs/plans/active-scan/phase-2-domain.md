# Phase 2: Domain 계층 추출

**Status**: ✅ Completed
**Started**: 2025-01-28
**Last Updated**: 2025-01-29
**Completed**: 2025-01-29

---

**⚠️ CRITICAL INSTRUCTIONS**: 각 Phase 완료 후:
1. ✅ 완료된 task 체크박스 체크
2. 🧪 모든 Quality Gate 검증 명령어 실행
3. ⚠️ 모든 Quality Gate 항목 통과 확인
4. 📅 "Last Updated" 날짜 업데이트
5. 📝 Notes 섹션에 배운 점 기록
6. ➡️ 그 후에만 다음 Phase로 진행

⛔ **Quality Gate를 건너뛰거나 실패한 상태로 진행하지 마세요**

---

## 📋 개요

### Phase 목표
CrawlWorker에 흩어져 있는 비즈니스 로직을 Domain 계층으로 추출하여 재사용성과 테스트 용이성을 확보합니다.

### 성공 기준
- [x] UrlValidator가 SSRF 검증 로직 캡슐화
- [x] DataTransformer가 모든 데이터 변환 로직 캡슐화
- [x] ScopeChecker가 URL 범위 검증 로직 캡슐화
- [x] 각 컴포넌트의 단위 테스트 커버리지 ≥95%
- [x] 기존 CrawlWorker의 private 함수들이 Domain Service로 이동

### 사용자 영향
- 코드 가독성 향상
- 새로운 검증 로직 추가 용이
- 보안 검증 로직 중앙 집중화

---

## 🏗️ 아키텍처 결정

| 결정 | 이유 | 트레이드오프 |
|------|------|------------|
| Value Object 패턴 | 불변성 보장, 유효성 검증 캡슐화 | 객체 생성 오버헤드 |
| Domain Service 분리 | 단일 책임, 재사용성 | 파일 수 증가 |
| Protocol 기반 인터페이스 | 의존성 주입, 테스트 용이성 | 추가 타입 정의 |

---

## 📦 의존성

### 시작 전 필요 사항
- [ ] Phase 1 완료 (모든 Quality Gate 통과)
- [ ] 기존 CrawlWorker 코드 분석 완료

### 외부 의존성
- 추가 의존성 없음

---

## 🧪 테스트 전략

### 테스트 접근법
**TDD 원칙**: 테스트를 먼저 작성하고, 테스트를 통과시키는 구현을 작성

### 이 Phase의 테스트 피라미드
| 테스트 유형 | 커버리지 목표 | 목적 |
|------------|--------------|------|
| **단위 테스트** | ≥95% | UrlValidator, DataTransformer, ScopeChecker |
| **속성 기반 테스트** | Edge cases | URL 파싱, IP 검증 |

### 테스트 파일 구조
```
backend/tests/
├── unit/
│   └── domain/
│       └── services/
│           ├── test_url_validator.py
│           ├── test_data_transformer.py
│           └── test_scope_checker.py
```

---

## 🚀 구현 작업

### Day 1-2: UrlValidator 구현

> **Note**: UrlValidator는 기존 `workers/crawl_worker.py:132-186`의 `is_safe_url()` 함수를 **추출 및 개선**합니다.
> 완전히 새로 구현하는 것이 아니라 검증된 로직을 클래스로 래핑하고 ValidationResult를 추가합니다.

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 1.1**: UrlValidator 단위 테스트 작성
  - File(s): `tests/unit/domain/services/test_url_validator.py`
  - Expected: 테스트 FAIL (UrlValidator가 아직 없음)
  - 참조: 기존 `is_safe_url()` 구현 (`workers/crawl_worker.py:132-186`)
  - 테스트 케이스:
    ```python
    class TestUrlValidator:
        # SSRF 방지 테스트
        async def test_blocks_localhost(self):
            """localhost 차단"""
            validator = UrlValidator()
            assert validator.is_safe("http://localhost/") is False
            assert validator.is_safe("http://127.0.0.1/") is False

        async def test_blocks_private_ip_ranges(self):
            """Private IP 대역 차단"""
            validator = UrlValidator()
            assert validator.is_safe("http://10.0.0.1/") is False
            assert validator.is_safe("http://192.168.1.1/") is False
            assert validator.is_safe("http://172.16.0.1/") is False

        async def test_blocks_link_local(self):
            """Link-local 주소 차단"""
            validator = UrlValidator()
            assert validator.is_safe("http://169.254.1.1/") is False

        async def test_blocks_dangerous_schemes(self):
            """위험한 스킴 차단"""
            validator = UrlValidator()
            assert validator.is_safe("file:///etc/passwd") is False
            assert validator.is_safe("gopher://evil.com/") is False
            assert validator.is_safe("data:text/html,<script>") is False

        async def test_allows_valid_public_urls(self):
            """유효한 공개 URL 허용"""
            validator = UrlValidator()
            assert validator.is_safe("https://example.com/") is True
            assert validator.is_safe("https://api.github.com/") is True

        async def test_blocks_ipv6_localhost(self):
            """IPv6 localhost 차단"""
            validator = UrlValidator()
            assert validator.is_safe("http://[::1]/") is False

        async def test_handles_none_and_empty(self):
            """None 및 빈 문자열 처리"""
            validator = UrlValidator()
            assert validator.is_safe(None) is False
            assert validator.is_safe("") is False

        async def test_handles_malformed_urls(self):
            """잘못된 형식의 URL 처리"""
            validator = UrlValidator()
            assert validator.is_safe("not-a-url") is False
            assert validator.is_safe("://missing-scheme") is False
    ```

**🟢 GREEN: 테스트를 통과시키는 구현**

- [ ] **Task 1.2**: UrlValidator 클래스 구현
  - File(s): `backend/app/domain/services/url_validator.py`
  - 목표: Test 1.1 통과
  - 구현 내용:
    ```python
    import ipaddress
    from urllib.parse import urlparse
    from typing import Set

    class UrlValidator:
        """SSRF 방지를 위한 URL 검증기"""

        BLOCKED_SCHEMES: Set[str] = {"file", "gopher", "ftp", "data"}
        BLOCKED_HOSTS: Set[str] = {"localhost", "127.0.0.1", "::1", "[::1]"}

        def is_safe(self, url: str | None) -> bool:
            """URL이 안전한지 검증"""
            if not url:
                return False

            try:
                parsed = urlparse(url)

                # 스킴 검증
                if not parsed.scheme or parsed.scheme.lower() in self.BLOCKED_SCHEMES:
                    return False

                # 호스트 검증
                hostname = parsed.hostname
                if not hostname or hostname.lower() in self.BLOCKED_HOSTS:
                    return False

                # IP 주소 검증
                try:
                    ip = ipaddress.ip_address(hostname)
                    if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local:
                        return False
                except ValueError:
                    pass  # 도메인 이름 - OK

                return True
            except Exception:
                return False
    ```

**🔵 REFACTOR: 코드 정리**

- [ ] **Task 1.3**: 코드 품질 개선
  - 체크리스트:
    - [ ] ValidationResult 반환 타입 추가 (이유 포함)
    - [ ] 로깅 추가
    - [ ] Docstring 완성

---

### Day 3-4: DataTransformer 구현

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 2.1**: DataTransformer 단위 테스트 작성
  - File(s): `tests/unit/domain/services/test_data_transformer.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    class TestDataTransformer:
        def test_map_discovery_source_html(self):
            """html_element_parser → AssetSource.HTML"""
            transformer = DataTransformer()
            assert transformer.map_source("html_element_parser") == AssetSource.HTML

        def test_map_discovery_source_network(self):
            """network_capturer → AssetSource.NETWORK"""
            transformer = DataTransformer()
            assert transformer.map_source("network_capturer") == AssetSource.NETWORK

        def test_map_discovery_source_js(self):
            """js_analyzer_* → AssetSource.JS"""
            transformer = DataTransformer()
            assert transformer.map_source("js_analyzer_regex") == AssetSource.JS
            assert transformer.map_source("js_analyzer_ast") == AssetSource.JS

        def test_map_discovery_source_dom(self):
            """interaction_engine → AssetSource.DOM"""
            transformer = DataTransformer()
            assert transformer.map_source("interaction_engine") == AssetSource.DOM

        def test_map_discovery_source_unknown(self):
            """알 수 없는 소스 → AssetSource.HTML (기본값)"""
            transformer = DataTransformer()
            assert transformer.map_source("unknown_module") == AssetSource.HTML

        def test_map_asset_type_form(self):
            """form → AssetType.FORM"""
            transformer = DataTransformer()
            assert transformer.map_type("form") == AssetType.FORM

        def test_map_asset_type_xhr(self):
            """api_endpoint, xhr, fetch → AssetType.XHR"""
            transformer = DataTransformer()
            assert transformer.map_type("api_endpoint") == AssetType.XHR
            assert transformer.map_type("xhr") == AssetType.XHR
            assert transformer.map_type("fetch") == AssetType.XHR

        def test_map_asset_type_url(self):
            """알 수 없는 타입 → AssetType.URL (기본값)"""
            transformer = DataTransformer()
            assert transformer.map_type("unknown") == AssetType.URL

        def test_to_discovery_context(self):
            """CrawlData → DiscoveryContext 변환"""
            transformer = DataTransformer()
            crawl_data = MockCrawlData(html_content="<html>", ...)
            context = transformer.to_discovery_context(crawl_data, "https://example.com")

            assert context.target_url == "https://example.com"
            assert context.crawl_data["html_content"] == "<html>"

        def test_transform_to_network_requests(self):
            """http_data → network_requests 변환"""
            transformer = DataTransformer()
            http_data = {...}
            requests = transformer.transform_to_network_requests(http_data)
            assert isinstance(requests, list)

        def test_transform_to_network_responses(self):
            """http_data → network_responses 변환"""
            transformer = DataTransformer()
            http_data = {...}
            responses = transformer.transform_to_network_responses(http_data)
            assert isinstance(responses, list)

        def test_extract_html_content_from_http_data(self):
            """http_data에서 HTML 컨텐츠 추출"""
            transformer = DataTransformer()
            http_data = {"responses": [{"url": "https://example.com", "body": "<html>"}]}
            html = transformer.extract_html_content(http_data, "https://example.com")
            assert html == "<html>"
    ```

**🟢 GREEN: 테스트를 통과시키는 구현**

- [ ] **Task 2.2**: DataTransformer 클래스 구현
  - File(s): `backend/app/domain/services/data_transformer.py`
  - 목표: Test 2.1 통과
  - 구현 내용:
    ```python
    from app.models.asset import AssetSource, AssetType
    from app.services.discovery.models import DiscoveryContext, ScanProfile

    class DataTransformer:
        """크롤링 데이터 ↔ Discovery 컨텍스트 변환"""

        SOURCE_MAPPING = {
            "html_element_parser": AssetSource.HTML,
            "network_capturer": AssetSource.NETWORK,
            "js_analyzer_regex": AssetSource.JS,
            "js_analyzer_ast": AssetSource.JS,
            "config_discovery": AssetSource.HTML,
            "interaction_engine": AssetSource.DOM,
        }

        TYPE_MAPPING = {
            "form": AssetType.FORM,
            "api_endpoint": AssetType.XHR,
            "api_call": AssetType.XHR,
            "xhr": AssetType.XHR,
            "fetch": AssetType.XHR,
        }

        def map_source(self, source: str) -> AssetSource:
            ...

        def map_type(self, asset_type: str) -> AssetType:
            ...

        def to_discovery_context(self, crawl_data, target_url, profile=ScanProfile.STANDARD) -> DiscoveryContext:
            ...

        def transform_to_network_requests(self, http_data: dict) -> list[dict]:
            ...

        def transform_to_network_responses(self, http_data: dict) -> list[dict]:
            ...

        def extract_html_content(self, http_data: dict, url: str) -> str:
            ...
    ```

**🔵 REFACTOR: 코드 정리**

- [ ] **Task 2.3**: 코드 품질 개선
  - 체크리스트:
    - [ ] 타입 힌트 개선
    - [ ] 에러 핸들링 추가
    - [ ] 로깅 추가

---

### Day 5: ScopeChecker 및 Port 인터페이스 정의

> **Note**: ScopeChecker는 기존 `services/scope_filter.py`의 `ScopeFilter` 클래스를 **래핑**합니다.
> 새로 구현하는 것이 아니라 Domain 계층에서 사용하기 위한 Adapter 역할입니다.

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 3.1**: ScopeChecker 단위 테스트 작성
  - File(s): `tests/unit/domain/services/test_scope_checker.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    class TestScopeChecker:
        """ScopeChecker 테스트 (기존 ScopeFilter 래핑)"""

        def test_domain_scope_allows_same_domain(self):
            """DOMAIN scope: 같은 도메인 허용 (www 동일 취급)"""
            checker = ScopeChecker()
            target = MockTarget(url="https://example.com", scope=TargetScope.DOMAIN)
            assert checker.is_in_scope("https://example.com/page", target) is True
            assert checker.is_in_scope("https://www.example.com/page", target) is True

        def test_domain_scope_blocks_subdomains(self):
            """DOMAIN scope: 서브도메인은 차단 (기존 ScopeFilter 동작)"""
            checker = ScopeChecker()
            target = MockTarget(url="https://example.com", scope=TargetScope.DOMAIN)
            # 주의: DOMAIN scope는 서브도메인을 허용하지 않음!
            assert checker.is_in_scope("https://api.example.com/", target) is False

        def test_domain_scope_blocks_different_domain(self):
            """DOMAIN scope: 다른 도메인 차단"""
            checker = ScopeChecker()
            target = MockTarget(url="https://example.com", scope=TargetScope.DOMAIN)
            assert checker.is_in_scope("https://evil.com/", target) is False

        def test_subdomain_scope_allows_subdomains(self):
            """SUBDOMAIN scope: 같은 base domain의 모든 서브도메인 허용"""
            checker = ScopeChecker()
            target = MockTarget(url="https://www.example.com", scope=TargetScope.SUBDOMAIN)
            assert checker.is_in_scope("https://www.example.com/page", target) is True
            assert checker.is_in_scope("https://api.example.com/", target) is True
            assert checker.is_in_scope("https://example.com/", target) is True

        def test_subdomain_scope_blocks_different_domain(self):
            """SUBDOMAIN scope: 다른 base domain 차단"""
            checker = ScopeChecker()
            target = MockTarget(url="https://www.example.com", scope=TargetScope.SUBDOMAIN)
            assert checker.is_in_scope("https://evil.com/", target) is False

        def test_url_only_scope_allows_same_url_prefix(self):
            """URL_ONLY scope: 같은 URL prefix만 허용"""
            checker = ScopeChecker()
            target = MockTarget(url="https://example.com/app", scope=TargetScope.URL_ONLY)
            assert checker.is_in_scope("https://example.com/app/page", target) is True
            assert checker.is_in_scope("https://example.com/other", target) is False
    ```

**🟢 GREEN: 테스트를 통과시키는 구현**

- [ ] **Task 3.2**: ScopeChecker 클래스 구현 (ScopeFilter 래핑)
  - File(s): `backend/app/domain/services/scope_checker.py`
  - 목표: Test 3.1 통과
  - 구현 내용:
    ```python
    from app.services.scope_filter import ScopeFilter
    from app.models.target import Target

    class ScopeChecker:
        """
        Domain 계층의 Scope 검증 서비스.

        기존 ScopeFilter를 래핑하여 Domain 계층에서 사용 가능하게 합니다.
        ScopeFilter의 검증 로직을 그대로 활용합니다.
        """

        def is_in_scope(self, url: str, target: Target) -> bool:
            """
            URL이 Target의 scope 내에 있는지 검증.

            Args:
                url: 검증할 URL
                target: Target 모델 (url, scope 속성 필요)

            Returns:
                True if URL is in scope
            """
            if not url or not target:
                return False

            filter = ScopeFilter(target.url, target.scope)
            return filter.is_in_scope(url)
    ```

- [ ] **Task 3.3**: Port 인터페이스 정의
  - File(s): `backend/app/infrastructure/ports/`
  - **중요**: 기존 서비스 API와 호환되는 인터페이스 설계
  - 구현 내용:
    ```python
    # crawler.py
    @dataclass
    class CrawlData:
        """크롤링 결과 데이터 (기존 tuple 반환값을 구조화)"""
        links: List[str]
        http_data: Dict[str, Any]
        js_contents: List[str]

    class ICrawler(Protocol):
        """크롤러 인터페이스 - CrawlerService.crawl()을 래핑"""
        async def crawl(self, url: str) -> CrawlData: ...

    # asset_repository.py
    class IAssetRepository(Protocol):
        """자산 저장소 인터페이스 - AssetService를 래핑"""
        async def save_batch(self, assets: list[Asset], task_id: int) -> int: ...
        async def find_by_hash(self, content_hash: str) -> Asset | None: ...

    # discovery.py
    class IDiscoveryService(Protocol):
        """
        Discovery 서비스 인터페이스.

        Note: 기존 DiscoveryService는 run() 메서드를 사용하므로
        어댑터가 run() → discover() 매핑을 수행합니다.
        또는 DiscoveryStage에서 직접 DiscoveryService.run()을 호출해도 됩니다.
        """
        async def discover(self, context: DiscoveryContext) -> list[DiscoveredAsset]: ...

    # cancellation.py
    class ICancellation(Protocol):
        """취소 확인 인터페이스 - Redis cancel flag 확인"""
        async def is_cancelled(self, task_id: int) -> bool: ...

    # task_queue.py (Phase 1에서 구현)
    class ITaskQueue(Protocol):
        """Task 큐 인터페이스 - 기존 TaskPriority 사용"""
        async def enqueue(self, task_data: dict, priority: TaskPriority) -> str: ...
        async def dequeue(self, timeout: float) -> Optional[Tuple[dict, str]]: ...
        async def ack(self, task_json: str) -> bool: ...
        async def nack(self, task_json: str, error: str, retry: bool) -> bool: ...
    ```

**🔵 REFACTOR: 코드 정리**

- [ ] **Task 3.4**: 코드 품질 개선
  - 체크리스트:
    - [ ] `__init__.py` 파일 정리
    - [ ] re-export 설정
    - [ ] 문서화

---

## ✋ Quality Gate

**⚠️ STOP: 모든 체크가 통과할 때까지 Phase 3로 진행하지 마세요**

### TDD 준수 (CRITICAL)
- [ ] **Red Phase**: 테스트를 먼저 작성하고 실패 확인
- [ ] **Green Phase**: 테스트를 통과시키는 최소 코드 작성
- [ ] **Refactor Phase**: 테스트 통과 상태에서 코드 개선
- [ ] **Coverage Check**: 테스트 커버리지 ≥95%

### 빌드 & 테스트
- [ ] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [ ] **All Tests Pass**: 100% 테스트 통과 (스킵 없음)
- [ ] **Test Performance**: 테스트 스위트 30초 이내 완료
- [ ] **No Flaky Tests**: 3회 이상 실행해도 일관된 결과

### 코드 품질
- [ ] **Linting**: ruff check 에러/경고 없음
- [ ] **Formatting**: ruff format으로 포맷팅됨
- [ ] **Type Safety**: mypy 통과
- [ ] **Static Analysis**: 심각한 이슈 없음

### 보안 & 성능
- [ ] **SSRF Tests**: 모든 SSRF 시나리오 테스트됨
- [ ] **Edge Cases**: 경계 조건 테스트됨

### 검증 명령어

```bash
# 테스트 실행
uv run pytest tests/unit/domain/ -v

# 커버리지 확인
uv run pytest tests/unit/domain/ --cov=app/domain --cov-report=term-missing

# 코드 품질
uv run ruff check app/domain/
uv run ruff format --check app/domain/
uv run mypy app/domain/
```

### 수동 테스트 체크리스트
- [ ] UrlValidator로 다양한 SSRF 페이로드 테스트
- [ ] DataTransformer 변환 결과 수동 검증
- [ ] ScopeChecker 범위 검증 수동 확인

---

## 📊 진행 상황

### 완료 상태
- **Day 1-2 (UrlValidator)**: ✅ 100%
- **Day 3-4 (DataTransformer)**: ✅ 100%
- **Day 5 (ScopeChecker + Ports)**: ✅ 100%

### 시간 추적
| 작업 | 예상 | 실제 | 차이 |
|------|------|------|------|
| UrlValidator | 16시간 | 완료 | - |
| DataTransformer | 16시간 | 완료 | - |
| ScopeChecker + Ports | 8시간 | 완료 | - |
| **합계** | 40시간 | 완료 | - |

---

## 📝 Notes & Learnings

### 구현 노트
- Domain Services 총 398줄 (domain/services/)
- Ports 5개 정의 (infrastructure/ports/)
- ScopeChecker는 기존 ScopeFilter 래핑

### 발생한 Blockers
- 없음

---

## 🔄 Phase 2 롤백 절차

Phase 2에서 문제 발생 시 롤백 절차:

### 롤백이 필요한 경우
- Domain Service 구현에 심각한 버그 발견
- 기존 CrawlWorker와의 호환성 문제
- 성능 저하 (예: UrlValidator가 너무 느림)

### 롤백 단계

1. **코드 롤백**:
   ```bash
   # Phase 2 시작 전 커밋으로 되돌리기
   git revert --no-commit HEAD~N..HEAD  # N = Phase 2 커밋 수
   git commit -m "revert: rollback Phase 2 Domain layer"
   ```

2. **삭제 대상** (Phase 2에서 생성된 파일):
   ```
   backend/app/domain/                  # 전체 디렉토리
   backend/tests/unit/domain/           # 테스트 디렉토리
   ```

3. **유지 대상**:
   - Phase 1에서 생성된 인프라 계층 (`infrastructure/`, `core/`)
   - 기존 `workers/crawl_worker.py` 변경 사항 없음

4. **검증**:
   ```bash
   # 기존 테스트가 모두 통과하는지 확인
   uv run pytest tests/workers/ -v
   uv run pytest tests/integration/ -v
   ```

### 영향 범위
- Phase 2만 롤백: Phase 1 인프라는 유지됨
- Phase 3 이후 진행 불가 (Domain 계층 의존)
- 기존 CrawlWorker는 영향 없음 (아직 변경 안 함)

---

**Phase Status**: ✅ Completed
**Completed**: 2025-01-29
**Next Phase**: Phase 3 (Pipeline 구조 구현 1)
