"""Factory for creating LLM provider instances from configuration."""

from __future__ import annotations

from eazy.ai.models import ProviderConfig, ProviderType
from eazy.ai.provider import LLMProvider
from eazy.ai.providers.antigravity import AntigravityOAuthProvider
from eazy.ai.providers.gemini_api import GeminiAPIProvider
from eazy.ai.providers.gemini_oauth import GeminiOAuthProvider
from eazy.ai.token_storage import TokenStorage


class ProviderFactory:
    """Factory for creating LLM provider instances from config."""

    @staticmethod
    def create(
        config: ProviderConfig,
        token_storage: TokenStorage | None = None,
    ) -> LLMProvider:
        """Create a provider from configuration.

        Args:
            config: Provider configuration with type and credentials.
            token_storage: Required for OAuth-based providers.

        Returns:
            Configured LLMProvider instance.

        Raises:
            ValueError: If provider type is unknown or
                token_storage missing for OAuth providers.
        """
        if config.provider_type == ProviderType.GEMINI_API:
            keys = [config.api_key] if config.api_key else []
            return GeminiAPIProvider(
                api_keys=keys,
                endpoint_url=config.endpoint_url,
            )

        if config.provider_type in (
            ProviderType.GEMINI_OAUTH,
            ProviderType.ANTIGRAVITY,
        ):
            if token_storage is None:
                msg = "token_storage required for OAuth providers."
                raise ValueError(msg)
            if config.provider_type == ProviderType.GEMINI_OAUTH:
                return GeminiOAuthProvider(
                    token_storage=token_storage,
                )
            return AntigravityOAuthProvider(
                token_storage=token_storage,
            )

        raise ValueError(f"Unknown provider type: {config.provider_type}")
