"""Unit tests for OAuthFlowEngine.

Test Coverage:
- Authorization URL generation with parameters
- State parameter generation (randomness)
- Code exchange for tokens
- Token refresh flow
- Token expiry detection
- Error handling for exchange failures
- Error handling for refresh failures
- Interactive browser flow: opens browser
- Interactive browser flow: returns tokens
- Interactive browser flow: state mismatch error
- Interactive browser flow: timeout error
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
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

    async def test_interactive_flow_opens_browser(self):
        """run_interactive_flow() calls webbrowser.open with auth URL."""
        # Arrange
        engine = OAuthFlowEngine(
            client_id="test-client-id",
            client_secret="test-secret",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["openid", "email"],
        )

        captured_url = None

        def mock_open(url: str) -> bool:
            nonlocal captured_url
            captured_url = url
            return True

        with patch(
            "eazy.ai.oauth_flow.webbrowser.open",
            side_effect=mock_open,
        ):
            flow_task = asyncio.create_task(engine.run_interactive_flow(timeout=3.0))
            await asyncio.sleep(0.3)

            # Extract redirect_uri and state from captured URL
            assert captured_url is not None
            params = parse_qs(urlparse(captured_url).query)
            assert params["client_id"] == ["test-client-id"]
            assert "openid email" in params["scope"][0]
            state = params["state"][0]
            redirect_uri = params["redirect_uri"][0]

            # Simulate callback to unblock the flow
            async with httpx.AsyncClient() as client:
                await client.get(f"{redirect_uri}?code=auth_code&state={state}")

            # Cancel to avoid exchange_code failure (no mock)
            flow_task.cancel()
            with pytest.raises((asyncio.CancelledError, OAuthError)):
                await flow_task

    @respx.mock
    async def test_interactive_flow_returns_tokens(self):
        """Full interactive flow returns OAuthTokens on success."""
        # Arrange
        engine = OAuthFlowEngine(
            client_id="test-client-id",
            client_secret="test-secret",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["openid"],
        )

        # Allow localhost passthrough for callback server
        respx.route(host="localhost").pass_through()
        respx.post("https://oauth2.googleapis.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "interactive-at",
                    "refresh_token": "interactive-rt",
                    "expires_in": 3600,
                    "scope": "openid",
                },
            )
        )

        captured_url = None

        def mock_open(url: str) -> bool:
            nonlocal captured_url
            captured_url = url
            return True

        with patch(
            "eazy.ai.oauth_flow.webbrowser.open",
            side_effect=mock_open,
        ):
            flow_task = asyncio.create_task(engine.run_interactive_flow(timeout=5.0))
            await asyncio.sleep(0.3)

            # Extract state and redirect_uri from browser URL
            params = parse_qs(urlparse(captured_url).query)
            state = params["state"][0]
            redirect_uri = params["redirect_uri"][0]

            # Simulate OAuth callback
            async with httpx.AsyncClient() as client:
                await client.get(f"{redirect_uri}?code=auth_code_123&state={state}")

            tokens = await flow_task

        # Assert
        assert isinstance(tokens, OAuthTokens)
        assert tokens.access_token == "interactive-at"
        assert tokens.refresh_token == "interactive-rt"

    async def test_interactive_flow_raises_on_state_mismatch(self):
        """Wrong state in callback raises OAuthError."""
        # Arrange
        engine = OAuthFlowEngine(
            client_id="test-client-id",
            client_secret="test-secret",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["openid"],
        )

        captured_url = None

        def mock_open(url: str) -> bool:
            nonlocal captured_url
            captured_url = url
            return True

        with patch(
            "eazy.ai.oauth_flow.webbrowser.open",
            side_effect=mock_open,
        ):
            flow_task = asyncio.create_task(engine.run_interactive_flow(timeout=3.0))
            await asyncio.sleep(0.3)

            # Send callback with WRONG state
            params = parse_qs(urlparse(captured_url).query)
            redirect_uri = params["redirect_uri"][0]

            async with httpx.AsyncClient() as client:
                await client.get(f"{redirect_uri}?code=auth_code&state=wrong_state")

            with pytest.raises(OAuthError, match="State mismatch"):
                await flow_task

    async def test_interactive_flow_raises_on_timeout(self):
        """No callback within timeout raises OAuthError."""
        # Arrange
        engine = OAuthFlowEngine(
            client_id="test-client-id",
            client_secret="test-secret",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["openid"],
        )

        with patch(
            "eazy.ai.oauth_flow.webbrowser.open",
            return_value=True,
        ):
            # Act & Assert
            with pytest.raises(OAuthError, match="timed out"):
                await engine.run_interactive_flow(timeout=0.5)
