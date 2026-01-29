# Phase 3: Pipeline 구조 구현 (1)

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
PipelineStage 인터페이스와 첫 번째 Stage들(GuardStage, CrawlStage)을 구현하여 파이프라인의 기초를 마련합니다.

### 성공 기준
- [x] PipelineStage 추상 클래스 정의
- [x] PipelineContext가 Stage 간 데이터 전달
- [x] GuardStage가 SSRF 및 Scope 검증 수행
- [x] CrawlStage가 Playwright 크롤링 실행
- [x] 각 Stage의 단위 테스트 커버리지 ≥90%
- [x] Stage 간 통합 테스트 통과

### 사용자 영향
- 모듈화된 검증 로직
- 더 명확한 에러 메시지
- 단계별 로깅으로 디버깅 용이

---

## 🏗️ 아키텍처 결정

| 결정 | 이유 | 트레이드오프 |
|------|------|------------|
| Stage별 책임 분리 | 단일 책임 원칙, 테스트 용이 | Stage 간 데이터 전달 필요 |
| StageResult 반환 타입 | 명확한 결과 표현, 흐름 제어 | 추가 타입 정의 |
| Context 패턴 | Stage 간 상태 공유 | 암묵적 의존성 |

---

## 📦 의존성

### 시작 전 필요 사항
- [ ] Phase 2 완료 (모든 Quality Gate 통과)
- [ ] UrlValidator, DataTransformer, ScopeChecker 구현 완료
- [ ] Port 인터페이스 정의 완료

### 외부 의존성
- playwright>=1.42.0 (이미 설치됨)

---

## 🧪 테스트 전략

### 테스트 접근법
**TDD 원칙**: 테스트를 먼저 작성하고, 테스트를 통과시키는 구현을 작성

### 이 Phase의 테스트 피라미드
| 테스트 유형 | 커버리지 목표 | 목적 |
|------------|--------------|------|
| **단위 테스트** | ≥90% | PipelineStage, PipelineContext, 각 Stage |
| **통합 테스트** | Critical paths | Stage 간 연동 |

### 테스트 파일 구조
```
backend/tests/
├── unit/
│   └── application/
│       ├── stages/
│       │   ├── test_base_stage.py
│       │   ├── test_guard_stage.py
│       │   └── test_crawl_stage.py
│       └── context/
│           └── test_pipeline_context.py
├── integration/
│   └── application/
│       └── test_stages_integration.py
└── conftest.py  # 공통 mock/fixture 정의
```

### Mock 및 Helper 유틸리티 정의

테스트에서 사용할 공통 mock 객체와 helper 함수를 정의합니다.

**File**: `tests/conftest.py` (또는 `tests/unit/application/conftest.py`)

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
import logging

from app.infrastructure.ports.crawler import CrawlData
from app.models.target import Target, TargetScope
from app.models.task import Task, TaskType, TaskStatus

# ============================================================
# Mock Data Classes
# ============================================================

@dataclass
class MockCrawlData:
    """테스트용 CrawlData mock"""
    links: List[str] = field(default_factory=list)
    http_data: Dict[str, Any] = field(default_factory=dict)
    js_contents: List[str] = field(default_factory=list)

    def to_crawl_data(self) -> CrawlData:
        return CrawlData(
            links=self.links,
            http_data=self.http_data,
            js_contents=self.js_contents,
        )


@dataclass
class MockTask:
    """테스트용 Task mock"""
    id: int = 1
    target_id: int = 10
    project_id: int = 1
    task_type: TaskType = TaskType.CRAWL
    status: TaskStatus = TaskStatus.PENDING
    depth: int = 0
    max_depth: int = 3
    crawl_url: Optional[str] = None


@dataclass
class MockTarget:
    """테스트용 Target mock"""
    id: int = 10
    project_id: int = 1
    url: str = "https://example.com"
    scope: TargetScope = TargetScope.DOMAIN


# ============================================================
# Mock Services
# ============================================================

class MockUrlValidator:
    """테스트용 UrlValidator mock"""
    def __init__(self, is_safe: bool = True):
        self._is_safe = is_safe

    def is_safe(self, url: str) -> bool:
        return self._is_safe


