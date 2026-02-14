"""Unit tests for GeminiAPIProvider.

Test Coverage:
- ABC compliance (LLMProvider)
- Capability properties (oauth, multi-account, billing)
- Authentication with API keys
- Send request with respx mock
- Rate limit tracking
- Multi-key rotation on rate limit exhaustion
"""

from __future__ import annotations

import httpx
import pytest
import respx

from eazy.ai.exceptions import (
    AuthenticationError,
    ProviderError,
    RateLimitError,
)
from eazy.ai.models import (
    BillingType,
    LLMRequest,
    LLMResponse,
    ProviderType,
)
from eazy.ai.provider import LLMProvider
from eazy.ai.providers.gemini_api import GeminiAPIProvider

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

MOCK_GEMINI_RESPONSE = {
    "candidates": [
        {
            "content": {"parts": [{"text": "Hello!"}]},
            "finishReason": "STOP",
        }
    ],
    "usageMetadata": {
        "promptTokenCount": 5,
        "candidatesTokenCount": 8,
        "totalTokenCount": 13,
    },
    "modelVersion": "gemini-2.0-flash",
}


class TestGeminiAPIProvider:
    """Test suite for GeminiAPIProvider."""

    def test_gemini_api_provider_implements_llm_provider(self):
        """GeminiAPIProvider is a subclass of LLMProvider ABC."""
        # Arrange & Act
        provider = GeminiAPIProvider(api_keys=["test-key"])

        # Assert
        assert isinstance(provider, LLMProvider)

    def test_gemini_api_provider_capability_no_oauth(self):
        """GeminiAPIProvider does not support OAuth."""
        # Arrange
        provider = GeminiAPIProvider(api_keys=["test-key"])

        # Act & Assert
        assert provider.supports_oauth is False

    def test_gemini_api_provider_capability_multi_key(self):
        """GeminiAPIProvider supports multi-account (multi-key)."""
        # Arrange
        provider = GeminiAPIProvider(api_keys=["key1", "key2"])

        # Act & Assert
        assert provider.supports_multi_account is True

    def test_gemini_api_provider_billing_type_per_token(self):
        """GeminiAPIProvider uses per-token billing."""
        # Arrange
        provider = GeminiAPIProvider(api_keys=["test-key"])

        # Act & Assert
        assert provider.billing_type == BillingType.PER_TOKEN

    async def test_gemini_api_provider_authenticate_with_api_key(
        self,
    ):
        """Adding an API key via authenticate makes provider authenticated."""
        # Arrange
        provider = GeminiAPIProvider()

        # Act
        result = await provider.authenticate(api_key="new-key")

        # Assert
        assert result is True
        assert provider.is_authenticated is True

    async def test_gemini_api_provider_authenticate_fails_with_empty_key(
        self,
    ):
        """Empty or whitespace-only API key returns False."""
        # Arrange
        provider = GeminiAPIProvider()

        # Act
        result = await provider.authenticate(api_key="")

        # Assert
        assert result is False
        assert provider.is_authenticated is False

    @respx.mock
    async def test_gemini_api_provider_send_returns_llm_response(
        self,
    ):
        """Successful Gemini API call returns LLMResponse with correct fields."""
        # Arrange
        provider = GeminiAPIProvider(api_keys=["test-key"])
        request = LLMRequest(prompt="Say hello")

        respx.post(url__startswith=f"{GEMINI_API_BASE}/models/").mock(
            return_value=httpx.Response(200, json=MOCK_GEMINI_RESPONSE)
        )

        # Act
        response = await provider.send(request)

        # Assert
        assert isinstance(response, LLMResponse)
        assert response.content == "Hello!"
        assert response.model == "gemini-2.0-flash"
        assert response.provider_type == ProviderType.GEMINI_API
        assert response.input_tokens == 5
        assert response.output_tokens == 8
        assert response.finish_reason == "STOP"

    async def test_gemini_api_provider_send_raises_when_not_authenticated(
        self,
    ):
        """Sending without any API keys raises AuthenticationError."""
        # Arrange
        provider = GeminiAPIProvider()
        request = LLMRequest(prompt="Say hello")

        # Act & Assert
        with pytest.raises(AuthenticationError):
            await provider.send(request)

    @respx.mock
    async def test_gemini_api_provider_tracks_rate_limit(self):
        """After a successful send, rate limit counters decrement."""
        # Arrange
        provider = GeminiAPIProvider(api_keys=["test-key"])
        request = LLMRequest(prompt="Say hello")

        respx.post(url__startswith=f"{GEMINI_API_BASE}/models/").mock(
            return_value=httpx.Response(200, json=MOCK_GEMINI_RESPONSE)
        )

        # Act
        await provider.send(request)

        # Assert
        rate_limit = provider.get_rate_limit("test-key")
        assert rate_limit is not None
        assert rate_limit.remaining_minute == 14  # 15 - 1
        assert rate_limit.remaining_day == 1499  # 1500 - 1

    @respx.mock
    async def test_gemini_api_provider_rotates_keys_on_rate_limit(
        self,
    ):
        """When key1 is rate-limited, provider auto-switches to key2."""
        # Arrange
        provider = GeminiAPIProvider(api_keys=["key1", "key2"])
        request = LLMRequest(prompt="Say hello")

        # Exhaust key1 rate limit
        provider.exhaust_key("key1")

        respx.post(url__startswith=f"{GEMINI_API_BASE}/models/").mock(
            return_value=httpx.Response(200, json=MOCK_GEMINI_RESPONSE)
        )

        # Act
        response = await provider.send(request)

        # Assert — should succeed using key2
        assert isinstance(response, LLMResponse)
        assert response.content == "Hello!"
        # key2 should have decremented
        rate_limit = provider.get_rate_limit("key2")
        assert rate_limit is not None
        assert rate_limit.remaining_minute == 14

    @respx.mock
    async def test_send_raises_authentication_error_on_401(self):
        """HTTP 401 from Gemini API raises AuthenticationError."""
        # Arrange
        provider = GeminiAPIProvider(api_keys=["test-key"])
        request = LLMRequest(prompt="Say hello")
        respx.post(url__startswith=f"{GEMINI_API_BASE}/models/").mock(
            return_value=httpx.Response(401, json={"error": "unauthorized"})
        )

        # Act & Assert
        with pytest.raises(AuthenticationError):
            await provider.send(request)

    @respx.mock
    async def test_send_raises_rate_limit_error_on_429(self):
        """HTTP 429 from Gemini API raises RateLimitError."""
        # Arrange
        provider = GeminiAPIProvider(api_keys=["test-key"])
        request = LLMRequest(prompt="Say hello")
        respx.post(url__startswith=f"{GEMINI_API_BASE}/models/").mock(
            return_value=httpx.Response(429, json={"error": "rate limited"})
        )

        # Act & Assert
        with pytest.raises(RateLimitError):
            await provider.send(request)

    @respx.mock
    async def test_send_raises_provider_error_on_500(self):
        """HTTP 500 from Gemini API raises ProviderError."""
        # Arrange
        provider = GeminiAPIProvider(api_keys=["test-key"])
        request = LLMRequest(prompt="Say hello")
        respx.post(url__startswith=f"{GEMINI_API_BASE}/models/").mock(
            return_value=httpx.Response(500, json={"error": "internal"})
        )

        # Act & Assert
        with pytest.raises(ProviderError):
            await provider.send(request)

    @respx.mock
    async def test_send_exhausts_key_and_sets_reset_at_on_429(self):
        """HTTP 429 with Retry-After header exhausts key and sets reset_at."""
        # Arrange
        provider = GeminiAPIProvider(api_keys=["test-key"])
        request = LLMRequest(prompt="Say hello")
        respx.post(url__startswith=f"{GEMINI_API_BASE}/models/").mock(
            return_value=httpx.Response(
                429,
                headers={"retry-after": "60"},
                json={"error": "rate limited"},
            )
        )

        # Act
        with pytest.raises(RateLimitError):
            await provider.send(request)

        # Assert — key should be exhausted
        rl = provider.get_rate_limit("test-key")
        assert rl is not None
        assert rl.remaining_minute == 0
        assert rl.remaining_day == 0
        assert rl.reset_at is not None

    @respx.mock
    async def test_send_parses_retry_after_header(self):
        """RateLimitError includes retry_after from response header."""
        # Arrange
        provider = GeminiAPIProvider(api_keys=["test-key"])
        request = LLMRequest(prompt="Say hello")
        respx.post(url__startswith=f"{GEMINI_API_BASE}/models/").mock(
            return_value=httpx.Response(
                429,
                headers={"retry-after": "60"},
                json={"error": "rate limited"},
            )
        )

        # Act & Assert
        with pytest.raises(RateLimitError) as exc_info:
            await provider.send(request)
        assert exc_info.value.retry_after == 60
