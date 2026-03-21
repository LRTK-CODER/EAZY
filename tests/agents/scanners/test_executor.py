"""Tests for ScannerExecutor — parallel plugin execution."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from src.agents.scanners.base import ScannerPlugin
from src.agents.scanners.executor import ScannerExecutor

# ---------------------------------------------------------------------------
# Mock scanner plugins
# ---------------------------------------------------------------------------


class _FastScanner(ScannerPlugin):
    """Returns a fixed result instantly."""

    def __init__(
        self, category_name: str, scanner_name: str, result: dict[str, Any]
    ) -> None:
        self._category = category_name
        self._name = scanner_name
        self._result = result

    @property
    def category(self) -> str:
        return self._category

    @property
    def name(self) -> str:
        return self._name

    async def scan(self, target: str, config: dict[str, Any]) -> dict[str, Any]:
        return self._result

    def parse_output(self, raw: str) -> dict[str, Any]:
        return {"parsed": raw}


class _SlowScanner(ScannerPlugin):
    """Sleeps for a given delay before returning."""

    def __init__(self, category_name: str, scanner_name: str, delay: float) -> None:
        self._category = category_name
        self._name = scanner_name
        self._delay = delay

    @property
    def category(self) -> str:
        return self._category

    @property
    def name(self) -> str:
        return self._name

    async def scan(self, target: str, config: dict[str, Any]) -> dict[str, Any]:
        await asyncio.sleep(self._delay)
        return {"delayed": self._delay}

    def parse_output(self, raw: str) -> dict[str, Any]:
        return {"parsed": raw}


class _FailingScanner(ScannerPlugin):
    """Raises an exception on scan."""

    def __init__(self, category_name: str, scanner_name: str, exc: Exception) -> None:
        self._category = category_name
        self._name = scanner_name
        self._exc = exc

    @property
    def category(self) -> str:
        return self._category

    @property
    def name(self) -> str:
        return self._name

    async def scan(self, target: str, config: dict[str, Any]) -> dict[str, Any]:
        raise self._exc

    def parse_output(self, raw: str) -> dict[str, Any]:
        return {"parsed": raw}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestScannerExecutor:
    @pytest.mark.asyncio
    async def test_execute_with_active_plugins_returns_results(self) -> None:
        plugins: list[ScannerPlugin] = [
            _FastScanner("js_analysis", "js_scanner", {"found": 3}),
            _FastScanner("osint", "whois", {"domain": "example.com"}),
            _FastScanner("js_analysis", "js_lint", {"errors": 0}),
        ]
        executor = ScannerExecutor(plugins)
        result = await executor.execute("https://example.com")

        assert "js_analysis" in result.results_by_category
        assert "osint" in result.results_by_category
        assert len(result.results_by_category["js_analysis"]) == 2
        assert len(result.results_by_category["osint"]) == 1

    @pytest.mark.asyncio
    async def test_execute_no_plugins_returns_empty(self) -> None:
        executor = ScannerExecutor([])
        result = await executor.execute("https://example.com")

        assert result.results_by_category == {}
        assert result.plugin_statuses == []
        assert result.elapsed_time >= 0

    @pytest.mark.asyncio
    async def test_execute_failing_plugin_isolates_error(self) -> None:
        plugins: list[ScannerPlugin] = [
            _FailingScanner("osint", "bad_scanner", RuntimeError("boom")),
            _FastScanner("js_analysis", "good_scanner", {"ok": True}),
        ]
        executor = ScannerExecutor(plugins)
        result = await executor.execute("https://example.com")

        assert "js_analysis" in result.results_by_category
        assert len(result.results_by_category["js_analysis"]) == 1

    @pytest.mark.asyncio
    async def test_execute_records_plugin_status(self) -> None:
        plugins: list[ScannerPlugin] = [
            _FastScanner("osint", "good_one", {"ok": True}),
            _FailingScanner("js_analysis", "bad_one", ValueError("fail")),
        ]
        executor = ScannerExecutor(plugins)
        result = await executor.execute("https://example.com")

        statuses = {s.plugin_name: s for s in result.plugin_statuses}
        assert statuses["good_one"].success is True
        assert statuses["good_one"].error is None
        assert statuses["bad_one"].success is False
        assert statuses["bad_one"].error is not None

    @pytest.mark.asyncio
    async def test_execute_records_elapsed_time(self) -> None:
        plugins: list[ScannerPlugin] = [
            _FastScanner("osint", "fast", {"ok": True}),
        ]
        executor = ScannerExecutor(plugins)
        result = await executor.execute("https://example.com")

        assert result.elapsed_time >= 0

    @pytest.mark.asyncio
    async def test_execute_runs_plugins_concurrently(self) -> None:
        plugins: list[ScannerPlugin] = [
            _SlowScanner("osint", "slow1", 0.1),
            _SlowScanner("js_analysis", "slow2", 0.1),
            _SlowScanner("directory", "slow3", 0.1),
        ]
        executor = ScannerExecutor(plugins)
        result = await executor.execute("https://example.com")

        # If sequential: >= 0.3s. If parallel: ~0.1s
        assert result.elapsed_time < 0.3

    @pytest.mark.asyncio
    async def test_execute_result_contains_category_key(self) -> None:
        plugins: list[ScannerPlugin] = [
            _FastScanner("tech_stack", "tech1", {"framework": "django"}),
            _FastScanner("error_pattern", "err1", {"pattern": "500"}),
        ]
        executor = ScannerExecutor(plugins)
        result = await executor.execute("https://example.com")

        assert set(result.results_by_category.keys()) == {"tech_stack", "error_pattern"}