class MockScopeChecker:
    """테스트용 ScopeChecker mock"""
    def __init__(self, in_scope: bool = True):
        self._in_scope = in_scope

    def is_in_scope(self, url: str, target: Target) -> bool:
        return self._in_scope


class MockCrawler:
    """테스트용 ICrawler mock"""
    def __init__(
        self,
        links: List[str] = None,
        http_data: Dict[str, Any] = None,
        js_contents: List[str] = None,
        raises: Exception = None,
    ):
        self.links = links or []
        self.http_data = http_data or {}
        self.js_contents = js_contents or []
        self.raises = raises
        self.crawl_called = False

    async def crawl(self, url: str) -> CrawlData:
        self.crawl_called = True
        if self.raises:
            raise self.raises
        return CrawlData(
            links=self.links,
            http_data=self.http_data,
            js_contents=self.js_contents,
        )


class MockPipelineContext:
    """
    테스트용 PipelineContext mock.

    실제 PipelineContext의 주요 기능을 모방하며,
    테스트에서 의존성 없이 Stage를 검증할 수 있게 합니다.
    """
    def __init__(
        self,
        task: Optional[MockTask] = None,
        target: Optional[MockTarget] = None,
        crawl_url: str = "https://example.com",
        is_cancelled: bool = False,
    ):
        self.task = task or MockTask()
        self.target = target or MockTarget()
        self._crawl_url = crawl_url
        self._is_cancelled = is_cancelled
        self.crawl_data: Optional[CrawlData] = None
        self.discovered_assets: List[Any] = []
        self.saved_count: int = 0
        self.child_tasks_spawned: int = 0
        self.errors: List[tuple] = []

    @property
    def crawl_url(self) -> str:
        return self._crawl_url or self.target.url

    @property
    def target_id(self) -> int:
        return self.target.id

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def mark_cancelled(self) -> None:
        self._is_cancelled = True

    def set_crawl_data(self, data: CrawlData) -> None:
        self.crawl_data = data

    def set_discovered_assets(self, assets: List[Any]) -> None:
        self.discovered_assets = assets

    def set_saved_count(self, count: int) -> None:
        self.saved_count = count

    def set_child_tasks_spawned(self, count: int) -> None:
        self.child_tasks_spawned = count

    def add_error(self, stage_name: str, error: Exception) -> None:
        self.errors.append((stage_name, error))


# ============================================================
# Helper Functions
# ============================================================

@contextmanager
def capture_logs(logger_name: str = None, level: int = logging.INFO):
    """
    로그 캡처 helper.

    Usage:
        with capture_logs() as logs:
            some_function()
        assert any("expected" in log for log in logs)
    """
    import io

    handler = logging.StreamHandler(io.StringIO())
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter('%(message)s'))

    logger = logging.getLogger(logger_name)
    original_level = logger.level
    logger.setLevel(level)
    logger.addHandler(handler)

    logs = []

    try:
        yield logs
    finally:
        handler.stream.seek(0)
        logs.extend(handler.stream.read().splitlines())
        logger.removeHandler(handler)
        logger.setLevel(original_level)


# ============================================================
# Pytest Fixtures
# ============================================================

import pytest

@pytest.fixture
def mock_task():
    """기본 MockTask fixture"""
    return MockTask()


@pytest.fixture
def mock_target():
    """기본 MockTarget fixture"""
    return MockTarget()


@pytest.fixture
def mock_crawl_data():
    """기본 MockCrawlData fixture"""
    return MockCrawlData(
        links=["https://example.com/page1", "https://example.com/page2"],
        http_data={
            "https://example.com": {
                "response": {"status": 200, "body": "<html></html>"}
            }
        },
        js_contents=["console.log('test')"],
    )
