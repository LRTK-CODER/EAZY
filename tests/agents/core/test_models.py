"""Tests for core Pydantic models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.agents.core.models import (
    AuthFlow,
    CryptoContext,
    Endpoint,
    Parameter,
    SessionConfig,
    Technology,
    WafProfile,
)


class TestSessionConfig:
    def test_session_config_valid(self) -> None:
        config = SessionConfig(
            session_name="test-session",
            target_url="https://example.com",
        )
        assert config.session_name == "test-session"
        assert config.target_url == "https://example.com"

    def test_session_config_missing_required(self) -> None:
        with pytest.raises(ValidationError):
            SessionConfig()  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            SessionConfig(session_name="test")  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            SessionConfig(target_url="https://example.com")  # type: ignore[call-arg]

    def test_session_config_invalid_url(self) -> None:
        with pytest.raises(ValidationError):
            SessionConfig(session_name="test", target_url="")

    def test_session_config_defaults(self) -> None:
        config = SessionConfig(session_name="test", target_url="https://example.com")
        assert config.tool_enabled is True
        assert config.auto_approve_low is False
        assert config.max_retries == 3
        assert config.reflexion_memory_size == 5
        assert config.llm_model == "gpt-4o"
        assert config.llm_temperature == 0.0
        assert config.scope == []
        assert config.exclude == []

    def test_session_config_boundary_values(self) -> None:
        with pytest.raises(ValidationError):
            SessionConfig(
                session_name="test",
                target_url="https://example.com",
                max_retries=0,
            )
        with pytest.raises(ValidationError):
            SessionConfig(
                session_name="test",
                target_url="https://example.com",
                llm_temperature=2.1,
            )

    def test_session_config_serialization(self) -> None:
        config = SessionConfig(session_name="test", target_url="https://example.com")
        data = config.model_dump()
        restored = SessionConfig(**data)
        assert restored == config

    def test_session_config_created_auto(self) -> None:
        before = datetime.now(UTC)
        config = SessionConfig(session_name="test", target_url="https://example.com")
        after = datetime.now(UTC)
        assert before <= config.created <= after


class TestEndpoint:
    def test_endpoint_valid(self) -> None:
        ep = Endpoint(url="/api/login", method="POST")
        assert ep.url == "/api/login"
        assert ep.method == "POST"
        assert ep.parameters == []
        assert ep.auth_required is False
        assert ep.content_type == "application/json"

    def test_endpoint_invalid_method(self) -> None:
        with pytest.raises(ValidationError):
            Endpoint(url="/api/login", method="INVALID")

    def test_endpoint_serialization_json(self) -> None:
        ep = Endpoint(
            url="/api/data",
            method="GET",
            parameters=[Parameter(name="id", location="query", sample_value="42")],
        )
        json_str = ep.model_dump_json()
        restored = Endpoint.model_validate_json(json_str)
        assert restored == ep


class TestParameter:
    def test_parameter_valid_locations(self) -> None:
        for loc in ("query", "header", "cookie", "body", "path"):
            p = Parameter(name="test", location=loc)
            assert p.location == loc

    def test_parameter_invalid_location(self) -> None:
        with pytest.raises(ValidationError):
            Parameter(name="test", location="invalid")  # type: ignore[arg-type]


class TestCryptoContext:
    def test_crypto_context_defaults(self) -> None:
        ctx = CryptoContext()
        assert ctx.detected is False
        assert ctx.algorithm is None
        assert ctx.key is None
        assert ctx.iv is None
        assert ctx.padding is None
        assert ctx.encryption_scope is None
        assert ctx.encrypted_endpoints == []


class TestAuthFlow:
    def test_auth_flow_session_mechanism(self) -> None:
        for mech in ("cookie", "jwt", "bearer", "custom"):
            flow = AuthFlow(session_mechanism=mech)
            assert flow.session_mechanism == mech

        with pytest.raises(ValidationError):
            AuthFlow(session_mechanism="invalid")  # type: ignore[arg-type]


class TestWafProfile:
    def test_waf_profile_confidence_range(self) -> None:
        with pytest.raises(ValidationError):
            WafProfile(confidence=1.5)

        valid = WafProfile(confidence=0.85)
        assert valid.confidence == 0.85


class TestTechnology:
    def test_technology_minimal(self) -> None:
        tech = Technology(name="nginx")
        assert tech.name == "nginx"
        assert tech.version is None
        assert tech.category is None
