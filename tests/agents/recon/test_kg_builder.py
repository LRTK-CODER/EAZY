"""Tests for KGBuilder — KnowledgeGraph 구축기."""

import json
from pathlib import Path

import pytest

from src.agents.core.models import AuthFlow, AuthStep, Endpoint
from src.agents.recon.auth_flow_mapper import AuthFlowResult
from src.agents.recon.crawler import ApiCallRelation, CrawlResult, DataFlowPath
from src.agents.recon.kg_builder import KGBuilder
from src.agents.recon.scan_interpreter import ScanInterpreterResult


class _MockLLMClient:
    """Mock LLM client — only external boundary is mocked."""

    def __init__(self, response: str, *, should_fail: bool = False) -> None:
        self.response = response
        self.should_fail = should_fail
        self.call_count = 0

    async def interpret(self, prompt: str) -> str:
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("LLM unavailable")
        return self.response


@pytest.fixture()
def mock_llm() -> _MockLLMClient:
    """BusinessFlow JSON 반환하는 mock LLM."""
    response = json.dumps(
        [
            {
                "name": "Login Flow",
                "type": "auth",
                "steps": [
                    {
                        "order": 1,
                        "node_id": "endpoint:/api/login:POST",
                        "description": "Submit credentials",
                    },
                ],
                "critical_data_paths": [
                    {
                        "param_name": "password",
                        "source_node": "endpoint:/api/login:POST",
                        "sink_node": "endpoint:/api/session:GET",
                        "manipulation_risk": "privilege_escalation",
                    },
                ],
            },
        ],
    )
    return _MockLLMClient(response)


@pytest.fixture()
def sample_crawl_result() -> CrawlResult:
    """엔드포인트 2개, ApiCallRelation 1개, DataFlowPath 1개."""
    return CrawlResult(
        discovered_endpoints=[
            Endpoint(url="/api/login", method="POST", auth_required=False),
            Endpoint(url="/api/users", method="GET", auth_required=True),
        ],
        api_calls=[
            ApiCallRelation(
                source_url="/api/login",
                target_url="/api/session",
                method="POST",
                trigger="fetch",
            ),
        ],
        data_flows=[
            DataFlowPath(
                param_name="price",
                source_url="/api/products",
                sink_url="/api/checkout",
                location="body",
            ),
        ],
    )


@pytest.fixture()
def sample_scan_result() -> ScanInterpreterResult:
    """Finding 1개, tech_stack, waf_profile 포함."""
    return ScanInterpreterResult(
        risk_summary="Medium risk",
        findings=[],
        tech_stack=[],
        is_fallback=False,
    )


@pytest.fixture()
def sample_auth_result() -> AuthFlowResult:
    """성공한 인증, session_mechanism='cookie'."""
    return AuthFlowResult(
        auth_flow=AuthFlow(
            steps=[AuthStep(order=1, action="POST /api/login", description="Login")],
            session_mechanism="cookie",
        ),
        success=True,
        login_url="http://target.test/login",
    )


# ── Test 1: Endpoint nodes ──────────────────────────────────────


@pytest.mark.asyncio()
async def test_build_adds_endpoint_nodes(
    mock_llm: _MockLLMClient,
    sample_crawl_result: CrawlResult,
    sample_scan_result: ScanInterpreterResult,
    sample_auth_result: AuthFlowResult,
) -> None:
    builder = KGBuilder(llm_client=mock_llm, target_url="http://target.test")
    kg = await builder.build(
        sample_crawl_result, sample_scan_result, sample_auth_result
    )

    endpoint_nodes = kg.get_nodes_by_type("endpoint")
    assert len(endpoint_nodes) >= 2  # noqa: PLR2004


# ── Test 2: calls edges ─────────────────────────────────────────


@pytest.mark.asyncio()
async def test_build_adds_calls_edges(
    mock_llm: _MockLLMClient,
    sample_crawl_result: CrawlResult,
    sample_scan_result: ScanInterpreterResult,
    sample_auth_result: AuthFlowResult,
) -> None:
    builder = KGBuilder(llm_client=mock_llm, target_url="http://target.test")
    kg = await builder.build(
        sample_crawl_result, sample_scan_result, sample_auth_result
    )

    calls_edges = kg.get_edges_by_type("calls")
    assert len(calls_edges) >= 1


# ── Test 3: sends_data edges ────────────────────────────────────


@pytest.mark.asyncio()
async def test_build_adds_sends_data_edges(
    mock_llm: _MockLLMClient,
    sample_crawl_result: CrawlResult,
    sample_scan_result: ScanInterpreterResult,
    sample_auth_result: AuthFlowResult,
) -> None:
    builder = KGBuilder(llm_client=mock_llm, target_url="http://target.test")
    kg = await builder.build(
        sample_crawl_result, sample_scan_result, sample_auth_result
    )

    sends_data_edges = kg.get_edges_by_type("sends_data")
    assert len(sends_data_edges) >= 1


# ── Test 4: requires_auth edges ─────────────────────────────────


