"""GuardStage 단위 테스트."""

import logging
from dataclasses import dataclass
from typing import Optional

import pytest

try:
    from app.application.stages.guard_stage import GuardStage
except ImportError:
    pytest.skip("guard_stage module not yet implemented", allow_module_level=True)


# ============================================================
# Mock classes for testing
# ============================================================


class MockUrlValidator:
    """테스트용 UrlValidator mock."""

    def __init__(self, is_safe: bool = True):
        self._is_safe = is_safe
        self.last_checked_url: Optional[str] = None

    def is_safe(self, url: Optional[str]) -> bool:
        self.last_checked_url = url
        return self._is_safe


class MockScopeChecker:
    """테스트용 ScopeChecker mock."""

    def __init__(self, in_scope: bool = True):
        self._in_scope = in_scope
        self.last_checked_url: Optional[str] = None

    def is_in_scope(self, url: Optional[str], target=None) -> bool:
        self.last_checked_url = url
        return self._in_scope


@dataclass
class MockTarget:
    """테스트용 Target mock."""

    id: int = 10
    url: str = "https://example.com"
    scope: str = "domain"


class MockPipelineContext:
    """테스트용 PipelineContext mock."""

    def __init__(
        self,
        crawl_url: str = "https://example.com",
        target: Optional[MockTarget] = None,
        is_cancelled: bool = False,
    ):
        self._crawl_url = crawl_url
        self.target = target or MockTarget()
        self._is_cancelled = is_cancelled

    @property
    def crawl_url(self) -> str:
        return self._crawl_url

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled


# ============================================================
# Tests
# ============================================================


class TestGuardStageProperties:
    """GuardStage 속성 테스트."""

    def test_stage_name_is_guard(self):
        """Stage name은 'guard'."""
        stage = GuardStage(
            url_validator=MockUrlValidator(), scope_checker=MockScopeChecker()
        )
        assert stage.name == "guard"

    def test_can_continue_on_error_is_false(self):
        """GuardStage 에러 시 계속 불가."""
        stage = GuardStage(
            url_validator=MockUrlValidator(), scope_checker=MockScopeChecker()
        )
        assert stage.can_continue_on_error is False


class TestGuardStageProcess:
    """GuardStage.process() 테스트."""

    @pytest.mark.asyncio
    async def test_returns_ok_for_safe_in_scope_url(self):
        """안전하고 범위 내 URL은 ok 반환."""
        stage = GuardStage(
            url_validator=MockUrlValidator(is_safe=True),
            scope_checker=MockScopeChecker(in_scope=True),
        )
        context = MockPipelineContext(crawl_url="https://example.com")
        result = await stage.process(context)

        assert result.success is True
        assert result.should_stop is False

    @pytest.mark.asyncio
    async def test_returns_stop_for_unsafe_url(self):
        """안전하지 않은 URL은 stop 반환."""
        stage = GuardStage(
            url_validator=MockUrlValidator(is_safe=False),
            scope_checker=MockScopeChecker(in_scope=True),
        )
        context = MockPipelineContext(crawl_url="http://localhost/admin")
        result = await stage.process(context)

        assert result.should_stop is True

    @pytest.mark.asyncio
    async def test_returns_stop_for_out_of_scope_url(self):
        """범위 외 URL은 stop 반환."""
        stage = GuardStage(
            url_validator=MockUrlValidator(is_safe=True),
            scope_checker=MockScopeChecker(in_scope=False),
        )
        context = MockPipelineContext(crawl_url="https://evil.com/")
        result = await stage.process(context)

        assert result.should_stop is True

    @pytest.mark.asyncio
    async def test_ssrf_check_before_scope_check(self):
        """SSRF 검사가 Scope 검사보다 먼저 실행."""
        validator = MockUrlValidator(is_safe=False)
        checker = MockScopeChecker(in_scope=False)
        stage = GuardStage(url_validator=validator, scope_checker=checker)

        context = MockPipelineContext(crawl_url="http://localhost/")
        await stage.process(context)

        # URL validator가 호출되었지만
        assert validator.last_checked_url == "http://localhost/"
        # scope checker는 호출되지 않아야 함 (SSRF에서 이미 차단)
        assert checker.last_checked_url is None

    @pytest.mark.asyncio
    async def test_passes_target_to_scope_checker(self):
        """target을 scope checker에 전달."""
        checker = MockScopeChecker(in_scope=True)
        stage = GuardStage(
            url_validator=MockUrlValidator(is_safe=True), scope_checker=checker
        )
        target = MockTarget(url="https://example.com")
        context = MockPipelineContext(
            crawl_url="https://example.com/page", target=target
        )
        await stage.process(context)

        assert checker.last_checked_url == "https://example.com/page"

    @pytest.mark.asyncio
    async def test_returns_stop_for_cancelled_context(self):
        """취소된 컨텍스트는 stop 반환."""
        stage = GuardStage(
            url_validator=MockUrlValidator(is_safe=True),
            scope_checker=MockScopeChecker(in_scope=True),
        )
        context = MockPipelineContext(
            crawl_url="https://example.com", is_cancelled=True
        )
        result = await stage.process(context)

        assert result.should_stop is True

    @pytest.mark.asyncio
    async def test_returns_stop_for_empty_url(self):
        """빈 URL은 stop 반환."""
        stage = GuardStage(
            url_validator=MockUrlValidator(is_safe=True),
            scope_checker=MockScopeChecker(in_scope=True),
        )
        context = MockPipelineContext(crawl_url="")
        result = await stage.process(context)

        assert result.should_stop is True


class TestGuardStageLogging:
    """GuardStage 로깅 테스트."""

    @pytest.mark.asyncio
    async def test_logs_blocked_unsafe_url(self, caplog):
        """안전하지 않은 URL 차단 시 로깅."""
        stage = GuardStage(
            url_validator=MockUrlValidator(is_safe=False),
            scope_checker=MockScopeChecker(in_scope=True),
        )
        context = MockPipelineContext(crawl_url="http://localhost/")

        with caplog.at_level(logging.WARNING):
            await stage.process(context)

        assert any(
            "unsafe" in record.message.lower() or "blocked" in record.message.lower()
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logs_out_of_scope_url(self, caplog):
        """범위 외 URL 시 로깅."""
        stage = GuardStage(
            url_validator=MockUrlValidator(is_safe=True),
            scope_checker=MockScopeChecker(in_scope=False),
        )
        context = MockPipelineContext(crawl_url="https://evil.com/")

        with caplog.at_level(logging.INFO):
            await stage.process(context)

        assert any("scope" in record.message.lower() for record in caplog.records)
