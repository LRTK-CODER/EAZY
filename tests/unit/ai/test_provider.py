"""Unit tests for LLMProvider abstract base class and ProviderFactory."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from eazy.ai.models import (
    BillingType,
    LLMRequest,
    LLMResponse,
    ProviderConfig,
    ProviderType,
)
from eazy.ai.provider import LLMProvider
from eazy.ai.provider_factory import ProviderFactory
from eazy.ai.providers.antigravity import AntigravityOAuthProvider
from eazy.ai.providers.gemini_api import GeminiAPIProvider
from eazy.ai.providers.gemini_oauth import GeminiOAuthProvider
from eazy.ai.token_storage import TokenStorage


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


class TestProviderFactory:
    def test_provider_factory_creates_gemini_api_provider(self):
        """GEMINI_API config creates GeminiAPIProvider."""
        config = ProviderConfig(
            provider_type=ProviderType.GEMINI_API,
            api_key="test-key",
        )
        provider = ProviderFactory.create(config)

        assert isinstance(provider, GeminiAPIProvider)
        assert provider.provider_type == ProviderType.GEMINI_API
        assert provider.is_authenticated is True

    def test_provider_factory_creates_gemini_oauth_provider(self, tmp_path):
        """GEMINI_OAUTH config creates GeminiOAuthProvider."""
        token_storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        config = ProviderConfig(
            provider_type=ProviderType.GEMINI_OAUTH,
        )
        provider = ProviderFactory.create(config, token_storage=token_storage)

        assert isinstance(provider, GeminiOAuthProvider)
        assert provider.provider_type == ProviderType.GEMINI_OAUTH

    def test_provider_factory_creates_antigravity_provider(self, tmp_path):
        """ANTIGRAVITY config creates AntigravityOAuthProvider."""
        token_storage = TokenStorage(
            base_dir=tmp_path,
            encryption_key=Fernet.generate_key(),
        )
        config = ProviderConfig(
            provider_type=ProviderType.ANTIGRAVITY,
        )
        provider = ProviderFactory.create(config, token_storage=token_storage)

        assert isinstance(provider, AntigravityOAuthProvider)
        assert provider.provider_type == ProviderType.ANTIGRAVITY

    def test_provider_factory_raises_for_unknown_type(self):
        """Unknown provider type raises ValueError."""
        config = ProviderConfig(
            provider_type=ProviderType.GEMINI_API,
        )
        # Monkey-patch provider_type to simulate unknown
        object.__setattr__(config, "provider_type", "unknown_type")

        with pytest.raises(ValueError, match="Unknown provider type"):
            ProviderFactory.create(config)
