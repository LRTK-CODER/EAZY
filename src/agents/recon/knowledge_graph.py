"""KnowledgeGraph engine wrapping NetworkX DiGraph."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx  # type: ignore[import-untyped]

from src.agents.recon.kg_models import (
    BusinessFlow,
    DataPath,
    EdgeType,
    GraphEdge,
    GraphMetadata,
    GraphNode,
    KnowledgeGraphData,
    NodeType,
)


class KnowledgeGraph:
    """NetworkX DiGraph wrapper for recon knowledge graphs."""

    def __init__(self, target_url: str) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._target_url: str = target_url
        self._business_flows: list[BusinessFlow] = []
        self._data_paths: list[DataPath] = []

    # ── CRUD: Nodes ──────────────────────────────────────────────

    def add_node(self, node: GraphNode) -> None:
        """Add a node. Raises ValueError if node ID already exists."""
        if self._graph.has_node(node.id):
            msg = f"Node already exists: {node.id}"
            raise ValueError(msg)
        self._graph.add_node(
            node.id,
            type=node.type,
            properties=node.properties,
        )

    def has_node(self, node_id: str) -> bool:
        """Check whether a node exists."""
        return bool(self._graph.has_node(node_id))

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its connected edges."""
        self._graph.remove_node(node_id)

    def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        """Return all nodes matching the given type."""
        return [
            self._reconstruct_node(nid, data)
            for nid, data in self._graph.nodes(data=True)
            if data.get("type") == node_type
        ]

    # ── CRUD: Edges ──────────────────────────────────────────────

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge. Raises ValueError if source or target node is missing."""
        if not self._graph.has_node(edge.source):
            msg = f"Source node not found: {edge.source}"
            raise ValueError(msg)
        if not self._graph.has_node(edge.target):
            msg = f"Target node not found: {edge.target}"
            raise ValueError(msg)
        self._graph.add_edge(
            edge.source,
            edge.target,
            type=edge.type,
            properties=edge.properties,
        )

    def has_edge(self, source: str, target: str) -> bool:
        """Check whether an edge exists between source and target."""
        return bool(self._graph.has_edge(source, target))

    def get_edges_by_type(self, edge_type: EdgeType) -> list[GraphEdge]:
        """Return all edges matching the given type."""
        return [
            self._reconstruct_edge(src, tgt, data)
            for src, tgt, data in self._graph.edges(data=True)
            if data.get("type") == edge_type
        ]

    # ── Business logic overlays ──────────────────────────────────

    def add_business_flow(self, flow: BusinessFlow) -> None:
        """Store a business flow overlay."""
        self._business_flows.append(flow)

    def add_data_path(self, data_path: DataPath) -> None:
        """Store a standalone data path."""
        self._data_paths.append(data_path)

    # ── Query ────────────────────────────────────────────────────

    def get_neighbors(self, node_id: str) -> list[GraphNode]:
        """Return successor nodes (DiGraph direction)."""
        return [
            self._reconstruct_node(nid, self._graph.nodes[nid])
            for nid in self._graph.neighbors(node_id)
        ]

    def find_paths(self, source: str, target: str) -> list[list[str]]:
        """Return all simple paths from source to target."""
        try:
            return list(nx.all_simple_paths(self._graph, source, target))
        except nx.NodeNotFound:
            return []

    # ── Properties ───────────────────────────────────────────────

    @property
    def node_count(self) -> int:
        """Number of nodes in the graph."""
        return int(self._graph.number_of_nodes())

    @property
    def edge_count(self) -> int:
        """Number of edges in the graph."""
        return int(self._graph.number_of_edges())

    @property
    def business_flows(self) -> list[BusinessFlow]:
        """Defensive copy of business flows."""
        return list(self._business_flows)

    @property
    def data_paths(self) -> list[DataPath]:
        """Defensive copy of standalone data paths."""
        return list(self._data_paths)

    # ── Serialization ────────────────────────────────────────────

    def to_json(self) -> str:
        """Serialize to JSON string using KnowledgeGraphData wrapper."""
        nodes = [
            self._reconstruct_node(nid, data)
            for nid, data in self._graph.nodes(data=True)
        ]
        edges = [
            self._reconstruct_edge(src, tgt, data)
            for src, tgt, data in self._graph.edges(data=True)
        ]
        metadata = GraphMetadata(
            target_url=self._target_url,
            total_nodes=self.node_count,
            total_edges=self.edge_count,
        )
        graph_data = KnowledgeGraphData(
            nodes=nodes,
            edges=edges,
            business_flows=list(self._business_flows),
            metadata=metadata,
        )
        wrapper: dict[str, object] = {
            "graph": json.loads(graph_data.model_dump_json()),
            "data_paths": [json.loads(dp.model_dump_json()) for dp in self._data_paths],
        }
        return json.dumps(wrapper)

    @classmethod
    def from_json(cls, json_str: str) -> KnowledgeGraph:
        """Deserialize from JSON string."""
        wrapper = json.loads(json_str)
        graph_data = KnowledgeGraphData.model_validate(wrapper["graph"])
        kg = cls(target_url=graph_data.metadata.target_url)
        for node in graph_data.nodes:
            kg.add_node(node)
        for edge in graph_data.edges:
            kg.add_edge(edge)
        for flow in graph_data.business_flows:
            kg.add_business_flow(flow)
        for dp_raw in wrapper.get("data_paths", []):
            kg.add_data_path(DataPath.model_validate(dp_raw))
        return kg

    def save(self, path: Path) -> None:
        """Write JSON to file."""
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> KnowledgeGraph:
        """Load from JSON file."""
        return cls.from_json(path.read_text(encoding="utf-8"))

    # ── Private helpers ──────────────────────────────────────────

    @staticmethod
    def _reconstruct_node(node_id: str, data: dict[str, Any]) -> GraphNode:
        props: dict[str, object] = dict(data.get("properties") or {})
        return GraphNode(id=node_id, type=data["type"], properties=props)

    @staticmethod
    def _reconstruct_edge(source: str, target: str, data: dict[str, Any]) -> GraphEdge:
        props: dict[str, object] = dict(data.get("properties") or {})
        return GraphEdge(
            source=source, target=target, type=data["type"], properties=props
        )
