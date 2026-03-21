"""Tests for Knowledge Graph data models."""

import pytest
from pydantic import ValidationError

from src.agents.recon.kg_models import (
    BusinessFlow,
    DataPath,
    FlowStep,
    GraphEdge,
    GraphMetadata,
    GraphNode,
    KnowledgeGraphData,
)


class TestGraphNode:
    """Tests for GraphNode model."""

    @pytest.mark.parametrize(
        "node_type",
        ["endpoint", "data_object", "auth_level", "business_process"],
    )
    def test_graph_node_creation_sets_fields(self, node_type: str) -> None:
        node = GraphNode(
            id="node-1",
            type=node_type,
            properties={"key": "value"},
        )
        assert node.id == "node-1"
        assert node.type == node_type
        assert node.properties == {"key": "value"}

    def test_graph_node_invalid_type_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            GraphNode(id="node-1", type="invalid", properties={})


class TestGraphEdge:
    """Tests for GraphEdge model."""

    def test_graph_edge_creation_sets_fields(self) -> None:
        edge = GraphEdge(
            source="node-1",
            target="node-2",
            type="calls",
            properties={"weight": 1},
        )
        assert edge.source == "node-1"
        assert edge.target == "node-2"
        assert edge.type == "calls"
        assert edge.properties == {"weight": 1}

    def test_graph_edge_invalid_type_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            GraphEdge(
                source="node-1",
                target="node-2",
                type="invalid",
                properties={},
            )


class TestFlowStep:
    """Tests for FlowStep model."""

    def test_flow_step_creation_sets_fields(self) -> None:
        step = FlowStep(order=1, node_id="node-1", description="Login step")
        assert step.order == 1
        assert step.node_id == "node-1"
        assert step.description == "Login step"


class TestDataPath:
    """Tests for DataPath model."""

    def test_data_path_creation_sets_fields(self) -> None:
        path = DataPath(
            param_name="price",
            source_node="node-1",
            sink_node="node-2",
            manipulation_risk="price_tampering",
        )
        assert path.param_name == "price"
        assert path.source_node == "node-1"
        assert path.sink_node == "node-2"
        assert path.manipulation_risk == "price_tampering"

    def test_data_path_invalid_risk_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            DataPath(
                param_name="price",
                source_node="node-1",
                sink_node="node-2",
                manipulation_risk="invalid_risk",
            )


class TestBusinessFlow:
    """Tests for BusinessFlow model."""

    def test_business_flow_creation_with_steps_and_paths(self) -> None:
        step = FlowStep(order=1, node_id="node-1", description="Step 1")
        data_path = DataPath(
            param_name="price",
            source_node="node-1",
            sink_node="node-2",
            manipulation_risk="price_tampering",
        )
        flow = BusinessFlow(
            name="Payment Flow",
            type="payment",
            steps=[step],
            critical_data_paths=[data_path],
        )
        assert flow.name == "Payment Flow"
        assert flow.type == "payment"
        assert len(flow.steps) == 1
        assert len(flow.critical_data_paths) == 1

    def test_business_flow_invalid_type_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            BusinessFlow(
                name="Invalid Flow",
                type="invalid_type",
                steps=[],
                critical_data_paths=[],
            )


class TestGraphMetadata:
    """Tests for GraphMetadata model."""

    def test_graph_metadata_creation_sets_fields(self) -> None:
        metadata = GraphMetadata(
            target_url="https://example.com",
            total_nodes=10,
            total_edges=15,
        )
        assert metadata.target_url == "https://example.com"
        assert metadata.total_nodes == 10
        assert metadata.total_edges == 15


class TestKnowledgeGraphData:
    """Tests for KnowledgeGraphData model."""

    def test_knowledge_graph_data_creation_sets_all(self) -> None:
        node = GraphNode(id="node-1", type="endpoint", properties={"path": "/api"})
        edge = GraphEdge(
            source="node-1",
            target="node-2",
            type="calls",
            properties={},
        )
        step = FlowStep(order=1, node_id="node-1", description="Step 1")
        data_path = DataPath(
            param_name="id",
            source_node="node-1",
            sink_node="node-2",
            manipulation_risk="idor",
        )
        flow = BusinessFlow(
            name="Auth Flow",
            type="auth",
            steps=[step],
            critical_data_paths=[data_path],
        )
        metadata = GraphMetadata(
            target_url="https://example.com",
            total_nodes=1,
            total_edges=1,
        )
        kg = KnowledgeGraphData(
            nodes=[node],
            edges=[edge],
            business_flows=[flow],
            metadata=metadata,
        )
        assert len(kg.nodes) == 1
        assert len(kg.edges) == 1
        assert len(kg.business_flows) == 1
        assert kg.metadata.target_url == "https://example.com"

    def test_knowledge_graph_data_json_roundtrip(self) -> None:
        node = GraphNode(id="node-1", type="endpoint", properties={"path": "/api"})
        edge = GraphEdge(
            source="node-1",
            target="node-2",
            type="calls",
            properties={},
        )
        step = FlowStep(order=1, node_id="node-1", description="Step 1")
        data_path = DataPath(
            param_name="token",
            source_node="node-1",
            sink_node="node-2",
            manipulation_risk="privilege_escalation",
        )
        flow = BusinessFlow(
            name="Auth",
            type="auth",
            steps=[step],
            critical_data_paths=[data_path],
        )
        metadata = GraphMetadata(
            target_url="https://example.com",
            total_nodes=1,
            total_edges=1,
        )
        original = KnowledgeGraphData(
            nodes=[node],
            edges=[edge],
            business_flows=[flow],
            metadata=metadata,
        )
        json_str = original.model_dump_json()
        restored = KnowledgeGraphData.model_validate_json(json_str)
        assert restored == original
