"""Pydantic data models for LLM provider integration."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class BillingType(str, Enum):
    """Billing model classification for LLM providers.

    Attributes:
        SUBSCRIPTION: Fixed-rate subscription (e.g. Gemini Advanced).
        PER_TOKEN: Pay-per-token usage (e.g. API key billing).
        FREE: No-cost tier with rate limits.
    """

    SUBSCRIPTION = "subscription"
    PER_TOKEN = "per_token"
    FREE = "free"


class ProviderType(str, Enum):
    """LLM provider type identifier.

    Attributes:
        GEMINI_OAUTH: Gemini via Google OAuth authentication.
        ANTIGRAVITY: Gemini via Antigravity IDE OAuth.
        GEMINI_API: Gemini via API key authentication.
    """

    GEMINI_OAUTH = "gemini_oauth"
    ANTIGRAVITY = "antigravity"
    GEMINI_API = "gemini_api"


class AccountStatus(str, Enum):
    """Account health status for multi-account management.

    Attributes:
        ACTIVE: Account is available for requests.
        RATE_LIMITED: Account has hit rate limits.
        EXPIRED: Account credentials have expired.
        REVOKED: Account access has been revoked.
    """

    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    EXPIRED = "expired"
    REVOKED = "revoked"


class LLMRequest(BaseModel):
    """Immutable request payload for LLM inference.

    Attributes:
        prompt: The user prompt to send.
        model: Model identifier string.
        system_prompt: Optional system instruction.
        temperature: Sampling temperature (0.0 to 1.0).
        max_tokens: Maximum tokens in the response.
        response_format: Expected response format hint.
    """

    model_config = ConfigDict(frozen=True)

    prompt: str
    model: str = "gemini-2.0-flash"
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    response_format: str | None = None


class LLMResponse(BaseModel):
    """Immutable response from an LLM provider.

    Attributes:
        content: The generated text content.
        model: Model that produced the response.
        provider_type: Which provider handled the request.
        input_tokens: Number of input tokens consumed.
        output_tokens: Number of output tokens generated.
        finish_reason: Why generation stopped.
    """

    model_config = ConfigDict(frozen=True)

    content: str
    model: str
    provider_type: ProviderType
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str | None = None


class RateLimitInfo(BaseModel):
    """Mutable rate limit tracking for an account.

    Attributes:
        max_requests_per_minute: Maximum requests per minute.
        max_requests_per_day: Maximum requests per day.
        remaining_minute: Remaining requests this minute.
        remaining_day: Remaining requests today.
        reset_at: When the rate limit window resets.
    """

    max_requests_per_minute: int
    max_requests_per_day: int
    remaining_minute: int
    remaining_day: int
    reset_at: datetime | None = None

    @property
    def is_exceeded(self) -> bool:
        """Check if any rate limit has been exceeded.

        Returns:
            True if minute or day remaining is zero or less.
        """
        return self.remaining_minute <= 0 or self.remaining_day <= 0


class AccountInfo(BaseModel):
    """Account metadata for multi-account management.

    Attributes:
        account_id: Unique account identifier (e.g. email).
        provider_type: Which LLM provider this account uses.
        status: Current health status of the account.
        rate_limit: Optional rate limit tracking info.
        last_used: Timestamp of last successful request.
    """

    account_id: str
    provider_type: ProviderType
    status: AccountStatus = AccountStatus.ACTIVE
    rate_limit: RateLimitInfo | None = None
    last_used: datetime | None = None


class ProviderConfig(BaseModel):
    """Immutable configuration for an LLM provider.

    Attributes:
        provider_type: Which provider to configure.
        api_key: API key for key-based authentication.
        oauth_client_id: OAuth client ID.
        oauth_client_secret: OAuth client secret.
        endpoint_url: Custom API endpoint URL.
    """

    model_config = ConfigDict(frozen=True)

    provider_type: ProviderType
    api_key: str | None = None
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = None
    endpoint_url: str | None = None


class OAuthTokens(BaseModel):
    """Immutable OAuth token set from authorization flow.

    Attributes:
        access_token: Bearer token for API requests.
        refresh_token: Token used to obtain new access tokens.
        expires_at: When the access token expires (UTC).
        scope: Space-separated list of granted scopes.
    """

    model_config = ConfigDict(frozen=True)

    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None
    scope: str = ""
