"""Unit tests for LLMProvider abstract base class."""

from __future__ import annotations

import pytest

from eazy.ai.models import (
    BillingType,
    LLMRequest,
    LLMResponse,
    ProviderType,
)
from eazy.ai.provider import LLMProvider


class TestLLMProvider:
    def test_llm_provider_cannot_be_instantiated(self):
        """LLMProvider ABC should not be directly instantiable."""
        with pytest.raises(TypeError):
            LLMProvider()

    def test_llm_provider_requires_send_method(self):
        """LLMProvider subclass must implement send()."""

        class IncompleteProvider(LLMProvider):
            @property
            def provider_type(self) -> ProviderType:
                return ProviderType.GEMINI_API

            @property
            def supports_oauth(self) -> bool:
                return False

            @property
            def supports_multi_account(self) -> bool:
                return False

            @property
            def billing_type(self) -> BillingType:
                return BillingType.FREE

            @property
            def is_authenticated(self) -> bool:
                return False

            async def authenticate(self, **kwargs) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_llm_provider_requires_authenticate_method(self):
        """LLMProvider subclass must implement authenticate()."""

        class IncompleteProvider(LLMProvider):
            @property
            def provider_type(self) -> ProviderType:
                return ProviderType.GEMINI_API

            @property
            def supports_oauth(self) -> bool:
                return False

            @property
            def supports_multi_account(self) -> bool:
                return False

            @property
            def billing_type(self) -> BillingType:
                return BillingType.FREE

            @property
            def is_authenticated(self) -> bool:
                return False

            async def send(self, request: LLMRequest) -> LLMResponse:
                return LLMResponse(
                    content="test",
                    model="test",
                    provider_type=ProviderType.GEMINI_API,
                )

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_llm_provider_requires_is_authenticated_property(
        self,
    ):
        """LLMProvider subclass must implement is_authenticated."""

        class IncompleteProvider(LLMProvider):
            @property
            def provider_type(self) -> ProviderType:
                return ProviderType.GEMINI_API

            @property
            def supports_oauth(self) -> bool:
                return False

            @property
            def supports_multi_account(self) -> bool:
                return False

            @property
            def billing_type(self) -> BillingType:
                return BillingType.FREE

            async def send(self, request: LLMRequest) -> LLMResponse:
                return LLMResponse(
                    content="test",
                    model="test",
                    provider_type=ProviderType.GEMINI_API,
                )

            async def authenticate(self, **kwargs) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_llm_provider_has_capability_properties(self):
        """LLMProvider should require capability properties."""

        class IncompleteProvider(LLMProvider):
            @property
            def is_authenticated(self) -> bool:
                return False

            async def send(self, request: LLMRequest) -> LLMResponse:
                return LLMResponse(
                    content="test",
                    model="test",
                    provider_type=ProviderType.GEMINI_API,
                )

            async def authenticate(self, **kwargs) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_concrete_provider_can_be_instantiated(self):
        """A fully implemented LLMProvider should instantiate."""

        class ConcreteProvider(LLMProvider):
            @property
            def provider_type(self) -> ProviderType:
                return ProviderType.GEMINI_API

            @property
            def supports_oauth(self) -> bool:
                return False

            @property
            def supports_multi_account(self) -> bool:
                return True

            @property
            def billing_type(self) -> BillingType:
                return BillingType.PER_TOKEN

            @property
            def is_authenticated(self) -> bool:
                return False

            async def send(self, request: LLMRequest) -> LLMResponse:
                return LLMResponse(
                    content="response",
                    model="test-model",
                    provider_type=ProviderType.GEMINI_API,
                )

            async def authenticate(self, **kwargs) -> bool:
                return True

        provider = ConcreteProvider()
        assert provider.provider_type == ProviderType.GEMINI_API
        assert provider.supports_oauth is False
        assert provider.supports_multi_account is True
        assert provider.billing_type == BillingType.PER_TOKEN
        assert provider.is_authenticated is False
