"""RED phase tests for LLMProvider ABC and ProviderRegistry."""

from __future__ import annotations

import pytest

from eazy.ai.models import LLMResponse
from eazy.ai.provider import LLMProvider, ProviderRegistry

# ---------------------------------------------------------------------------
# Minimal concrete subclasses used across tests
# ---------------------------------------------------------------------------


class FullProvider(LLMProvider):
    """Fully implemented provider for valid-instantiation tests."""

    @property
    def name(self) -> str:
        return "full-provider"

    async def send(self, prompt: str, **kwargs) -> LLMResponse:
        return LLMResponse(content="ok", model="test")

    def is_available(self) -> bool:
        return True


class NoSendProvider(LLMProvider):
    """Concrete provider missing the send() method."""

    @property
    def name(self) -> str:
        return "no-send"

    def is_available(self) -> bool:
        return True


class NoIsAvailableProvider(LLMProvider):
    """Concrete provider missing the is_available() method."""

    @property
    def name(self) -> str:
        return "no-is-available"

    async def send(self, prompt: str, **kwargs) -> LLMResponse:
        return LLMResponse(content="ok", model="test")


class NoNameProvider(LLMProvider):
    """Concrete provider missing the name property."""

    async def send(self, prompt: str, **kwargs) -> LLMResponse:
        return LLMResponse(content="ok", model="test")

    def is_available(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLLMProvider:
    def test_cannot_instantiate_abc(self):
        """Instantiating LLMProvider directly raises TypeError.

        LLMProvider is an abstract base class and must not be
        instantiable without implementing all abstract members.
        """
        with pytest.raises(TypeError):
            LLMProvider()  # type: ignore[abstract]

    def test_concrete_requires_send(self):
        """Subclass missing send() raises TypeError on instantiation.

        All three abstract members must be implemented; omitting send()
        alone is sufficient to prevent instantiation.
        """
        with pytest.raises(TypeError):
            NoSendProvider()

    def test_concrete_requires_is_available(self):
        """Subclass missing is_available() raises TypeError on instantiation.

        Omitting is_available() alone is sufficient to prevent
        instantiation of an otherwise complete subclass.
        """
        with pytest.raises(TypeError):
            NoIsAvailableProvider()

    def test_concrete_requires_name(self):
        """Subclass missing name property raises TypeError on instantiation.

        The name abstract property must be implemented; omitting it
        prevents the class from being instantiated.
        """
        with pytest.raises(TypeError):
            NoNameProvider()


class TestProviderRegistry:
    def test_register_and_get(self):
        """Registered provider is returned by get() with the same instance.

        Arrange: create a fresh registry and a FullProvider instance.
        Act: register the provider, then call get() with its name.
        Assert: the returned object is identical to the registered one.
        """
        registry = ProviderRegistry()
        provider = FullProvider()

        registry.register(provider)

        assert registry.get("full-provider") is provider

    def test_list_providers(self):
        """list_providers() returns all registered provider names.

        Arrange: register two providers with distinct names.
        Act: call list_providers().
        Assert: both names appear in the result (order is not asserted).
        """

        class ProviderA(LLMProvider):
            @property
            def name(self) -> str:
                return "provider-a"

            async def send(self, prompt: str, **kwargs) -> LLMResponse:
                return LLMResponse(content="a", model="test")

            def is_available(self) -> bool:
                return True

        class ProviderB(LLMProvider):
            @property
            def name(self) -> str:
                return "provider-b"

            async def send(self, prompt: str, **kwargs) -> LLMResponse:
                return LLMResponse(content="b", model="test")

            def is_available(self) -> bool:
                return True

        registry = ProviderRegistry()
        registry.register(ProviderA())
        registry.register(ProviderB())

        names = registry.list_providers()

        assert "provider-a" in names
        assert "provider-b" in names

    def test_duplicate_raises_error(self):
        """Registering a provider with a duplicate name raises ValueError.

        Arrange: register a provider, then create a second provider with
        the identical name.
        Act: attempt to register the second provider.
        Assert: ValueError is raised.
        """
        registry = ProviderRegistry()
        registry.register(FullProvider())

        with pytest.raises(ValueError):
            registry.register(FullProvider())

    def test_get_unregistered_returns_none(self):
        """get() returns None when the requested name is not registered.

        Arrange: create an empty registry.
        Act: call get() with an arbitrary unknown name.
        Assert: the result is None.
        """
        registry = ProviderRegistry()

        result = registry.get("nonexistent-provider")

        assert result is None
