"""Unit tests for OAuth flow infrastructure."""

from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from eazy.ai.models import LLMError, OAuthConfig, OAuthTokens
from eazy.ai.oauth_flow import OAuthCallbackServer, OAuthFlow

TEST_CONFIG = OAuthConfig(
    client_id="test-client-id",
    client_secret="test-client-secret",
    auth_url="https://accounts.google.com/o/oauth2/auth",
    token_url="https://oauth2.googleapis.com/token",
    scopes=("scope1", "scope2"),
)

TOKEN_SUCCESS_BODY = {
    "access_token": "access123",
    "refresh_token": "refresh456",
    "expires_in": 3600,
}


class TestOAuthFlow:
    """Tests for OAuthFlow URL building and token exchange."""

    def test_build_auth_url_contains_required_params(
        self,
    ) -> None:
        """Auth URL includes client_id, scopes, redirect_uri."""
        flow = OAuthFlow(config=TEST_CONFIG)

        url = flow.build_auth_url(redirect_uri="http://localhost:8080")

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert params["client_id"] == ["test-client-id"]
        assert params["response_type"] == ["code"]
        assert params["redirect_uri"] == ["http://localhost:8080"]
        scope_str = params["scope"][0]
        assert "scope1" in scope_str
        assert "scope2" in scope_str

    @respx.mock
    async def test_exchange_code_success_returns_tokens(
        self,
    ) -> None:
        """Valid auth code exchanges for OAuthTokens."""
        respx.post(TEST_CONFIG.token_url).mock(
            return_value=httpx.Response(200, json=TOKEN_SUCCESS_BODY)
        )
        flow = OAuthFlow(config=TEST_CONFIG)

        tokens = await flow.exchange_code(
            code="auth-code",
            redirect_uri="http://localhost:8080",
        )

        assert isinstance(tokens, OAuthTokens)
        assert tokens.access_token == "access123"
        assert tokens.refresh_token == "refresh456"
        assert tokens.expires_at > 0

    @respx.mock
    async def test_exchange_code_error_raises_llm_error(
        self,
    ) -> None:
        """Invalid auth code raises LLMError."""
        respx.post(TEST_CONFIG.token_url).mock(
            return_value=httpx.Response(400, json={"error": "invalid_grant"})
        )
        flow = OAuthFlow(config=TEST_CONFIG)

        with pytest.raises(LLMError):
            await flow.exchange_code(
                code="bad-code",
                redirect_uri="http://localhost:8080",
            )

    @respx.mock
    async def test_refresh_token_success_returns_new_tokens(
        self,
    ) -> None:
        """Valid refresh token returns new OAuthTokens."""
        respx.post(TEST_CONFIG.token_url).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "new-access",
                    "refresh_token": "new-refresh",
                    "expires_in": 3600,
                },
            )
        )
        flow = OAuthFlow(config=TEST_CONFIG)

        tokens = await flow.refresh_token("old-refresh")

        assert isinstance(tokens, OAuthTokens)
        assert tokens.access_token == "new-access"
        assert tokens.refresh_token == "new-refresh"

    @respx.mock
    async def test_refresh_token_error_raises_llm_error(
        self,
    ) -> None:
        """Expired refresh token raises LLMError."""
        respx.post(TEST_CONFIG.token_url).mock(
            return_value=httpx.Response(400, json={"error": "invalid_grant"})
        )
        flow = OAuthFlow(config=TEST_CONFIG)

        with pytest.raises(LLMError):
            await flow.refresh_token("expired-refresh")


class TestOAuthCallbackServer:
    """Tests for OAuth callback HTTP server."""

    async def test_callback_server_receives_code(
        self,
    ) -> None:
        """Server captures authorization code from GET request."""
        server = OAuthCallbackServer(timeout=5)
        port = await server.start()

        async def send_code() -> None:
            await asyncio.sleep(0.1)
            async with httpx.AsyncClient() as client:
                await client.get(f"http://localhost:{port}/?code=test-code-123")

        task = asyncio.create_task(send_code())
        code = await server.wait_for_code()
        await task

        assert code == "test-code-123"

    async def test_callback_server_timeout_raises_error(
        self,
    ) -> None:
        """Server raises LLMError on timeout."""
        server = OAuthCallbackServer(timeout=0.1)
        await server.start()

        with pytest.raises(LLMError, match="[Tt]imeout"):
            await server.wait_for_code()
