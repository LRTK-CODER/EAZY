"""Unit tests for Gemini API key provider."""

from __future__ import annotations

import httpx
import pytest
import respx

from eazy.ai.models import LLMError, LLMResponse, RateLimitError
from eazy.ai.plugins.gemini_api import GeminiApiPlugin, GeminiApiProvider

GEMINI_API_BASE = "https://generativelanguage.googleapis.com"
GEMINI_API_URL = f"{GEMINI_API_BASE}/v1beta/models/gemini-2.0-flash:generateContent"

SUCCESS_BODY = {
    "candidates": [
        {
            "content": {"parts": [{"text": "Hello!"}]},
            "finishReason": "STOP",
        }
    ],
    "usageMetadata": {
        "promptTokenCount": 5,
        "candidatesTokenCount": 3,
    },
}


class TestGeminiApiPlugin:
    """Tests for GeminiApiPlugin authentication."""

    async def test_authenticate_with_valid_key_returns_true(
        self,
    ) -> None:
        """Valid non-empty API key is accepted."""
        plugin = GeminiApiPlugin()

        result = await plugin.authenticate(api_key="test-key-123")

        assert result is True

    async def test_authenticate_with_empty_key_returns_false(
        self,
    ) -> None:
        """Empty API key is rejected."""
        plugin = GeminiApiPlugin()

        result = await plugin.authenticate(api_key="")

        assert result is False

    def test_is_expired_always_returns_false(self) -> None:
        """API keys do not expire."""
        plugin = GeminiApiPlugin()

        assert plugin.is_expired() is False


class TestGeminiApiProvider:
    """Tests for GeminiApiProvider LLM calls."""

    def _make_provider(self, api_key: str = "test-key") -> GeminiApiProvider:
        plugin = GeminiApiPlugin()
        plugin._api_key = api_key
        return GeminiApiProvider(plugin=plugin)

    @respx.mock
    async def test_send_success_returns_llm_response(
        self,
    ) -> None:
        """Successful API call returns parsed LLMResponse."""
        respx.post(GEMINI_API_URL).mock(
            return_value=httpx.Response(200, json=SUCCESS_BODY)
        )
        provider = self._make_provider()

        result = await provider.send("Hi")

        assert isinstance(result, LLMResponse)
        assert result.content == "Hello!"
        assert result.model == "gemini-2.0-flash"
        assert result.input_tokens == 5
        assert result.output_tokens == 3
        assert result.finish_reason == "STOP"

    @respx.mock
    async def test_send_api_error_raises_llm_error(
        self,
    ) -> None:
        """4xx/5xx responses raise LLMError."""
        respx.post(GEMINI_API_URL).mock(
            return_value=httpx.Response(500, json={"error": {"message": "Internal"}})
        )
        provider = self._make_provider()

        with pytest.raises(LLMError):
            await provider.send("Hi")

    @respx.mock
    async def test_send_rate_limit_raises_rate_limit_error(
        self,
    ) -> None:
        """HTTP 429 raises RateLimitError."""
        respx.post(GEMINI_API_URL).mock(
            return_value=httpx.Response(
                429,
                json={"error": {"message": "Rate limited"}},
            )
        )
        provider = self._make_provider()

        with pytest.raises(RateLimitError):
            await provider.send("Hi")

    def test_is_available_with_key_returns_true(self) -> None:
        """Provider with API key is available."""
        provider = self._make_provider(api_key="test-key")

        assert provider.is_available() is True

    def test_is_available_without_key_returns_false(self) -> None:
        """Provider without API key is not available."""
        plugin = GeminiApiPlugin()
        provider = GeminiApiProvider(plugin=plugin)

        assert provider.is_available() is False
