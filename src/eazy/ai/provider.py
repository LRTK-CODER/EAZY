"""Abstract base class for LLM provider implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from eazy.ai.models import BillingType, LLMRequest, LLMResponse, ProviderType


class LLMProvider(ABC):
    """Abstract base for LLM provider integrations.

    All provider implementations must inherit from this class and implement
    all abstract methods and properties. This ensures a consistent interface
    across different LLM backends (Gemini OAuth, API key, etc.).
    """

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Get the provider type identifier.

        Returns:
            The ProviderType enum value for this provider.
        """

    @property
    @abstractmethod
    def supports_oauth(self) -> bool:
        """Check if this provider supports OAuth authentication.

        Returns:
            True if OAuth is supported, False otherwise.
        """

    @property
    @abstractmethod
    def supports_multi_account(self) -> bool:
        """Check if this provider supports multiple account management.

        Returns:
            True if multi-account is supported, False otherwise.
        """

    @property
    @abstractmethod
    def billing_type(self) -> BillingType:
        """Get the billing model for this provider.

        Returns:
            The BillingType enum value (subscription, per_token, or free).
        """

    @property
    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if the provider is currently authenticated.

        Returns:
            True if authenticated and ready to send requests.
        """

    @abstractmethod
    async def send(self, request: LLMRequest) -> LLMResponse:
        """Send a request to the LLM provider and return the response.

        Args:
            request: The LLMRequest containing prompt and parameters.

        Returns:
            LLMResponse with generated content and metadata.

        Raises:
            AuthenticationError: If not authenticated.
            RateLimitError: If rate limit exceeded.
            ProviderError: For other provider-specific errors.
        """

    @abstractmethod
    async def authenticate(self, **kwargs) -> bool:
        """Authenticate with the LLM provider.

        Args:
            **kwargs: Provider-specific authentication parameters
                (e.g., api_key, oauth_token, credentials).

        Returns:
            True if authentication succeeded, False otherwise.

        Raises:
            AuthenticationError: If authentication fails with details.
        """
