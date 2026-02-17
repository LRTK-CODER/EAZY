"""AI data models for LLM provider abstraction."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class LLMResponse(BaseModel):
    """Response from an LLM provider.

    Attributes:
        content: Generated text content.
        model: Model identifier used for generation.
        input_tokens: Number of input tokens consumed.
        output_tokens: Number of output tokens generated.
        finish_reason: Reason the generation stopped.
    """

    model_config = ConfigDict(frozen=True)

    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str | None = None


class OAuthTokens(BaseModel):
    """OAuth token pair with expiration.

    Attributes:
        access_token: Bearer access token.
        refresh_token: Token used to obtain new access tokens.
        expires_at: Expiration time as Unix epoch milliseconds.
    """

    model_config = ConfigDict(frozen=True)

    access_token: str
    refresh_token: str
    expires_at: int


class ApiKeyEntry(BaseModel):
    """API key credential.

    Attributes:
        key: Raw API key string.
    """

    model_config = ConfigDict(frozen=True)

    key: str

    @property
    def masked_key(self) -> str:
        """Return masked representation of the key.

        Returns:
            First 4 and last 4 characters with '...' in between
            for keys longer than 8 characters, otherwise '****'.
        """
        if len(self.key) > 8:
            return self.key[:4] + "..." + self.key[-4:]
        return "****"


class AuthEntry(BaseModel):
    """Authentication credential entry.

    Attributes:
        type: Authentication type discriminator.
        oauth: OAuth tokens when type is 'oauth'.
        api: API key entry when type is 'api'.
    """

    type: Literal["oauth", "api"]
    oauth: OAuthTokens | None = None
    api: ApiKeyEntry | None = None