```

---

## 🚀 구현 작업

### Day 1-2: PipelineStage 인터페이스 및 PipelineContext

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 1.1**: PipelineStage 인터페이스 테스트 작성
  - File(s): `tests/unit/application/stages/test_base_stage.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    class TestPipelineStage:
        def test_stage_has_name_property(self):
            """Stage는 name 속성을 가져야 함"""
            class TestStage(PipelineStage):
                @property
                def name(self) -> str:
                    return "test"

                async def process(self, context):
                    return StageResult.ok()

            stage = TestStage()
            assert stage.name == "test"

        def test_stage_has_can_continue_on_error_default_false(self):
            """can_continue_on_error 기본값은 False"""
            class TestStage(PipelineStage):
                @property
                def name(self) -> str:
                    return "test"

                async def process(self, context):
                    return StageResult.ok()

            stage = TestStage()
            assert stage.can_continue_on_error is False


    class TestStageResult:
        def test_ok_creates_success_result(self):
            """ok()는 성공 결과 생성"""
            result = StageResult.ok()
            assert result.success is True
            assert result.should_stop is False

        def test_stop_creates_stop_result(self):
            """stop()은 중지 결과 생성"""
            result = StageResult.stop("reason")
            assert result.success is True
            assert result.should_stop is True

        def test_fail_creates_failure_result(self):
            """fail()은 실패 결과 생성"""
            result = StageResult.fail("error message")
            assert result.success is False
            assert result.should_stop is True
            assert result.error == "error message"
    ```

- [ ] **Test 1.2**: PipelineContext 테스트 작성
  - File(s): `tests/unit/application/context/test_pipeline_context.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    class TestPipelineContext:
        def test_context_initializes_with_task_and_target(self):
            """Context는 task와 target_id로 초기화"""
            task = MockTask(id=1)
            context = PipelineContext(task=task, target_id=10)
            assert context.task == task
            assert context.target_id == 10

        async def test_load_target_fetches_target(self):
            """load_target()는 Target을 조회"""
            context = PipelineContext(task=MockTask(), target_id=10)
            context.set_session(mock_session)
            await context.load_target()
            assert context.target is not None

        def test_set_crawl_data(self):
            """set_crawl_data()는 크롤 데이터 저장"""
            context = PipelineContext(task=MockTask(), target_id=10)
            crawl_data = MockCrawlData()
            context.set_crawl_data(crawl_data)
            assert context.crawl_data == crawl_data

        def test_crawl_url_returns_task_url_or_target_url(self):
            """crawl_url은 task.crawl_url 또는 target.url 반환"""
            task = MockTask(crawl_url="https://child.com")
            target = MockTarget(url="https://parent.com")
            context = PipelineContext(task=task, target_id=10)
            context._target = target
            assert context.crawl_url == "https://child.com"

            task2 = MockTask(crawl_url=None)
            context2 = PipelineContext(task=task2, target_id=10)
            context2._target = target
            assert context2.crawl_url == "https://parent.com"

        def test_mark_cancelled(self):
            """mark_cancelled()는 취소 상태 설정"""
            context = PipelineContext(task=MockTask(), target_id=10)
            context.mark_cancelled()
            assert context.is_cancelled is True

        def test_add_error(self):
            """add_error()는 에러 기록"""
            context = PipelineContext(task=MockTask(), target_id=10)
            context.add_error("stage_name", ValueError("test"))
            assert len(context.errors) == 1

        def test_to_result_returns_orchestrator_result(self):
            """to_result()는 OrchestratorResult 반환"""
            context = PipelineContext(task=MockTask(), target_id=10)
            context.set_saved_count(5)
            context.set_child_tasks_spawned(3)
            result = context.to_result()
            assert result.saved_assets == 5
            assert result.child_tasks_spawned == 3
    ```

**🟢 GREEN: 테스트를 통과시키는 구현**

- [ ] **Task 1.3**: PipelineStage 인터페이스 구현
  - File(s): `backend/app/application/stages/base.py`
  - 목표: Test 1.1 통과
  - 구현 내용:
    ```python
    from abc import ABC, abstractmethod
    from dataclasses import dataclass
    from typing import Optional

    @dataclass
    class StageResult:
        success: bool
        should_stop: bool = False
        error: Optional[str] = None

        @classmethod
        def ok(cls) -> "StageResult":
            return cls(success=True)

        @classmethod
        def stop(cls, reason: str = "") -> "StageResult":
            return cls(success=True, should_stop=True)

        @classmethod
        def fail(cls, error: str) -> "StageResult":
            return cls(success=False, should_stop=True, error=error)


    class PipelineStage(ABC):
        @property
        @abstractmethod
        def name(self) -> str:
            pass

        @property
        def can_continue_on_error(self) -> bool:
            return False

        @abstractmethod
        async def process(self, context: "PipelineContext") -> StageResult:
            pass
    ```

- [ ] **Task 1.4**: PipelineContext 구현
  - File(s): `backend/app/application/context/pipeline_context.py`
  - 목표: Test 1.2 통과

**🔵 REFACTOR: 코드 정리**

- [ ] **Task 1.5**: 코드 품질 개선
  - 체크리스트:
    - [ ] 타입 힌트 완성
    - [ ] Docstring 추가
    - [ ] `__init__.py` 정리

---

### Day 3-4: GuardStage 구현

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 2.1**: GuardStage 단위 테스트 작성
  - File(s): `tests/unit/application/stages/test_guard_stage.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    class TestGuardStage:
        async def test_returns_ok_for_safe_in_scope_url(self):
            """안전하고 범위 내 URL은 ok 반환"""
            validator = MockUrlValidator(is_safe=True)
            checker = MockScopeChecker(in_scope=True)
            stage = GuardStage(url_validator=validator, scope_checker=checker)

            context = MockPipelineContext(crawl_url="https://example.com")
            result = await stage.process(context)

            assert result.success is True
            assert result.should_stop is False

        async def test_returns_stop_for_unsafe_url(self):
            """안전하지 않은 URL은 stop 반환"""
            validator = MockUrlValidator(is_safe=False)
            checker = MockScopeChecker(in_scope=True)
            stage = GuardStage(url_validator=validator, scope_checker=checker)

            context = MockPipelineContext(crawl_url="http://localhost/")
            result = await stage.process(context)

            assert result.should_stop is True

        async def test_returns_stop_for_out_of_scope_url(self):
            """범위 외 URL은 stop 반환"""
            validator = MockUrlValidator(is_safe=True)
            checker = MockScopeChecker(in_scope=False)
            stage = GuardStage(url_validator=validator, scope_checker=checker)

            context = MockPipelineContext(crawl_url="https://evil.com/")
            result = await stage.process(context)

            assert result.should_stop is True

        async def test_logs_blocked_urls(self):
            """차단된 URL 로깅"""
            validator = MockUrlValidator(is_safe=False)
            checker = MockScopeChecker(in_scope=True)
            stage = GuardStage(url_validator=validator, scope_checker=checker)

            context = MockPipelineContext(crawl_url="http://localhost/")
            with capture_logs() as logs:
                await stage.process(context)

            assert any("blocked" in log.lower() for log in logs)

        async def test_stage_name_is_guard(self):
            """Stage name은 'guard'"""
            stage = GuardStage(MockUrlValidator(), MockScopeChecker())
            assert stage.name == "guard"

        async def test_can_continue_on_error_is_false(self):
            """GuardStage 에러 시 계속 불가"""
            stage = GuardStage(MockUrlValidator(), MockScopeChecker())
            assert stage.can_continue_on_error is False
    ```

**🟢 GREEN: 테스트를 통과시키는 구현**

- [ ] **Task 2.2**: GuardStage 클래스 구현
  - File(s): `backend/app/application/stages/guard_stage.py`
  - 목표: Test 2.1 통과
  - 구현 내용:
    ```python
    from app.application.stages.base import PipelineStage, StageResult
    from app.domain.services.url_validator import UrlValidator
    from app.domain.services.scope_checker import ScopeChecker

    class GuardStage(PipelineStage):
        """보안 검증 Stage (SSRF, Scope)"""

        def __init__(
            self,
            url_validator: UrlValidator | None = None,
            scope_checker: ScopeChecker | None = None,
        ):
            self._url_validator = url_validator or UrlValidator()
            self._scope_checker = scope_checker or ScopeChecker()

        @property
        def name(self) -> str:
            return "guard"

        async def process(self, context: PipelineContext) -> StageResult:
            url = context.crawl_url

            # SSRF 검증
            if not self._url_validator.is_safe(url):
                logger.warning("Blocked unsafe URL", url=url)
                return StageResult.stop(f"Unsafe URL blocked: {url}")

            # Scope 검증
            if not self._scope_checker.is_in_scope(url, context.target):
                logger.info("URL out of scope", url=url)
                return StageResult.stop(f"URL out of scope: {url}")

            return StageResult.ok()
    ```

**🔵 REFACTOR: 코드 정리**

- [ ] **Task 2.3**: 코드 품질 개선
  - 체크리스트:
    - [ ] 구조화된 로깅 추가
    - [ ] ValidationResult 상세 정보 포함

---

### Day 5: CrawlStage 구현

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 3.1**: CrawlStage 단위 테스트 작성
  - File(s): `tests/unit/application/stages/test_crawl_stage.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    class TestCrawlStage:
        async def test_crawls_url_and_stores_data(self):
            """URL 크롤링 후 데이터 저장"""
            mock_crawler = MockCrawler(
                links=["https://example.com/page1"],
                http_data={"responses": []},
                js_contents=["console.log('test')"],
            )
            stage = CrawlStage(crawler=mock_crawler)

            context = MockPipelineContext(crawl_url="https://example.com")
            result = await stage.process(context)

            assert result.success is True
            assert context.crawl_data is not None
            assert len(context.crawl_data.links) == 1

        async def test_returns_failure_on_crawler_exception(self):
            """크롤러 예외 시 실패 반환"""
            mock_crawler = MockCrawler(raises=Exception("Connection timeout"))
            stage = CrawlStage(crawler=mock_crawler)

            context = MockPipelineContext(crawl_url="https://example.com")
            result = await stage.process(context)

            assert result.success is False
            assert "timeout" in result.error.lower()

        async def test_stage_name_is_crawl(self):
            """Stage name은 'crawl'"""
            stage = CrawlStage(MockCrawler())
            assert stage.name == "crawl"

        async def test_can_continue_on_error_is_false(self):
            """CrawlStage 에러 시 계속 불가"""
            stage = CrawlStage(MockCrawler())
            assert stage.can_continue_on_error is False

        async def test_logs_crawl_duration(self):
            """크롤 소요 시간 로깅"""
            mock_crawler = MockCrawler(links=[], http_data={}, js_contents=[])
            stage = CrawlStage(crawler=mock_crawler)

            context = MockPipelineContext(crawl_url="https://example.com")
            with capture_logs() as logs:
                await stage.process(context)

            assert any("duration" in log.lower() for log in logs)
    ```

**🟢 GREEN: 테스트를 통과시키는 구현**

- [ ] **Task 3.2**: CrawlStage 클래스 구현
  - File(s): `backend/app/application/stages/crawl_stage.py`
  - 목표: Test 3.1 통과
  - **중요**: 기존 `CrawlerService`를 `PlaywrightCrawlerAdapter`로 래핑하여 `ICrawler` 인터페이스 사용
  - 구현 내용:
    ```python
    from app.application.stages.base import PipelineStage, StageResult
    from app.infrastructure.ports.crawler import ICrawler, CrawlData
    from app.infrastructure.adapters.playwright_crawler import PlaywrightCrawlerAdapter
    from app.services.crawler_service import CrawlerService

    class CrawlStage(PipelineStage):
        """웹 크롤링 Stage"""

        def __init__(self, crawler: ICrawler | None = None):
            # 기존 CrawlerService를 어댑터로 래핑
            self._crawler = crawler or PlaywrightCrawlerAdapter(CrawlerService())

        @property
        def name(self) -> str:
            return "crawl"

        async def process(self, context: PipelineContext) -> StageResult:
            url = context.crawl_url
            start_time = time.time()

            try:
                # ICrawler.crawl()은 CrawlData를 반환
                crawl_data = await self._crawler.crawl(url)
                context.set_crawl_data(crawl_data)

                duration = time.time() - start_time
                logger.info("Crawl completed", url=url, duration_ms=duration * 1000)

                return StageResult.ok()

            except Exception as e:
                logger.error("Crawl failed", url=url, error=str(e))
                return StageResult.fail(f"Crawl failed: {str(e)}")
    ```

  **PlaywrightCrawlerAdapter 구현** (`infrastructure/adapters/playwright_crawler.py`):
  ```python
  from app.infrastructure.ports.crawler import ICrawler, CrawlData
  from app.services.crawler_service import CrawlerService

  class PlaywrightCrawlerAdapter:
      """기존 CrawlerService를 ICrawler 인터페이스로 래핑"""

      def __init__(self, crawler_service: CrawlerService | None = None):
          self._crawler = crawler_service or CrawlerService()

      async def crawl(self, url: str) -> CrawlData:
          # 기존 API: Tuple[List[str], Dict, List[str]] 반환
          links, http_data, js_contents = await self._crawler.crawl(url)
          # 새 API: CrawlData 반환
          return CrawlData(
              links=links,
              http_data=http_data,
              js_contents=js_contents,
          )
  ```

- [ ] **Task 3.3**: Stage 통합 테스트 작성
  - File(s): `tests/integration/application/test_stages_integration.py`
  - 테스트 케이스:
    - GuardStage → CrawlStage 연동

**🔵 REFACTOR: 코드 정리**

- [ ] **Task 3.4**: 코드 품질 개선
  - 체크리스트:
    - [ ] 에러 타입별 처리 분리
    - [ ] Retry 로직 고려
    - [ ] Timeout 설정

---

## ✋ Quality Gate

**⚠️ STOP: 모든 체크가 통과할 때까지 Phase 4로 진행하지 마세요**

### TDD 준수 (CRITICAL)
- [ ] **Red Phase**: 테스트를 먼저 작성하고 실패 확인
- [ ] **Green Phase**: 테스트를 통과시키는 최소 코드 작성
- [ ] **Refactor Phase**: 테스트 통과 상태에서 코드 개선
- [ ] **Coverage Check**: 테스트 커버리지 ≥90%

### 빌드 & 테스트
- [ ] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [ ] **All Tests Pass**: 100% 테스트 통과 (스킵 없음)
- [ ] **Test Performance**: 테스트 스위트 30초 이내 완료
- [ ] **No Flaky Tests**: 3회 이상 실행해도 일관된 결과

### 코드 품질
- [ ] **Linting**: ruff check 에러/경고 없음
- [ ] **Formatting**: ruff format으로 포맷팅됨
- [ ] **Type Safety**: mypy 통과

### 검증 명령어

```bash
# 테스트 실행
uv run pytest tests/unit/application/ -v

