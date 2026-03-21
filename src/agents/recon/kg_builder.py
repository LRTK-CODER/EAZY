"""KGBuilder — CrawlResult + ScanInterpreterResult + AuthFlowResult → KnowledgeGraph."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path

from src.agents.core.models import Endpoint
from src.agents.recon.auth_flow_mapper import AuthFlowResult
from src.agents.recon.crawler import ApiCallRelation, CrawlResult, DataFlowPath
from src.agents.recon.kg_models import (
    BusinessFlow,
    DataPath,
    GraphEdge,
    GraphNode,
    ManipulationRisk,
)
from src.agents.recon.knowledge_graph import KnowledgeGraph
from src.agents.recon.scan_interpreter import LLMClient, ScanInterpreterResult

# Default manipulation risk when LLM doesn't provide one
_DEFAULT_RISK: ManipulationRisk = "idor"


class KGBuilder:
    """Builds a KnowledgeGraph from recon pipeline outputs."""

    def __init__(self, llm_client: LLMClient, target_url: str) -> None:
        self._llm = llm_client
        self._target_url = target_url

    async def build(
        self,
        crawl_result: CrawlResult,
        scan_result: ScanInterpreterResult,
        auth_result: AuthFlowResult,
        *,
        workspace_path: Path | None = None,
    ) -> KnowledgeGraph:
        """Build a KnowledgeGraph from recon results."""
        kg = KnowledgeGraph(self._target_url)

        # Nodes
        self._add_endpoint_nodes(kg, crawl_result.discovered_endpoints)
        self._add_auth_level_nodes(kg, auth_result)
        self._add_data_object_nodes(kg, crawl_result.data_flows)

        # Edges
        self._add_calls_edges(kg, crawl_result.api_calls)
        self._add_sends_data_edges(kg, crawl_result.data_flows)
        self._add_requires_auth_edges(
            kg,
            crawl_result.discovered_endpoints,
            auth_result,
        )

        # Business flows (LLM 1회)
        business_flows = await self._identify_business_flows(
            kg,
            crawl_result,
            scan_result,
        )
        for flow in business_flows:
            kg.add_business_flow(flow)

        # Data paths
        data_paths = self._extract_data_paths(crawl_result.data_flows)
        for dp in data_paths:
            kg.add_data_path(dp)

        # Persist
        if workspace_path is not None:
            kg.save(workspace_path / "knowledge_graph.json")

        return kg

    # ── Node helpers ──────────────────────────────────────────────

    @staticmethod
    def _add_endpoint_nodes(
        kg: KnowledgeGraph,
        endpoints: list[Endpoint],
    ) -> None:
        for ep in endpoints:
            node_id = f"endpoint:{ep.url}:{ep.method}"
            if not kg.has_node(node_id):
                kg.add_node(
                    GraphNode(
                        id=node_id,
                        type="endpoint",
                        properties={
                            "url": ep.url,
                            "method": ep.method,
                            "auth_required": ep.auth_required,
                        },
                    ),
                )

    @staticmethod
    def _add_auth_level_nodes(
        kg: KnowledgeGraph,
        auth_result: AuthFlowResult,
    ) -> None:
        mechanism = auth_result.auth_flow.session_mechanism
        if not auth_result.success:
            return
        node_id = f"auth:{mechanism}"
        if not kg.has_node(node_id):
            kg.add_node(
                GraphNode(
                    id=node_id,
                    type="auth_level",
                    properties={"mechanism": mechanism},
                ),
            )

    @staticmethod
    def _add_data_object_nodes(
        kg: KnowledgeGraph,
        data_flows: list[DataFlowPath],
    ) -> None:
        seen: set[str] = set()
        for df in data_flows:
            if df.param_name in seen:
                continue
            seen.add(df.param_name)
            node_id = f"data:{df.param_name}"
            if not kg.has_node(node_id):
                kg.add_node(
                    GraphNode(
                        id=node_id,
                        type="data_object",
                        properties={"param_name": df.param_name},
                    ),
                )

    # ── Edge helpers ──────────────────────────────────────────────

    @staticmethod
    def _add_calls_edges(
        kg: KnowledgeGraph,
        api_calls: list[ApiCallRelation],
    ) -> None:
        for call in api_calls:
            source_id = f"endpoint:{call.source_url}:GET"
            target_id = f"endpoint:{call.target_url}:{call.method}"
            # Ensure source/target nodes exist
            if not kg.has_node(source_id):
                kg.add_node(
                    GraphNode(
                        id=source_id,
                        type="endpoint",
                        properties={"url": call.source_url, "method": "GET"},
                    ),
                )
            if not kg.has_node(target_id):
                kg.add_node(
                    GraphNode(
                        id=target_id,
                        type="endpoint",
                        properties={
                            "url": call.target_url,
                            "method": call.method,
                        },
                    ),
                )
            kg.add_edge(
                GraphEdge(
                    source=source_id,
                    target=target_id,
                    type="calls",
                    properties={"method": call.method, "trigger": call.trigger},
                ),
            )

    @staticmethod
    def _add_sends_data_edges(
        kg: KnowledgeGraph,
        data_flows: list[DataFlowPath],
    ) -> None:
        for df in data_flows:
            source_id = f"endpoint:{df.source_url}:GET"
            sink_id = f"endpoint:{df.sink_url}:GET"
            # Ensure source/sink nodes exist
            if not kg.has_node(source_id):
                kg.add_node(
                    GraphNode(
                        id=source_id,
                        type="endpoint",
                        properties={"url": df.source_url, "method": "GET"},
                    ),
                )
            if not kg.has_node(sink_id):
                kg.add_node(
                    GraphNode(
                        id=sink_id,
                        type="endpoint",
                        properties={"url": df.sink_url, "method": "GET"},
                    ),
                )
            kg.add_edge(
                GraphEdge(
                    source=source_id,
                    target=sink_id,
                    type="sends_data",
                    properties={
                        "param_name": df.param_name,
                        "location": df.location,
                    },
                ),
            )

    @staticmethod
    def _add_requires_auth_edges(
        kg: KnowledgeGraph,
        endpoints: list[Endpoint],
        auth_result: AuthFlowResult,
    ) -> None:
        if not auth_result.success:
            return
        mechanism = auth_result.auth_flow.session_mechanism
        auth_node_id = f"auth:{mechanism}"
        if not kg.has_node(auth_node_id):
            return
        for ep in endpoints:
            if not ep.auth_required:
                continue
            ep_node_id = f"endpoint:{ep.url}:{ep.method}"
            if kg.has_node(ep_node_id):
                kg.add_edge(
                    GraphEdge(
                        source=ep_node_id,
                        target=auth_node_id,
                        type="requires_auth",
                        properties={"mechanism": mechanism},
                    ),
                )

    # ── LLM-based business flow identification ───────────────────

    async def _identify_business_flows(
        self,
        kg: KnowledgeGraph,
        crawl_result: CrawlResult,
        scan_result: ScanInterpreterResult,
    ) -> list[BusinessFlow]:
        endpoints_summary = [
            {"url": ep.url, "method": ep.method, "auth_required": ep.auth_required}
            for ep in crawl_result.discovered_endpoints
        ]
        api_calls_summary = [
            {
                "source": c.source_url,
                "target": c.target_url,
                "method": c.method,
            }
            for c in crawl_result.api_calls
        ]
        prompt = (
            "You are a security analyst. Identify business flows from the "
            "following API endpoints and call relationships.\n"
            "Return a JSON array of business flows. Each flow has:\n"
            '- name: string\n- type: one of "payment","auth","registration",'
            '"data_management","privilege","reward"\n'
            "- steps: list of {order: int, node_id: string, description: string}\n"
            "  node_id format: endpoint:<url>:<METHOD>\n"
            "- critical_data_paths: list of {param_name, source_node, "
            "sink_node, manipulation_risk}\n"
            '  manipulation_risk: one of "price_tampering","step_bypass",'
            '"duplicate_use","race_condition","idor","privilege_escalation"\n'
            "Return ONLY valid JSON, no markdown.\n\n"
            f"Endpoints:\n{json.dumps(endpoints_summary)}\n\n"
            f"API Calls:\n{json.dumps(api_calls_summary)}\n\n"
            f"Risk Summary: {scan_result.risk_summary}"
        )
        try:
            response = await self._llm.interpret(prompt)
            return self._parse_business_flows(response)
        except Exception:  # noqa: BLE001
            return []

    @staticmethod
    def _parse_business_flows(response: str) -> list[BusinessFlow]:
        flows: list[BusinessFlow] = []
        with contextlib.suppress(Exception):
            parsed = json.loads(response)
            if isinstance(parsed, list):
                flows = [BusinessFlow(**f) for f in parsed]
        return flows

    # ── Data path extraction ─────────────────────────────────────

    @staticmethod
    def _extract_data_paths(data_flows: list[DataFlowPath]) -> list[DataPath]:
        paths: list[DataPath] = []
        for df in data_flows:
            source_node = f"endpoint:{df.source_url}:GET"
            sink_node = f"endpoint:{df.sink_url}:GET"
            paths.append(
                DataPath(
                    param_name=df.param_name,
                    source_node=source_node,
                    sink_node=sink_node,
                    manipulation_risk=_DEFAULT_RISK,
                ),
            )
        return paths
