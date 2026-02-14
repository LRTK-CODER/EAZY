"""Exception classes for LLM provider errors."""

from __future__ import annotations


class ProviderError(Exception):
    """Base exception for LLM provider errors."""


class AuthenticationError(ProviderError):
    """Raised when authentication fails or is missing."""


class RateLimitError(ProviderError):
    """Raised when all available keys/accounts have exceeded rate limits."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