@pytest.mark.asyncio()
async def test_build_adds_requires_auth_edges(
    mock_llm: _MockLLMClient,
    sample_crawl_result: CrawlResult,
    sample_scan_result: ScanInterpreterResult,
    sample_auth_result: AuthFlowResult,
) -> None:
    builder = KGBuilder(llm_client=mock_llm, target_url="http://target.test")
    kg = await builder.build(
        sample_crawl_result, sample_scan_result, sample_auth_result
    )

    requires_auth_edges = kg.get_edges_by_type("requires_auth")
    assert len(requires_auth_edges) >= 1


# ── Test 5: auth_level nodes ────────────────────────────────────


@pytest.mark.asyncio()
async def test_build_adds_auth_level_nodes(
    mock_llm: _MockLLMClient,
    sample_crawl_result: CrawlResult,
    sample_scan_result: ScanInterpreterResult,
    sample_auth_result: AuthFlowResult,
) -> None:
    builder = KGBuilder(llm_client=mock_llm, target_url="http://target.test")
    kg = await builder.build(
        sample_crawl_result, sample_scan_result, sample_auth_result
    )

    auth_level_nodes = kg.get_nodes_by_type("auth_level")
    assert len(auth_level_nodes) >= 1


# ── Test 6: data_object nodes ───────────────────────────────────


@pytest.mark.asyncio()
async def test_build_adds_data_object_nodes(
    mock_llm: _MockLLMClient,
    sample_crawl_result: CrawlResult,
    sample_scan_result: ScanInterpreterResult,
    sample_auth_result: AuthFlowResult,
) -> None:
    builder = KGBuilder(llm_client=mock_llm, target_url="http://target.test")
    kg = await builder.build(
        sample_crawl_result, sample_scan_result, sample_auth_result
    )

    data_object_nodes = kg.get_nodes_by_type("data_object")
    assert len(data_object_nodes) >= 1


# ── Test 7: business flows via LLM ──────────────────────────────


@pytest.mark.asyncio()
async def test_build_creates_business_flows(
    mock_llm: _MockLLMClient,
    sample_crawl_result: CrawlResult,
    sample_scan_result: ScanInterpreterResult,
    sample_auth_result: AuthFlowResult,
) -> None:
    builder = KGBuilder(llm_client=mock_llm, target_url="http://target.test")
    kg = await builder.build(
        sample_crawl_result, sample_scan_result, sample_auth_result
    )

    assert len(kg.business_flows) >= 1
    assert mock_llm.call_count == 1


# ── Test 8: data paths extraction ───────────────────────────────


@pytest.mark.asyncio()
async def test_build_extracts_data_paths(
    mock_llm: _MockLLMClient,
    sample_crawl_result: CrawlResult,
    sample_scan_result: ScanInterpreterResult,
    sample_auth_result: AuthFlowResult,
) -> None:
    builder = KGBuilder(llm_client=mock_llm, target_url="http://target.test")
    kg = await builder.build(
        sample_crawl_result, sample_scan_result, sample_auth_result
    )

    assert len(kg.data_paths) >= 1


# ── Test 9: saves to workspace ──────────────────────────────────


@pytest.mark.asyncio()
async def test_build_saves_to_workspace(
    mock_llm: _MockLLMClient,
    sample_crawl_result: CrawlResult,
    sample_scan_result: ScanInterpreterResult,
    sample_auth_result: AuthFlowResult,
    tmp_path: Path,
) -> None:
    builder = KGBuilder(llm_client=mock_llm, target_url="http://target.test")
    await builder.build(
        sample_crawl_result,
        sample_scan_result,
        sample_auth_result,
        workspace_path=tmp_path,
    )

    saved_file = tmp_path / "knowledge_graph.json"
    assert saved_file.exists()
    data = json.loads(saved_file.read_text(encoding="utf-8"))
    assert "graph" in data


# ── Test 10: metadata calculation ────────────────────────────────


@pytest.mark.asyncio()
async def test_build_calculates_metadata(
    mock_llm: _MockLLMClient,
    sample_crawl_result: CrawlResult,
    sample_scan_result: ScanInterpreterResult,
    sample_auth_result: AuthFlowResult,
) -> None:
    builder = KGBuilder(llm_client=mock_llm, target_url="http://target.test")
    kg = await builder.build(
        sample_crawl_result, sample_scan_result, sample_auth_result
    )

    assert kg.node_count > 0
    assert kg.edge_count > 0
    # Verify metadata via serialization
    data = json.loads(kg.to_json())
    metadata = data["graph"]["metadata"]
    assert metadata["total_nodes"] == kg.node_count
    assert metadata["total_edges"] == kg.edge_count


# ── Test 11: empty input ─────────────────────────────────────────


@pytest.mark.asyncio()
async def test_build_empty_input_returns_empty_kg() -> None:
    empty_llm = _MockLLMClient("[]")
    builder = KGBuilder(llm_client=empty_llm, target_url="http://target.test")
    kg = await builder.build(
        CrawlResult(),
        ScanInterpreterResult(risk_summary=""),
        AuthFlowResult(
            auth_flow=AuthFlow(steps=[], session_mechanism="custom"),
            success=False,
            login_url="",
        ),
    )

    assert kg.node_count == 0
    assert kg.edge_count == 0
    assert len(kg.business_flows) == 0
    assert len(kg.data_paths) == 0