# 커버리지 확인
uv run pytest tests/unit/application/ --cov=app/application --cov-report=term-missing

# 통합 테스트
uv run pytest tests/integration/application/ -v

# 코드 품질
uv run ruff check app/application/
uv run mypy app/application/
```

### 수동 테스트 체크리스트
- [ ] GuardStage로 SSRF URL 테스트
- [ ] CrawlStage로 실제 URL 크롤링 테스트
- [ ] Stage 간 Context 전달 확인

---

## 📊 진행 상황

### 완료 상태
- **Day 1-2 (Base + Context)**: ✅ 100%
- **Day 3-4 (GuardStage)**: ✅ 100%
- **Day 5 (CrawlStage)**: ✅ 100%

### 시간 추적
| 작업 | 예상 | 실제 | 차이 |
|------|------|------|------|
| Base + Context | 16시간 | 완료 | - |
| GuardStage | 16시간 | 완료 | - |
| CrawlStage | 8시간 | 완료 | - |
| **합계** | 40시간 | 완료 | - |

---

## 🔄 Phase 3 롤백 절차

Phase 3에서 문제 발생 시 롤백 절차:

### 롤백이 필요한 경우
- Pipeline Stage 설계에 근본적인 문제 발견
- GuardStage/CrawlStage 통합 실패
- 성능 병목 발생

### 롤백 단계

1. **코드 롤백**:
   ```bash
   git revert --no-commit HEAD~N..HEAD  # N = Phase 3 커밋 수
   git commit -m "revert: rollback Phase 3 Pipeline stages"
   ```

2. **삭제 대상** (Phase 3에서 생성된 파일):
   ```
   backend/app/application/stages/      # Stage 구현
   backend/app/application/context/     # PipelineContext
   backend/tests/unit/application/      # 단위 테스트
   backend/tests/integration/application/  # 통합 테스트
   ```

3. **유지 대상**:
   - Phase 1 인프라 (`infrastructure/`, `core/`)
   - Phase 2 Domain 계층 (`domain/`)
   - 기존 `workers/crawl_worker.py` (변경 없음)

4. **검증**:
   ```bash
   uv run pytest tests/unit/domain/ -v
   uv run pytest tests/workers/ -v
   ```

### 영향 범위
- Phase 3만 롤백: Phase 1-2는 유지됨
- Phase 4-5 진행 불가
- Domain Service는 독립적으로 사용 가능

---

**Phase Status**: ✅ Completed
**Completed**: 2025-01-29
**Next Phase**: Phase 4 (Pipeline 구조 구현 2)
