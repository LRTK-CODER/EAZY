"""LLM provider abstraction and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from eazy.ai.models import LLMResponse


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Subclasses must implement name, send, and is_available.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier."""

    @abstractmethod
    async def send(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Send a prompt to the LLM and return a response.

        Args:
            prompt: Text prompt to send.
            **kwargs: Provider-specific parameters.

        Returns:
            LLM response with content and metadata.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the provider is ready to accept requests."""


class ProviderRegistry:
    """Registry for managing LLM provider instances.

    Provides registration, lookup, and listing of providers
    by their unique name.
    """

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}

    def register(self, provider: LLMProvider) -> None:
        """Register a provider instance.

        Args:
            provider: Provider to register.

        Raises:
            ValueError: If a provider with the same name
                is already registered.
        """
        if provider.name in self._providers:
            msg = f"Provider '{provider.name}' is already registered"
            raise ValueError(msg)
        self._providers[provider.name] = provider

    def get(self, name: str) -> LLMProvider | None:
        """Look up a provider by name.

        Args:
            name: Provider name to look up.

        Returns:
            The provider instance, or None if not found.
        """
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """Return names of all registered providers.

        Returns:
            List of registered provider names.
        """
        return list(self._providers.keys())
