"""Build a KnowledgeGraph from CrawlResult."""

from __future__ import annotations

import json

from eazy.models.crawl_types import (
    CrawlResult,
    GraphEdge,
    GraphEdgeType,
    GraphNode,
    GraphNodeType,
    KnowledgeGraph,
)

__all__ = ["GraphBuilder"]


class GraphBuilder:
    """Transform CrawlResult into a KnowledgeGraph.

    Pure synchronous data transformation — no I/O or async needed.
    """

    @staticmethod
    def build(crawl_result: CrawlResult) -> KnowledgeGraph:
        """Build a knowledge graph from crawl results.

        Each PageResult becomes a PAGE node. Links become HYPERLINK edges,
        forms become FORM_ACTION edges, and API endpoints become API nodes
        with API_CALL edges.

        Args:
            crawl_result: The completed crawl result to transform.

        Returns:
            A KnowledgeGraph with nodes and edges.
        """
        graph = KnowledgeGraph()

        for page in crawl_result.pages:
            graph.add_node(
                GraphNode(
                    url=page.url,
                    node_type=GraphNodeType.PAGE,
                    metadata={
                        "status_code": page.status_code,
                        "title": page.title,
                        "depth": page.depth,
                    },
                )
            )

            for link in page.links:
                graph.add_edge(
                    GraphEdge(
                        source=page.url,
                        target=link,
                        edge_type=GraphEdgeType.HYPERLINK,
                    )
                )

            for form in page.forms:
                graph.add_edge(
                    GraphEdge(
                        source=page.url,
                        target=form.action,
                        edge_type=GraphEdgeType.FORM_ACTION,
                    )
                )

            for ep in page.api_endpoints:
                graph.add_node(
                    GraphNode(
                        url=ep.url,
                        node_type=GraphNodeType.API,
                        metadata={
                            "method": ep.method,
                            "source": ep.source,
                        },
                    )
                )
                graph.add_edge(
                    GraphEdge(
                        source=page.url,
                        target=ep.url,
                        edge_type=GraphEdgeType.API_CALL,
                    )
                )

        return graph

    @staticmethod
    def to_json(graph: KnowledgeGraph) -> str:
        """Export a knowledge graph to JSON string.

        Args:
            graph: The knowledge graph to serialize.

        Returns:
            Pretty-printed JSON string.
        """
        return json.dumps(graph.model_dump(mode="json"), indent=2)
