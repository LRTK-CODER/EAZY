"""Tests for AttackSurface model and extract_from_kg function."""

from src.agents.core.models import (
    AuthFlow,
    AuthStep,
    CryptoContext,
    Endpoint,
    Parameter,
    Technology,
    WafProfile,
)
from src.agents.recon.attack_surface import AttackSurface, extract_from_kg
from src.agents.recon.kg_models import GraphMetadata, GraphNode, KnowledgeGraphData


class TestAttackSurface:
    """Tests for AttackSurface model."""

    def test_attack_surface_creation_with_required_fields(self) -> None:
        endpoint = Endpoint(url="/api/login", method="POST")
        auth_flow = AuthFlow(session_mechanism="cookie")
        surface = AttackSurface(
            target_url="https://example.com",
            endpoints=[endpoint],
            auth_flow=auth_flow,
        )
        assert surface.target_url == "https://example.com"
        assert len(surface.endpoints) == 1
        assert surface.auth_flow.session_mechanism == "cookie"
        assert surface.waf_profile is None
        assert surface.tech_stack == []
        assert surface.crypto_context is None

    def test_attack_surface_optional_waf_none(self) -> None:
        surface = AttackSurface(
            target_url="https://example.com",
            endpoints=[],
            auth_flow=AuthFlow(session_mechanism="jwt"),
            waf_profile=None,
        )
        assert surface.waf_profile is None

    def test_attack_surface_optional_crypto_none(self) -> None:
        surface = AttackSurface(
            target_url="https://example.com",
            endpoints=[],
            auth_flow=AuthFlow(session_mechanism="cookie"),
            crypto_context=None,
        )
        assert surface.crypto_context is None

    def test_attack_surface_with_full_fields(self) -> None:
        param = Parameter(name="username", location="body", type="string")
        endpoint = Endpoint(
            url="/api/login",
            method="POST",
            parameters=[param],
            auth_required=False,
            content_type="application/json",
        )
        auth_flow = AuthFlow(
            steps=[AuthStep(order=1, action="login", description="Submit creds")],
            session_mechanism="jwt",
            two_factor=True,
            sso=False,
        )
        waf = WafProfile(detected=True, vendor="Cloudflare", confidence=0.9)
        tech = Technology(name="Django", version="4.2", category="framework")
        crypto = CryptoContext(detected=True, algorithm="AES-256-CBC")

        surface = AttackSurface(
            target_url="https://example.com",
            endpoints=[endpoint],
            auth_flow=auth_flow,
            waf_profile=waf,
            tech_stack=[tech],
            crypto_context=crypto,
        )
        assert surface.endpoints[0].url == "/api/login"
        assert surface.auth_flow.two_factor is True
        assert surface.waf_profile is not None
        assert surface.waf_profile.vendor == "Cloudflare"
        assert len(surface.tech_stack) == 1
        assert surface.tech_stack[0].name == "Django"
        assert surface.crypto_context is not None
        assert surface.crypto_context.algorithm == "AES-256-CBC"

    def test_attack_surface_json_roundtrip(self) -> None:
        param = Parameter(name="token", location="header", type="string")
        endpoint = Endpoint(
            url="/api/data",
            method="GET",
            parameters=[param],
            auth_required=True,
        )
        auth_flow = AuthFlow(
            steps=[AuthStep(order=1, action="bearer", description="Send token")],
            session_mechanism="bearer",
        )
        waf = WafProfile(detected=False)
        tech = Technology(name="Express", version="4.18")
        crypto = CryptoContext(detected=True, algorithm="RSA-2048")

        original = AttackSurface(
            target_url="https://example.com",
            endpoints=[endpoint],
            auth_flow=auth_flow,
            waf_profile=waf,
            tech_stack=[tech],
            crypto_context=crypto,
        )
        json_str = original.model_dump_json()
        restored = AttackSurface.model_validate_json(json_str)
        assert restored == original


class TestExtractFromKG:
    """Tests for extract_from_kg function."""

    def test_extract_attack_surface_from_kg_data(self) -> None:
        nodes = [
            GraphNode(
                id="ep-login",
                type="endpoint",
                properties={
                    "url": "/api/login",
                    "method": "POST",
                    "parameters": [
                        {"name": "username", "location": "body", "type": "string"},
                    ],
                    "auth_required": False,
                    "content_type": "application/json",
                },
            ),
            GraphNode(
                id="ep-users",
                type="endpoint",
                properties={
                    "url": "/api/users",
                    "method": "GET",
                    "parameters": [],
                    "auth_required": True,
                    "content_type": "application/json",
                },
            ),
        ]
        auth_flow = AuthFlow(session_mechanism="jwt")
        waf = WafProfile(detected=True, vendor="ModSecurity", confidence=0.8)
        tech = Technology(name="Flask", version="3.0")
        crypto = CryptoContext(detected=False)

        metadata = GraphMetadata(
            target_url="https://target.com",
            auth_flow=auth_flow,
            waf_profile=waf,
            tech_stack=[tech],
            crypto_context=crypto,
            total_nodes=2,
            total_edges=0,
        )
        kg_data = KnowledgeGraphData(nodes=nodes, metadata=metadata)

        surface = extract_from_kg(kg_data)

        assert surface.target_url == "https://target.com"
        assert len(surface.endpoints) == 2
        assert surface.endpoints[0].url == "/api/login"
        assert surface.endpoints[1].url == "/api/users"
        assert surface.auth_flow.session_mechanism == "jwt"
        assert surface.waf_profile is not None
        assert surface.waf_profile.vendor == "ModSecurity"
        assert len(surface.tech_stack) == 1
        assert surface.crypto_context is not None

    def test_extract_attack_surface_empty_kg_returns_empty_endpoints(self) -> None:
        nodes = [
            GraphNode(
                id="do-user",
                type="data_object",
                properties={"name": "User"},
            ),
        ]
        metadata = GraphMetadata(
            target_url="https://target.com",
            total_nodes=1,
            total_edges=0,
        )
        kg_data = KnowledgeGraphData(nodes=nodes, metadata=metadata)

        surface = extract_from_kg(kg_data)

        assert surface.endpoints == []
        assert surface.target_url == "https://target.com"
        # auth_flow defaults when metadata has None
        assert surface.auth_flow.session_mechanism == "cookie"
