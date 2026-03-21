"""Knowledge Graph data models for the recon pipeline."""

from typing import Literal

from pydantic import BaseModel, Field

from src.agents.core.models import AuthFlow, CryptoContext, Technology, WafProfile

NodeType = Literal["endpoint", "data_object", "auth_level", "business_process"]

EdgeType = Literal[
    "calls",
    "sends_data",
    "requires_auth",
    "depends_on",
    "validates",
    "creates",
    "reads",
    "updates",
    "deletes",
]

ManipulationRisk = Literal[
    "price_tampering",
    "step_bypass",
    "duplicate_use",
    "race_condition",
    "idor",
    "privilege_escalation",
]

FlowType = Literal[
    "payment",
    "auth",
    "registration",
    "data_management",
    "privilege",
    "reward",
]


class GraphNode(BaseModel):
    """A node in the knowledge graph."""

    id: str
    type: NodeType
    properties: dict[str, object] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """An edge in the knowledge graph."""

    source: str
    target: str
    type: EdgeType
    properties: dict[str, object] = Field(default_factory=dict)


class FlowStep(BaseModel):
    """A single step in a business flow."""

    order: int
    node_id: str
    description: str = ""


class DataPath(BaseModel):
    """A data path tracking parameter flow between nodes."""

    param_name: str
    source_node: str
    sink_node: str
    manipulation_risk: ManipulationRisk


class BusinessFlow(BaseModel):
    """A business flow consisting of steps and critical data paths."""

    name: str
    type: FlowType
    steps: list[FlowStep] = Field(default_factory=list)
    critical_data_paths: list[DataPath] = Field(default_factory=list)


class GraphMetadata(BaseModel):
    """Metadata for the knowledge graph."""

    target_url: str
    auth_flow: AuthFlow | None = None
    waf_profile: WafProfile | None = None
    tech_stack: list[Technology] = Field(default_factory=list)
    crypto_context: CryptoContext | None = None
    total_nodes: int = 0
    total_edges: int = 0


class KnowledgeGraphData(BaseModel):
    """Complete knowledge graph data container."""

    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    business_flows: list[BusinessFlow] = Field(default_factory=list)
    metadata: GraphMetadata
