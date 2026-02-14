"""Integration tests for LLM provider end-to-end workflows."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from eazy.ai.account_manager import AccountManager
from eazy.ai.models import (
    AccountInfo,
    LLMRequest,
    ProviderConfig,
    ProviderType,
)
from eazy.ai.provider_factory import ProviderFactory
from eazy.ai.providers.gemini_api import GeminiAPIProvider


def _gemini_success_response() -> dict:
    """Build a mock Gemini API success response."""
    return {
        "candidates": [
            {
                "content": {"parts": [{"text": "Hello from Gemini!"}]},
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 5,
            "candidatesTokenCount": 10,
        },
        "modelVersion": "gemini-2.0-flash",
    }


class TestProviderIntegration:
    @respx.mock
    @pytest.mark.asyncio
    async def test_end_to_end_send_with_gemini_api_provider(self):
        """Factory creates provider, provider sends request, returns LLMResponse."""
        config = ProviderConfig(
            provider_type=ProviderType.GEMINI_API,
            api_key="test-api-key",
        )
        provider = ProviderFactory.create(config)

        respx.post(
            "https://generativelanguage.googleapis.com/v1beta"
            "/models/gemini-2.0-flash:generateContent"
        ).mock(return_value=Response(200, json=_gemini_success_response()))

        request = LLMRequest(prompt="Hello")
        response = await provider.send(request)

        assert response.content == "Hello from Gemini!"
        assert response.provider_type == ProviderType.GEMINI_API
        assert response.input_tokens == 5
        assert response.output_tokens == 10

    @respx.mock
    @pytest.mark.asyncio
    async def test_end_to_end_send_with_auto_account_switching(self):
        """Two accounts registered; first rate-limited, second used."""
        manager = AccountManager()

        account1 = AccountInfo(
            account_id="acct1@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        account2 = AccountInfo(
            account_id="acct2@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        provider1 = GeminiAPIProvider(api_keys=["key1"])
        provider2 = GeminiAPIProvider(api_keys=["key2"])

        manager.register(account1, provider1)
        manager.register(account2, provider2)

        # Mark first account as rate-limited
        manager.mark_rate_limited("acct1@test.com")

        # get_active should return second account
        active_account, active_provider = manager.get_active(
            ProviderType.GEMINI_API,
        )
        assert active_account.account_id == "acct2@test.com"

        respx.post(
            "https://generativelanguage.googleapis.com/v1beta"
            "/models/gemini-2.0-flash:generateContent"
        ).mock(return_value=Response(200, json=_gemini_success_response()))

        request = LLMRequest(prompt="Test prompt")
        response = await active_provider.send(request)

        assert response.content == "Hello from Gemini!"

    @respx.mock
    @pytest.mark.asyncio
    async def test_provider_factory_integration_with_account_manager(
        self,
    ):
        """Factory creates provider, registered in AccountManager, sends."""
        config = ProviderConfig(
            provider_type=ProviderType.GEMINI_API,
            api_key="integration-key",
        )
        provider = ProviderFactory.create(config)

        manager = AccountManager()
        account = AccountInfo(
            account_id="factory@test.com",
            provider_type=ProviderType.GEMINI_API,
        )
        manager.register(account, provider)

        active_account, active_provider = manager.get_active(
            ProviderType.GEMINI_API,
        )
        assert active_account.account_id == "factory@test.com"

        respx.post(
            "https://generativelanguage.googleapis.com/v1beta"
            "/models/gemini-2.0-flash:generateContent"
        ).mock(return_value=Response(200, json=_gemini_success_response()))

        request = LLMRequest(prompt="Integration test")
        response = await active_provider.send(request)

        assert response.content == "Hello from Gemini!"
        assert response.provider_type == ProviderType.GEMINI_API
