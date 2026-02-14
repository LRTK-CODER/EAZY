"""Exception classes for LLM provider errors."""

from __future__ import annotations


class ProviderError(Exception):
    """Base exception for LLM provider errors."""


class AuthenticationError(ProviderError):
    """Raised when authentication fails or is missing."""


class RateLimitError(ProviderError):
    """Raised when all available keys/accounts have exceeded rate limits."""
