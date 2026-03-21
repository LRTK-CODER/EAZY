"""Tests for KnowledgeGraph engine."""

import json
from pathlib import Path

import pytest

from src.agents.recon.kg_models import (
    BusinessFlow,
    DataPath,
    FlowStep,
    GraphEdge,
    GraphNode,
)
from src.agents.recon.knowledge_graph import KnowledgeGraph


def _make_node(
    node_id: str = "ep-1", node_type: str = "endpoint", **props: object
) -> GraphNode:
    return GraphNode(id=node_id, type=node_type, properties=props)


def _make_edge(
    source: str = "ep-1",
    target: str = "ep-2",
    edge_type: str = "calls",
    **props: object,
) -> GraphEdge:
    return GraphEdge(source=source, target=target, type=edge_type, properties=props)


@pytest.fixture
def populated_graph() -> KnowledgeGraph:
    """Graph with 3 nodes, 2 edges, 1 BusinessFlow, 1 standalone DataPath."""
    kg = KnowledgeGraph(target_url="https://example.com")

    kg.add_node(_make_node(node_id="ep-1", node_type="endpoint"))
    kg.add_node(_make_node(node_id="ep-2", node_type="endpoint"))
    kg.add_node(_make_node(node_id="do-1", node_type="data_object"))

    kg.add_edge(_make_edge(source="ep-1", target="ep-2", edge_type="calls"))
    kg.add_edge(_make_edge(source="ep-1", target="do-1", edge_type="sends_data"))

    flow = BusinessFlow(
        name="Auth Flow",
        type="auth",
        steps=[
            FlowStep(order=1, node_id="ep-1", description="Login"),
            FlowStep(order=2, node_id="ep-2", description="Verify"),
        ],
        critical_data_paths=[
            DataPath(
                param_name="token",
                source_node="ep-1",
                sink_node="ep-2",
                manipulation_risk="privilege_escalation",
            )
        ],
    )
    kg.add_business_flow(flow)

    standalone_path = DataPath(
        param_name="price",
        source_node="ep-1",
        sink_node="do-1",
        manipulation_risk="price_tampering",
    )
    kg.add_data_path(standalone_path)

    return kg


class TestKnowledgeGraphBasic:
    """Basic CRUD operations."""

    def test_empty_graph_has_zero_nodes_and_edges(self) -> None:
        kg = KnowledgeGraph(target_url="https://example.com")
        assert kg.node_count == 0
        assert kg.edge_count == 0

    def test_add_node_makes_it_queryable(self) -> None:
        kg = KnowledgeGraph(target_url="https://example.com")
        kg.add_node(_make_node(node_id="ep-1"))
        assert kg.has_node("ep-1") is True

    def test_add_duplicate_node_raises_error(self) -> None:
        kg = KnowledgeGraph(target_url="https://example.com")
        kg.add_node(_make_node(node_id="ep-1"))
        with pytest.raises(ValueError, match="ep-1"):
            kg.add_node(_make_node(node_id="ep-1"))

    def test_add_edge_connects_nodes(self) -> None:
        kg = KnowledgeGraph(target_url="https://example.com")
        kg.add_node(_make_node(node_id="ep-1"))
        kg.add_node(_make_node(node_id="ep-2"))
        kg.add_edge(_make_edge(source="ep-1", target="ep-2"))
        assert kg.has_edge("ep-1", "ep-2") is True

    def test_add_edge_missing_node_raises_error(self) -> None:
        kg = KnowledgeGraph(target_url="https://example.com")
        kg.add_node(_make_node(node_id="ep-1"))
        with pytest.raises(ValueError, match="ep-2"):
            kg.add_edge(_make_edge(source="ep-1", target="ep-2"))

    def test_remove_node_removes_connected_edges(self) -> None:
        kg = KnowledgeGraph(target_url="https://example.com")
        kg.add_node(_make_node(node_id="ep-1"))
        kg.add_node(_make_node(node_id="ep-2"))
        kg.add_edge(_make_edge(source="ep-1", target="ep-2"))
        kg.remove_node("ep-1")
        assert kg.has_node("ep-1") is False
        assert kg.edge_count == 0


