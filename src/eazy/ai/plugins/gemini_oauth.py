"""Gemini OAuth authentication plugin and provider."""

from __future__ import annotations

import time
from typing import Any

import httpx

from eazy.ai.models import (
    LLMError,
    LLMResponse,
    OAuthConfig,
    OAuthTokens,
    RateLimitError,
)
from eazy.ai.oauth_flow import OAuthFlow
from eazy.ai.plugins.base import AuthPlugin
from eazy.ai.plugins.gemini_common import (
    GEMINI_API_BASE,
    extract_error_message,
    parse_gemini_response,
)
from eazy.ai.provider import LLMProvider

GEMINI_OAUTH_CONFIG = OAuthConfig(
    client_id="936475272427.apps.googleusercontent.com",
    client_secret="KWsJlkaMn1jGLxQpWxMnOox-",
    auth_url="https://accounts.google.com/o/oauth2/auth",
    token_url="https://oauth2.googleapis.com/token",
    scopes=(
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/generative-language.retriever",
    ),
)


class GeminiOAuthPlugin(AuthPlugin):
    """Authentication plugin using Gemini OAuth flow.

    Uses browser consent flow to obtain OAuth tokens
    for Gemini API access.

    Attributes:
        _tokens: Current OAuth tokens.
        _oauth_flow: OAuth flow handler.
    """

    def __init__(self) -> None:
        self._tokens: OAuthTokens | None = None
        self._oauth_flow: OAuthFlow = OAuthFlow(config=GEMINI_OAUTH_CONFIG)

    async def authenticate(self, **kwargs: Any) -> bool:
        """Run OAuth browser consent flow.

        Args:
            **kwargs: Optional 'tokens' for pre-set tokens.

        Returns:
            True if tokens were obtained.
        """
        tokens = kwargs.get("tokens")
        if isinstance(tokens, OAuthTokens):
            self._tokens = tokens
            return True
        return False

    async def refresh(self) -> bool:
        """Refresh expired OAuth tokens.

        Returns:
            True if refresh succeeded.

        Raises:
            LLMError: If refresh fails.
        """
        if not self._tokens:
            return False
        self._tokens = await self._oauth_flow.refresh_token(self._tokens.refresh_token)
        return True

    def is_expired(self) -> bool:
        """Check whether the access token is expired.

        Returns:
            True if tokens are missing or expired.
        """
        if not self._tokens:
            return True
        return self._tokens.expires_at < int(time.time() * 1000)


class GeminiOAuthProvider(LLMProvider):
    """LLM provider using Gemini API with OAuth authentication.

    Sends prompts using Bearer token auth and auto-refreshes
    expired tokens before sending.

    Attributes:
        _plugin: OAuth authentication plugin.
        _client: Optional shared httpx client.
    """

    def __init__(
        self,
        plugin: GeminiOAuthPlugin,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._plugin = plugin
        self._client = client

    @property
    def name(self) -> str:
        """Unique provider identifier."""
        return "gemini-oauth"

    async def send(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Send a prompt to Gemini with Bearer token auth.

        Auto-refreshes expired tokens before sending.

        Args:
            prompt: Text prompt to send.
            **kwargs: Optional 'model' (default gemini-2.0-flash).

        Returns:
            Parsed LLM response.

        Raises:
            RateLimitError: On HTTP 429.
            LLMError: On other HTTP errors.
        """
        if self._plugin.is_expired():
            await self._plugin.refresh()

        model = kwargs.get("model", "gemini-2.0-flash")
        url = f"{GEMINI_API_BASE}/v1beta/models/{model}:generateContent"
        headers = {
            "Authorization": (f"Bearer {self._plugin._tokens.access_token}"),
        }
        body = {"contents": [{"parts": [{"text": prompt}]}]}

        client = self._client or httpx.AsyncClient()
        try:
            resp = await client.post(url, json=body, headers=headers)
            if resp.status_code == 429:
                msg = extract_error_message(resp)
                raise RateLimitError(msg)
            if resp.status_code >= 400:
                msg = extract_error_message(resp)
                raise LLMError(msg)
            return parse_gemini_response(resp.json(), model)
        finally:
            if not self._client:
                await client.aclose()

    def is_available(self) -> bool:
        """Check whether OAuth tokens are available."""
        return self._plugin._tokens is not None
