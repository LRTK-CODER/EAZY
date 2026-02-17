"""Unit tests for Gemini OAuth provider."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock

import httpx
import respx

from eazy.ai.models import LLMResponse, OAuthTokens
from eazy.ai.plugins.gemini_oauth import (
    GEMINI_OAUTH_CONFIG,
    GeminiOAuthPlugin,
    GeminiOAuthProvider,
)

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/gemini-2.0-flash:generateContent"
)

SUCCESS_BODY = {
    "candidates": [
        {
            "content": {"parts": [{"text": "Response"}]},
            "finishReason": "STOP",
        }
    ],
    "usageMetadata": {
        "promptTokenCount": 10,
        "candidatesTokenCount": 5,
    },
}


def _future_ms(offset_s: int = 3600) -> int:
    """Return epoch ms in the future."""
    return int(time.time() * 1000) + offset_s * 1000


def _past_ms(offset_s: int = 60) -> int:
    """Return epoch ms in the past."""
    return int(time.time() * 1000) - offset_s * 1000


class TestGeminiOAuthPlugin:
    """Tests for GeminiOAuthPlugin authentication."""

    def test_oauth_config_has_correct_settings(self) -> None:
        """Config includes client_id, Google URLs, scopes."""
        assert GEMINI_OAUTH_CONFIG.client_id
        assert "google" in GEMINI_OAUTH_CONFIG.auth_url
        assert "google" in GEMINI_OAUTH_CONFIG.token_url
        assert len(GEMINI_OAUTH_CONFIG.scopes) > 0

    def test_is_expired_with_future_token_returns_false(
        self,
    ) -> None:
        """Token with future expiry is not expired."""
        plugin = GeminiOAuthPlugin()
        plugin._tokens = OAuthTokens(
            access_token="access",
            refresh_token="refresh",
            expires_at=_future_ms(),
        )

        assert plugin.is_expired() is False

    def test_is_expired_with_past_token_returns_true(
        self,
    ) -> None:
        """Token with past expiry is expired."""
        plugin = GeminiOAuthPlugin()
        plugin._tokens = OAuthTokens(
            access_token="access",
            refresh_token="refresh",
            expires_at=_past_ms(),
        )

        assert plugin.is_expired() is True

    async def test_refresh_calls_oauth_flow(self) -> None:
        """Refresh delegates to OAuthFlow.refresh_token."""
        new_tokens = OAuthTokens(
            access_token="new-access",
            refresh_token="new-refresh",
            expires_at=_future_ms(),
        )
        plugin = GeminiOAuthPlugin()
        plugin._tokens = OAuthTokens(
            access_token="old",
            refresh_token="old-refresh",
            expires_at=_past_ms(),
        )
        plugin._oauth_flow = AsyncMock()
        plugin._oauth_flow.refresh_token = AsyncMock(return_value=new_tokens)

        result = await plugin.refresh()

        assert result is True
        plugin._oauth_flow.refresh_token.assert_awaited_once_with("old-refresh")
        assert plugin._tokens == new_tokens


class TestGeminiOAuthProvider:
    """Tests for GeminiOAuthProvider LLM calls."""

    def _make_provider(self, expired: bool = False) -> GeminiOAuthProvider:
        expires_at = _past_ms() if expired else _future_ms()
        tokens = OAuthTokens(
            access_token="valid-token",
            refresh_token="refresh-token",
            expires_at=expires_at,
        )
        plugin = GeminiOAuthPlugin()
        plugin._tokens = tokens
        return GeminiOAuthProvider(plugin=plugin)

    @respx.mock
    async def test_send_with_valid_token_success(
        self,
    ) -> None:
        """Valid Bearer token sends successfully."""
        respx.post(GEMINI_API_URL).mock(
            return_value=httpx.Response(200, json=SUCCESS_BODY)
        )
        provider = self._make_provider()

        result = await provider.send("Hello")

        assert isinstance(result, LLMResponse)
        assert result.content == "Response"
        assert result.model == "gemini-2.0-flash"

    @respx.mock
    async def test_send_with_expired_token_auto_refreshes(
        self,
    ) -> None:
        """Expired token triggers refresh before sending."""
        respx.post(GEMINI_API_URL).mock(
            return_value=httpx.Response(200, json=SUCCESS_BODY)
        )
        new_tokens = OAuthTokens(
            access_token="new-access",
            refresh_token="new-refresh",
            expires_at=_future_ms(),
        )
        plugin = GeminiOAuthPlugin()
        plugin._tokens = OAuthTokens(
            access_token="expired-token",
            refresh_token="refresh",
            expires_at=_past_ms(),
        )
        plugin._oauth_flow = AsyncMock()
        plugin._oauth_flow.refresh_token = AsyncMock(return_value=new_tokens)
        provider = GeminiOAuthProvider(plugin=plugin)

        result = await provider.send("Hello")

        assert result.content == "Response"
        plugin._oauth_flow.refresh_token.assert_awaited_once()
