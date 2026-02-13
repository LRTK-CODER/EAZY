"""Unit tests for GraphBuilder."""

import json
from datetime import datetime

from eazy.crawler.graph_builder import GraphBuilder
from eazy.models.crawl_types import (
    CrawlConfig,
    CrawlResult,
    EndpointInfo,
    FormData,
    GraphEdgeType,
    GraphNodeType,
    PageResult,
)


def _make_crawl_result(pages: list[PageResult]) -> CrawlResult:
    """Create a CrawlResult with given pages for testing."""
    now = datetime.now()
    return CrawlResult(
        target_url="https://example.com",
        started_at=now,
        completed_at=now,
        config=CrawlConfig(target_url="https://example.com"),
        pages=pages,
    )


def _make_page(
    url: str = "https://example.com",
    status_code: int = 200,
    depth: int = 0,
    title: str | None = "Home",
    links: list[str] | None = None,
    forms: list[FormData] | None = None,
    api_endpoints: list[EndpointInfo] | None = None,
) -> PageResult:
    """Create a PageResult with defaults for testing."""
    return PageResult(
        url=url,
        status_code=status_code,
        depth=depth,
        title=title,
        links=links or [],
        forms=forms or [],
        api_endpoints=api_endpoints or [],
        crawled_at=datetime.now(),
    )


class TestGraphBuilder:
    """Tests for GraphBuilder.build() and to_json()."""

    def test_build_graph_from_crawl_result_creates_page_nodes(self):
        """Each PageResult should create a PAGE node."""
        pages = [
            _make_page(url="https://example.com"),
            _make_page(url="https://example.com/about", depth=1),
        ]
        result = _make_crawl_result(pages)
        graph = GraphBuilder.build(result)
        page_nodes = graph.get_nodes_by_type(GraphNodeType.PAGE)
        assert len(page_nodes) == 2

    def test_build_graph_includes_hyperlink_edges(self):
        """Links in a page should create HYPERLINK edges."""
        pages = [
            _make_page(
                url="https://example.com",
                links=[
                    "https://example.com/about",
                    "https://example.com/contact",
                ],
            ),
        ]
        result = _make_crawl_result(pages)
        graph = GraphBuilder.build(result)
        hyperlink_edges = [
            e for e in graph.edges if e.edge_type == GraphEdgeType.HYPERLINK
        ]
        assert len(hyperlink_edges) == 2
        targets = {e.target for e in hyperlink_edges}
        assert "https://example.com/about" in targets
        assert "https://example.com/contact" in targets

    def test_build_graph_includes_form_action_edges(self):
        """Forms in a page should create FORM_ACTION edges."""
        pages = [
            _make_page(
                url="https://example.com",
                forms=[
                    FormData(action="/login", method="POST"),
                    FormData(action="/search", method="GET"),
                ],
            ),
        ]
        result = _make_crawl_result(pages)
        graph = GraphBuilder.build(result)
        form_edges = [
            e for e in graph.edges if e.edge_type == GraphEdgeType.FORM_ACTION
        ]
        assert len(form_edges) == 2
        targets = {e.target for e in form_edges}
        assert "/login" in targets
        assert "/search" in targets

    def test_build_graph_includes_api_call_edges(self):
        """API endpoints should create API nodes and API_CALL edges."""
        pages = [
            _make_page(
                url="https://example.com",
                api_endpoints=[
                    EndpointInfo(url="/api/users", method="GET", source="fetch"),
                ],
            ),
        ]
        result = _make_crawl_result(pages)
        graph = GraphBuilder.build(result)
        api_nodes = graph.get_nodes_by_type(GraphNodeType.API)
        assert len(api_nodes) == 1
        assert api_nodes[0].url == "/api/users"
        api_edges = [e for e in graph.edges if e.edge_type == GraphEdgeType.API_CALL]
        assert len(api_edges) == 1
        assert api_edges[0].source == "https://example.com"
        assert api_edges[0].target == "/api/users"

    def test_build_graph_deduplicates_nodes_by_url(self):
        """Nodes with the same URL should be deduplicated."""
        pages = [
            _make_page(
                url="https://example.com",
                links=["https://example.com/about"],
            ),
            _make_page(
                url="https://example.com/about",
                depth=1,
                links=["https://example.com"],
            ),
        ]
        result = _make_crawl_result(pages)
        graph = GraphBuilder.build(result)
        assert len(graph.nodes) == 2

    def test_build_graph_empty_crawl_result_returns_empty_graph(self):
        """Empty CrawlResult should return a graph with 0 nodes and edges."""
        result = _make_crawl_result(pages=[])
        graph = GraphBuilder.build(result)
        assert graph.statistics == {"total_nodes": 0, "total_edges": 0}

    def test_export_graph_to_json_valid_format(self):
        """to_json should return valid JSON with nodes and edges."""
        pages = [
            _make_page(
                url="https://example.com",
                links=["https://example.com/about"],
                api_endpoints=[
                    EndpointInfo(url="/api/data", method="POST", source="xhr"),
                ],
            ),
        ]
        result = _make_crawl_result(pages)
        graph = GraphBuilder.build(result)
        json_str = GraphBuilder.to_json(graph)
        data = json.loads(json_str)
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], dict)
        assert isinstance(data["edges"], list)
