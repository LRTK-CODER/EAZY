"""Unit tests for OAuthFlowEngine (RED phase - implementation pending).

Test Coverage:
- Authorization URL generation with parameters
- State parameter generation (randomness)
- Code exchange for tokens
- Token refresh flow
- Token expiry detection
- Error handling for exchange failures
- Error handling for refresh failures
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from eazy.ai.models import OAuthTokens
from eazy.ai.oauth_flow import OAuthError, OAuthFlowEngine


class TestOAuthFlowEngine:
    """Test suite for OAuth 2.0 flow engine."""

    def test_oauth_flow_generates_authorization_url(self):
        """Auth URL contains client_id, redirect_uri, scope, response_type."""
        # Arrange
        engine = OAuthFlowEngine(
            client_id="test-client-id",
            client_secret="test-secret",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["openid", "email"],
        )

        # Act
        url = engine.generate_auth_url(
            redirect_uri="http://localhost:8080/callback",
            state="test-state",
        )

        # Assert
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert parsed.scheme == "https"
        assert parsed.netloc == "accounts.google.com"
        assert parsed.path == "/o/oauth2/v2/auth"
        assert params["client_id"] == ["test-client-id"]
        assert params["redirect_uri"] == ["http://localhost:8080/callback"]
        assert params["response_type"] == ["code"]
        assert params["scope"] == ["openid email"]
        assert params["state"] == ["test-state"]

    def test_oauth_flow_generates_state_parameter(self):
        """generate_state() returns unique random strings."""
        # Arrange
        engine = OAuthFlowEngine(
            client_id="test-client-id",
            client_secret="test-secret",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["openid"],
        )

        # Act
        state1 = engine.generate_state()
        state2 = engine.generate_state()

        # Assert
        assert isinstance(state1, str)
        assert isinstance(state2, str)
        assert len(state1) > 0
        assert len(state2) > 0
        assert state1 != state2  # Extremely unlikely collision

    @respx.mock
    async def test_oauth_flow_exchanges_code_for_tokens(self):
        """POST to token_url with code returns OAuthTokens."""
        # Arrange
        engine = OAuthFlowEngine(
            client_id="test-client-id",
            client_secret="test-secret",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["openid", "email"],
        )

        respx.post("https://oauth2.googleapis.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "at-123",
                    "refresh_token": "rt-456",
                    "expires_in": 3600,
                    "scope": "openid email",
                },
            )
        )

        # Act
        tokens = await engine.exchange_code(
            code="auth-code",
            redirect_uri="http://localhost:8080/callback",
        )

        # Assert
        assert isinstance(tokens, OAuthTokens)
        assert tokens.access_token == "at-123"
        assert tokens.refresh_token == "rt-456"
        assert tokens.scope == "openid email"
        assert tokens.expires_at is not None
        # Verify expires_at is approximately now + 3600 seconds
        expected_expiry = datetime.now(timezone.utc) + timedelta(seconds=3600)
        assert abs((tokens.expires_at - expected_expiry).total_seconds()) < 5

    @respx.mock
    async def test_oauth_flow_refreshes_expired_token(self):
        """POST with grant_type=refresh_token returns new OAuthTokens."""
        # Arrange
        engine = OAuthFlowEngine(
            client_id="test-client-id",
            client_secret="test-secret",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["openid"],
        )

        mock_route = respx.post("https://oauth2.googleapis.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "new-at-789",
                    "expires_in": 3600,
                    "scope": "openid",
                },
            )
        )

        # Act
        tokens = await engine.refresh_token(refresh_token="rt-456")

        # Assert
        assert isinstance(tokens, OAuthTokens)
        assert tokens.access_token == "new-at-789"
        assert tokens.scope == "openid"

        # Verify grant_type=refresh_token was sent in request
        request = mock_route.calls[0].request
        body = request.content.decode("utf-8")
        assert "grant_type=refresh_token" in body
        assert "refresh_token=rt-456" in body

    def test_oauth_flow_detects_token_expiry(self):
        """past→True, future→False, None→True."""
        # Arrange
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        # Act & Assert
        assert OAuthFlowEngine.is_token_expired(past) is True
        assert OAuthFlowEngine.is_token_expired(future) is False
        assert OAuthFlowEngine.is_token_expired(None) is True

    @respx.mock
    async def test_oauth_flow_handles_exchange_failure(self):
        """Token exchange HTTP 400 raises OAuthError."""
        # Arrange
        engine = OAuthFlowEngine(
            client_id="test-client-id",
            client_secret="test-secret",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["openid"],
        )

        respx.post("https://oauth2.googleapis.com/token").mock(
            return_value=httpx.Response(
                400,
                json={"error": "invalid_grant", "error_description": "Bad code"},
            )
        )

        # Act & Assert
        with pytest.raises(OAuthError):
            await engine.exchange_code(
                code="bad-code",
                redirect_uri="http://localhost:8080/callback",
            )

    @respx.mock
    async def test_oauth_flow_handles_refresh_failure(self):
        """Token refresh HTTP 401 raises OAuthError."""
        # Arrange
        engine = OAuthFlowEngine(
            client_id="test-client-id",
            client_secret="test-secret",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["openid"],
        )

        respx.post("https://oauth2.googleapis.com/token").mock(
            return_value=httpx.Response(
                401,
                json={
                    "error": "invalid_client",
                    "error_description": "Invalid token",
                },
            )
        )

        # Act & Assert
        with pytest.raises(OAuthError):
            await engine.refresh_token(refresh_token="bad-refresh-token")