class TestKnowledgeGraphOverlays:
    """Business flow and data path overlays."""

    def test_add_business_flow_stores_flow(self) -> None:
        kg = KnowledgeGraph(target_url="https://example.com")
        flow = BusinessFlow(name="Payment", type="payment")
        kg.add_business_flow(flow)
        assert len(kg.business_flows) == 1

    def test_add_data_path_stores_path(self) -> None:
        kg = KnowledgeGraph(target_url="https://example.com")
        path = DataPath(
            param_name="id",
            source_node="ep-1",
            sink_node="ep-2",
            manipulation_risk="idor",
        )
        kg.add_data_path(path)
        assert len(kg.data_paths) == 1


class TestKnowledgeGraphSerialization:
    """JSON serialization and file I/O."""

    def test_to_json_returns_valid_json(self, populated_graph: KnowledgeGraph) -> None:
        result = populated_graph.to_json()
        parsed = json.loads(result)
        assert "graph" in parsed
        assert "data_paths" in parsed

    def test_from_json_restores_graph(self, populated_graph: KnowledgeGraph) -> None:
        json_str = populated_graph.to_json()
        restored = KnowledgeGraph.from_json(json_str)
        assert restored.node_count == populated_graph.node_count
        assert restored.edge_count == populated_graph.edge_count
        assert len(restored.business_flows) == len(populated_graph.business_flows)
        assert len(restored.data_paths) == len(populated_graph.data_paths)

    def test_save_creates_file(
        self, populated_graph: KnowledgeGraph, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "kg.json"
        populated_graph.save(file_path)
        assert file_path.exists()

    def test_load_restores_from_file(
        self, populated_graph: KnowledgeGraph, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "kg.json"
        populated_graph.save(file_path)
        restored = KnowledgeGraph.load(file_path)
        assert restored.node_count == populated_graph.node_count
        assert restored.edge_count == populated_graph.edge_count


class TestKnowledgeGraphQuery:
    """Filtering and path-finding queries."""

    def test_get_nodes_by_type_filters_correctly(
        self, populated_graph: KnowledgeGraph
    ) -> None:
        endpoints = populated_graph.get_nodes_by_type("endpoint")
        assert len(endpoints) == 2

    def test_get_edges_by_type_filters_correctly(
        self, populated_graph: KnowledgeGraph
    ) -> None:
        calls = populated_graph.get_edges_by_type("calls")
        assert len(calls) == 1

    def test_find_paths_returns_reachable_routes(self) -> None:
        kg = KnowledgeGraph(target_url="https://example.com")
        kg.add_node(_make_node(node_id="A", node_type="endpoint"))
        kg.add_node(_make_node(node_id="B", node_type="endpoint"))
        kg.add_node(_make_node(node_id="C", node_type="endpoint"))
        kg.add_edge(_make_edge(source="A", target="B"))
        kg.add_edge(_make_edge(source="B", target="C"))
        paths = kg.find_paths("A", "C")
        assert ["A", "B", "C"] in paths

    def test_find_paths_unreachable_returns_empty(self) -> None:
        kg = KnowledgeGraph(target_url="https://example.com")
        kg.add_node(_make_node(node_id="A", node_type="endpoint"))
        kg.add_node(_make_node(node_id="B", node_type="endpoint"))
        kg.add_node(_make_node(node_id="C", node_type="endpoint"))
        kg.add_edge(_make_edge(source="A", target="B"))
        # C is isolated
        paths = kg.find_paths("A", "C")
        assert paths == []

    def test_get_neighbors_returns_connected_nodes(self) -> None:
        kg = KnowledgeGraph(target_url="https://example.com")
        kg.add_node(_make_node(node_id="A", node_type="endpoint"))
        kg.add_node(_make_node(node_id="B", node_type="endpoint"))
        kg.add_node(_make_node(node_id="C", node_type="data_object"))
        kg.add_edge(_make_edge(source="A", target="B"))
        kg.add_edge(_make_edge(source="A", target="C", edge_type="sends_data"))
        neighbors = kg.get_neighbors("A")
        assert len(neighbors) == 2
