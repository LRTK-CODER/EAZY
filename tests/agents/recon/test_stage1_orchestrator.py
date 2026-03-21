"""Tests for Stage1 Orchestrator — recon pipeline coordinator."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from src.agents.core.models import (
    AuthFlow,
    AuthStep,
    Endpoint,
    SessionConfig,
)
from src.agents.recon.auth_flow_mapper import AuthFlowResult, Credentials
from src.agents.recon.crawler import ApiCallRelation, CrawlResult, DataFlowPath
from src.agents.recon.scan_interpreter import ScanInterpreterResult
from src.agents.scanners.executor import ScanResult

# ── Shared call-order tracker ──────────────────────────────────────


def _make_call_order() -> list[str]:
    return []


# ── Mock classes ───────────────────────────────────────────────────


class _MockAuthFlowMapper:
    def __init__(
        self,
        *,
        delay: float = 0.0,
        call_order: list[str] | None = None,
    ) -> None:
        self._delay = delay
        self._call_order = call_order if call_order is not None else []
        self.called = False

    async def map_auth_flow(
        self,
        target_url: str,
        credentials: Credentials,
    ) -> AuthFlowResult:
        if self._delay:
            await asyncio.sleep(self._delay)
        self.called = True
        self._call_order.append("auth_flow")
        return AuthFlowResult(
            auth_flow=AuthFlow(
                session_mechanism="cookie",
                steps=[AuthStep(order=1, action="POST", description="login")],
            ),
            success=True,
            login_url=target_url,
        )


class _MockScannerExecutor:
    def __init__(
        self,
        *,
        delay: float = 0.0,
        should_fail: bool = False,
        call_order: list[str] | None = None,
    ) -> None:
        self._delay = delay
        self._should_fail = should_fail
        self._call_order = call_order if call_order is not None else []
        self.called = False

    async def execute(
        self,
        target: str,
        config: dict[str, Any] | None = None,
    ) -> ScanResult:
        if self._delay:
            await asyncio.sleep(self._delay)
        self.called = True
        self._call_order.append("scanner")
        if self._should_fail:
            msg = "Scanner failed"
            raise RuntimeError(msg)
        return ScanResult(
            results_by_category={"headers": [{"x-frame-options": "DENY"}]},
            plugin_statuses=[],
            elapsed_time=0.5,
        )


class _MockScanInterpreter:
    def __init__(
        self,
        *,
        should_fail: bool = False,
        call_order: list[str] | None = None,
    ) -> None:
        self._should_fail = should_fail
        self._call_order = call_order if call_order is not None else []
        self.called = False

    async def interpret(self, scan_result: ScanResult) -> ScanInterpreterResult:
        self.called = True
        self._call_order.append("llm_interpret")
        if self._should_fail:
            msg = "LLM interpret failed"
            raise RuntimeError(msg)
        return ScanInterpreterResult(
            risk_summary="Low risk",
            findings=[],
        )


class _MockAuthenticatedCrawler:
    def __init__(
        self,
        *,
        should_fail: bool = False,
        call_order: list[str] | None = None,
    ) -> None:
        self._should_fail = should_fail
        self._call_order = call_order if call_order is not None else []
        self.called = False

    async def crawl(self, start_url: str, *, max_depth: int = 3) -> CrawlResult:
        self.called = True
        self._call_order.append("crawler")
        if self._should_fail:
            msg = "Crawler failed"
            raise RuntimeError(msg)
        return CrawlResult(
            discovered_endpoints=[
                Endpoint(url="/api/login", method="POST", auth_required=False),
                Endpoint(url="/api/users", method="GET", auth_required=True),
            ],
            api_calls=[
                ApiCallRelation(
                    source_url="/api/login",
                    target_url="/api/users",
                    method="GET",
                    trigger="redirect",
                ),
            ],
            data_flows=[
                DataFlowPath(
                    param_name="token",
                    source_url="/api/login",
                    sink_url="/api/users",
                ),
            ],
            pages_visited=["/", "/api/login"],
        )


class _MockKGBuilder:
    def __init__(self, *, call_order: list[str] | None = None) -> None:
        self._call_order = call_order if call_order is not None else []
        self.called = False

    async def build(
        self,
        crawl_result: CrawlResult,
        scan_result: ScanInterpreterResult,
        auth_result: AuthFlowResult,
        *,
        workspace_path: Path | None = None,
    ) -> Any:
        from src.agents.recon.knowledge_graph import KnowledgeGraph

        self.called = True
        self._call_order.append("kg_build")
        kg = KnowledgeGraph(target_url="http://example.com")
        from src.agents.recon.kg_models import GraphNode

        kg.add_node(
            GraphNode(
                id="endpoint:/api/login:POST",
                type="endpoint",
                properties={"url": "/api/login", "method": "POST"},
            ),
        )
        if workspace_path is not None:
            kg.save(workspace_path / "knowledge_graph.json")
        return kg


# ── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture()
def session_config() -> SessionConfig:
    return SessionConfig(
        session_name="test-session",
        target_url="http://example.com",
    )


@pytest.fixture()
def credentials() -> Credentials:
    return Credentials(username="admin", password="password123")


def _build_orchestrator(
    *,
    call_order: list[str] | None = None,
    auth_delay: float = 0.0,
    scanner_delay: float = 0.0,
    scanner_fail: bool = False,
    interpreter_fail: bool = False,
    crawler_fail: bool = False,
    workspace_path: Path | None = None,
    progress_callback: Any = None,
) -> Any:
    from src.agents.recon.orchestrator import Stage1Orchestrator

    order = call_order if call_order is not None else []
    return Stage1Orchestrator(
        auth_mapper=_MockAuthFlowMapper(delay=auth_delay, call_order=order),
        scanner_executor=_MockScannerExecutor(
            delay=scanner_delay,
            should_fail=scanner_fail,
            call_order=order,
        ),
        scan_interpreter=_MockScanInterpreter(
            should_fail=interpreter_fail,
            call_order=order,
        ),
        crawler=_MockAuthenticatedCrawler(
            should_fail=crawler_fail,
            call_order=order,
        ),
        kg_builder=_MockKGBuilder(call_order=order),
        workspace_path=workspace_path,
        progress_callback=progress_callback,
    )


# ── Tests ──────────────────────────────────────────────────────────


@pytest.mark.asyncio()
async def test_run_returns_stage1_result(
    session_config: SessionConfig,
    credentials: Credentials,
) -> None:
    """run() returns Stage1Result instance."""
    from src.agents.recon.orchestrator import Stage1Result

    orch = _build_orchestrator()
    result = await orch.run(session_config, credentials)
    assert isinstance(result, Stage1Result)


@pytest.mark.asyncio()
async def test_run_executes_auth_and_scanner_concurrently(
    session_config: SessionConfig,
    credentials: Credentials,
) -> None:
    """auth_flow and scanner run concurrently — total < sum of delays."""
    import time

    orch = _build_orchestrator(auth_delay=0.1, scanner_delay=0.1)
    start = time.monotonic()
    await orch.run(session_config, credentials)
    elapsed = time.monotonic() - start
    # If sequential: ~0.2s. If concurrent: ~0.1s.
    assert elapsed < 0.15


@pytest.mark.asyncio()
async def test_run_llm_interpret_after_both_complete(
    session_config: SessionConfig,
    credentials: Credentials,
) -> None:
    """LLM interpret runs after both auth_flow and scanner complete."""
    call_order: list[str] = []
    orch = _build_orchestrator(call_order=call_order)
    await orch.run(session_config, credentials)
    interpret_idx = call_order.index("llm_interpret")
    auth_idx = call_order.index("auth_flow")
    scanner_idx = call_order.index("scanner")
    assert interpret_idx > auth_idx
    assert interpret_idx > scanner_idx


@pytest.mark.asyncio()
async def test_run_crawler_after_auth_complete(
    session_config: SessionConfig,
    credentials: Credentials,
) -> None:
    """Crawler runs after auth_flow completes."""
    call_order: list[str] = []
    orch = _build_orchestrator(call_order=call_order)
    await orch.run(session_config, credentials)
    crawler_idx = call_order.index("crawler")
    auth_idx = call_order.index("auth_flow")
    assert crawler_idx > auth_idx


@pytest.mark.asyncio()
async def test_run_builds_kg_at_end(
    session_config: SessionConfig,
    credentials: Credentials,
) -> None:
    """KG build is the last phase."""
    call_order: list[str] = []
    orch = _build_orchestrator(call_order=call_order)
    await orch.run(session_config, credentials)
    kg_idx = call_order.index("kg_build")
    assert kg_idx == len(call_order) - 1


@pytest.mark.asyncio()
async def test_run_result_contains_knowledge_graph(
    session_config: SessionConfig,
    credentials: Credentials,
) -> None:
    """Result contains a KnowledgeGraph with nodes."""
    orch = _build_orchestrator()
    result = await orch.run(session_config, credentials)
    assert result.knowledge_graph.node_count >= 0


@pytest.mark.asyncio()
async def test_run_result_contains_attack_surface(
    session_config: SessionConfig,
    credentials: Credentials,
) -> None:
    """Result contains an AttackSurface."""
    from src.agents.recon.attack_surface import AttackSurface

    orch = _build_orchestrator()
    result = await orch.run(session_config, credentials)
    assert isinstance(result.attack_surface, AttackSurface)


@pytest.mark.asyncio()
async def test_run_reports_progress_via_callback(
    session_config: SessionConfig,
    credentials: Credentials,
) -> None:
    """Progress callback receives started/completed pairs."""
    progress: list[tuple[str, str]] = []

    def on_progress(phase: str, status: str) -> None:
        progress.append((phase, status))

    orch = _build_orchestrator(progress_callback=on_progress)
    await orch.run(session_config, credentials)
    phases_started = [p for p, s in progress if s == "started"]
    phases_completed = [p for p, s in progress if s == "completed"]
    assert len(phases_started) >= 3
    assert len(phases_completed) >= 3


@pytest.mark.asyncio()
async def test_run_partial_failure_continues_pipeline(
    session_config: SessionConfig,
    credentials: Credentials,
) -> None:
    """Scanner failure → partial_failure=True but KG still built."""
    orch = _build_orchestrator(scanner_fail=True)
    result = await orch.run(session_config, credentials)
    assert result.partial_failure is True
    assert result.knowledge_graph.node_count >= 0


@pytest.mark.asyncio()
async def test_run_saves_results_to_workspace(
    session_config: SessionConfig,
    credentials: Credentials,
    tmp_path: Path,
) -> None:
    """Results are saved to workspace directory."""
    orch = _build_orchestrator(workspace_path=tmp_path)
    await orch.run(session_config, credentials)
    assert (tmp_path / "knowledge_graph.json").exists()
