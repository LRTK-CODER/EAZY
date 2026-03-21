"""Attack surface model aggregating recon results."""

from pydantic import BaseModel, Field

from src.agents.core.models import (
    AuthFlow,
    CryptoContext,
    Endpoint,
    Technology,
    WafProfile,
)
from src.agents.recon.kg_models import KnowledgeGraphData


class AttackSurface(BaseModel):
    """Aggregated web attack surface from recon."""

    target_url: str
    endpoints: list[Endpoint]
    auth_flow: AuthFlow
    waf_profile: WafProfile | None = None
    tech_stack: list[Technology] = Field(default_factory=list)
    crypto_context: CryptoContext | None = None


def extract_from_kg(kg_data: KnowledgeGraphData) -> AttackSurface:
    """Extract AttackSurface from KnowledgeGraphData."""
    endpoints = [
        Endpoint.model_validate(node.properties)
        for node in kg_data.nodes
        if node.type == "endpoint"
    ]
    meta = kg_data.metadata
    return AttackSurface(
        target_url=meta.target_url,
        endpoints=endpoints,
        auth_flow=meta.auth_flow or AuthFlow(session_mechanism="cookie"),
        waf_profile=meta.waf_profile,
        tech_stack=meta.tech_stack,
        crypto_context=meta.crypto_context,
    )
